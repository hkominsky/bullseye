import os
import pandas as pd
from dotenv import load_dotenv
import yfinance as yf

load_dotenv()

class EarningsFetcher:
    def _get_stock_ticker(self, ticker: str):
        """Creates a yfinance Ticker object from the provided ticker symbol."""
        return yf.Ticker(ticker.upper())

    def _safe_float(self, value):
        """Converts a value to float if it's not null, otherwise returns None."""
        return float(value) if pd.notna(value) else None

    def _process_earnings_history(self, earnings_history, ticker: str):
        """Processes raw earnings history data and calculates surprise percentages and post-earnings returns."""
        stock = self._get_stock_ticker(ticker)
        earnings_data = []

        for index, row in earnings_history.iterrows():
            reported_eps = self._safe_float(row.get('epsActual'))
            estimated_eps = self._safe_float(row.get('epsEstimate'))

            surprise_percentage = None
            if reported_eps is not None and estimated_eps not in (None, 0):
                surprise_percentage = ((reported_eps - estimated_eps) / estimated_eps) * 100

            one_day_return, five_day_return = self._calculate_post_earnings_returns(stock, index)

            earnings_data.append({
                'fiscalDateEnding': index.strftime('%Y-%m-%d'),
                'reportedEPS': reported_eps,
                'estimatedEPS': estimated_eps,
                'surprisePercentage': surprise_percentage,
                'oneDayReturn': one_day_return,
                'fiveDayReturn': five_day_return
            })

        earnings_data.sort(key=lambda x: x['fiscalDateEnding'], reverse=True)
        return earnings_data

    def _calculate_post_earnings_returns(self, stock, earnings_date):
        """Calculates stock price returns for 1 and 5 days after an earnings announcement."""
        try:
            # Get price data around earnings date
            start_date = (earnings_date - pd.Timedelta(days=1)).strftime('%Y-%m-%d')  # Day before earnings
            end_date = (earnings_date + pd.Timedelta(days=10)).strftime('%Y-%m-%d')   # Extended range
            
            history = stock.history(start=start_date, end=end_date)
            
            if history.empty:
                return None, None

            # Find the closest trading day to earnings date
            earnings_idx = None
            for i, date in enumerate(history.index):
                if date.date() >= earnings_date.date():
                    earnings_idx = i
                    break
            
            if earnings_idx is None or earnings_idx >= len(history):
                return None, None
                
            earnings_close = history['Close'].iloc[earnings_idx]
            
            # Calculate 1-day return (next trading day)
            one_day_return = None
            if earnings_idx + 1 < len(history):
                next_day_close = history['Close'].iloc[earnings_idx + 1]
                one_day_return = ((next_day_close - earnings_close) / earnings_close) * 100
            
            # Calculate 5-day return
            five_day_return = None
            if earnings_idx + 5 < len(history):
                five_day_close = history['Close'].iloc[earnings_idx + 5]
                five_day_return = ((five_day_close - earnings_close) / earnings_close) * 100
            elif len(history) > earnings_idx + 1:
                # Use the last available price if we don't have 5 days
                last_close = history['Close'].iloc[-1]
                five_day_return = ((last_close - earnings_close) / earnings_close) * 100

            return one_day_return, five_day_return
            
        except Exception:
            return None, None

    def _create_empty_dataframe(self):
        """Creates an empty DataFrame with the standard earnings columns."""
        return pd.DataFrame(columns=[
            'fiscalDateEnding', 'reportedEPS', 'estimatedEPS', 'surprisePercentage',
            'oneDayReturn', 'fiveDayReturn'
        ])

    def _ensure_dataframe_columns(self, df):
        """Ensures the DataFrame has all required earnings columns, adding missing ones with None values."""
        important_cols = [
            'fiscalDateEnding', 'reportedEPS', 'estimatedEPS', 'surprisePercentage',
            'oneDayReturn', 'fiveDayReturn'
        ]
        for col in important_cols:
            if col not in df.columns:
                df[col] = None
        return df[important_cols]

    def fetch_historical(self, ticker: str) -> dict:
        """Fetches historical earnings data for a stock ticker and returns it as a dictionary."""
        stock = self._get_stock_ticker(ticker)
        earnings_history = stock.earnings_history
        if earnings_history is None or earnings_history.empty:
            return {"quarterlyEarnings": []}

        quarterly_data = self._process_earnings_history(earnings_history, ticker)
        return {"quarterlyEarnings": quarterly_data}

    def fetch_earnings(self, ticker: str, rows: int = 4) -> pd.DataFrame:
        """Fetches recent earnings data for a stock and returns it as a pandas DataFrame."""
        data = self.fetch_historical(ticker)
        quarterly = data.get("quarterlyEarnings", [])

        if not quarterly:
            return self._create_empty_dataframe()

        df = pd.DataFrame(quarterly)
        df = self._ensure_dataframe_columns(df)
        return df.head(rows)

    def fetch_next_earnings(self, ticker: str) -> dict:
        """Fetches upcoming earnings date and estimate along with valuation metrics for a stock."""
        try:
            stock = self._get_stock_ticker(ticker)
            calendar = stock.calendar

            if calendar is None or (hasattr(calendar, 'empty') and calendar.empty):
                return {"nextEarningsDate": None, "estimatedEPS": None, "forwardPE": None, "pegRatio": None}

            earnings_date = None
            eps_estimate = None
            
            # Handle different calendar data structures
            if isinstance(calendar, dict):
                # Dictionary format
                for key in ['Earnings Date', 'Date', 'earnings_date']:
                    if key in calendar:
                        earnings_date = calendar[key]
                        if isinstance(earnings_date, list) and earnings_date:
                            earnings_date = earnings_date[0]
                        break
                
                for key in ['Earnings Average', 'EPS Estimate', 'EPS Est', 'Estimate']:
                    if key in calendar:
                        eps_estimate = calendar[key]
                        if isinstance(eps_estimate, list) and eps_estimate:
                            eps_estimate = eps_estimate[0]
                        break
            elif hasattr(calendar, 'iloc') and len(calendar) > 0:
                # DataFrame format
                if 'Earnings Date' in calendar.columns:
                    earnings_date = calendar['Earnings Date'].iloc[0]
                elif 'Date' in calendar.columns:
                    earnings_date = calendar['Date'].iloc[0]
                
                eps_cols = ['Earnings Average', 'EPS Estimate', 'EPS Est', 'Estimate']
                for col in eps_cols:
                    if col in calendar.columns:
                        eps_estimate = calendar[col].iloc[0]
                        break

            valuation = self.fetch_valuation_metrics(ticker)

            return {
                "nextEarningsDate": earnings_date.strftime('%Y-%m-%d') if earnings_date is not None else None,
                "estimatedEPS": eps_estimate if pd.notna(eps_estimate) else None,
                "forwardPE": valuation.get("forwardPE"),
                "pegRatio": valuation.get("pegRatio")
            }
        except Exception:
            return {"nextEarningsDate": None, "estimatedEPS": None, "forwardPE": None, "pegRatio": None}

    def fetch_valuation_metrics(self, ticker: str) -> dict:
        """Fetches forward P/E ratio and PEG ratio valuation metrics for a stock."""
        try:
            stock = self._get_stock_ticker(ticker)
            info = stock.info
            
            forward_pe = info.get("forwardPE")
            peg_ratio = info.get("pegRatio")
            
            # Try alternative keys if primary ones don't work
            if forward_pe is None:
                alt_pe_keys = ['forwardEps', 'trailingPE', 'priceToEarningsRatio']
                for key in alt_pe_keys:
                    if key in info and info[key] is not None:
                        forward_pe = info[key]
                        break
            
            if peg_ratio is None:
                # Try to get trailing PEG ratio as fallback
                peg_ratio = info.get("trailingPegRatio")
            
            return {
                "forwardPE": forward_pe,
                "pegRatio": peg_ratio
            }
        except Exception:
            return {"forwardPE": None, "pegRatio": None}