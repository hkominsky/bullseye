import pandas as pd
from dotenv import load_dotenv
import yfinance as yf

load_dotenv()


class EarningsFetcher:
    """
    Class for retrieving historical and projected earnings call data for a ticker.
    """
    
    def _get_stock_ticker(self, ticker: str):
        """Creates a yfinance Ticker object from the provided ticker symbol."""
        return yf.Ticker(ticker.upper())

    def _safe_float(self, value):
        """Converts a value to float if it's not null, otherwise returns None."""
        return float(value) if pd.notna(value) else None

    def _calculate_surprise_percentage(self, reported_eps, estimated_eps):
        """Calculates the EPS surprise percentage."""
        if reported_eps is not None and estimated_eps not in (None, 0):
            return ((reported_eps - estimated_eps) / estimated_eps) * 100
        return None

    def _build_earnings_record(self, index, row, stock):
        """Builds a single earnings record with all calculated metrics."""
        reported_eps = self._safe_float(row.get('epsActual'))
        estimated_eps = self._safe_float(row.get('epsEstimate'))
        
        surprise_percentage = self._calculate_surprise_percentage(reported_eps, estimated_eps)
        one_day_return, five_day_return = self._calculate_post_earnings_returns(stock, index)

        return {
            'fiscalDateEnding': index.strftime('%Y-%m-%d'),
            'reportedEPS': reported_eps,
            'estimatedEPS': estimated_eps,
            'surprisePercentage': surprise_percentage,
            'oneDayReturn': one_day_return,
            'fiveDayReturn': five_day_return
        }

    def _process_earnings_history(self, earnings_history, ticker: str):
        """Processes raw earnings history data and calculates surprise percentages and post-earnings returns."""
        stock = self._get_stock_ticker(ticker)
        earnings_data = []

        for index, row in earnings_history.iterrows():
            earnings_record = self._build_earnings_record(index, row, stock)
            earnings_data.append(earnings_record)

        earnings_data.sort(key=lambda x: x['fiscalDateEnding'], reverse=True)
        return earnings_data

    def _get_earnings_date_index(self, history, earnings_date):
        """Finds the index of the earnings date in the stock price history."""
        for i, date in enumerate(history.index):
            if date.date() >= earnings_date.date():
                return i
        return None

    def _calculate_return_percentage(self, start_price, end_price):
        """Calculates percentage return between two prices."""
        return ((end_price - start_price) / start_price) * 100

    def _get_one_day_return(self, history, earnings_idx, earnings_close):
        """Calculates the one-day post-earnings return."""
        if earnings_idx + 1 < len(history):
            next_day_close = history['Close'].iloc[earnings_idx + 1]
            return self._calculate_return_percentage(earnings_close, next_day_close)
        return None

    def _get_five_day_return(self, history, earnings_idx, earnings_close):
        """Calculates the five-day post-earnings return."""
        if earnings_idx + 5 < len(history):
            five_day_close = history['Close'].iloc[earnings_idx + 5]
            return self._calculate_return_percentage(earnings_close, five_day_close)
        elif len(history) > earnings_idx + 1:
            last_close = history['Close'].iloc[-1]
            return self._calculate_return_percentage(earnings_close, last_close)
        return None

    def _calculate_post_earnings_returns(self, stock, earnings_date):
        """Calculates stock price returns for 1 and 5 days after an earnings announcement."""
        try:
            start_date = (earnings_date - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
            end_date = (earnings_date + pd.Timedelta(days=10)).strftime('%Y-%m-%d')
            
            history = stock.history(start=start_date, end=end_date)
            
            if history.empty:
                return None, None

            earnings_idx = self._get_earnings_date_index(history, earnings_date)
            
            if earnings_idx is None or earnings_idx >= len(history):
                return None, None
                
            earnings_close = history['Close'].iloc[earnings_idx]
            
            one_day_return = self._get_one_day_return(history, earnings_idx, earnings_close)
            five_day_return = self._get_five_day_return(history, earnings_idx, earnings_close)

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

    def _extract_earnings_date_from_dict(self, calendar):
        """Extracts earnings date from dictionary format calendar data."""
        date_keys = ['Earnings Date', 'Date', 'earnings_date']
        for key in date_keys:
            if key in calendar:
                earnings_date = calendar[key]
                if isinstance(earnings_date, list) and earnings_date:
                    return earnings_date[0]
                return earnings_date
        return None

    def _extract_eps_estimate_from_dict(self, calendar):
        """Extracts EPS estimate from dictionary format calendar data."""
        estimate_keys = ['Earnings Average', 'EPS Estimate', 'EPS Est', 'Estimate']
        for key in estimate_keys:
            if key in calendar:
                eps_estimate = calendar[key]
                if isinstance(eps_estimate, list) and eps_estimate:
                    return eps_estimate[0]
                return eps_estimate
        return None

    def _extract_earnings_date_from_dataframe(self, calendar):
        """Extracts earnings date from DataFrame format calendar data."""
        if 'Earnings Date' in calendar.columns:
            return calendar['Earnings Date'].iloc[0]
        elif 'Date' in calendar.columns:
            return calendar['Date'].iloc[0]
        return None

    def _extract_eps_estimate_from_dataframe(self, calendar):
        """Extracts EPS estimate from DataFrame format calendar data."""
        eps_cols = ['Earnings Average', 'EPS Estimate', 'EPS Est', 'Estimate']
        for col in eps_cols:
            if col in calendar.columns:
                return calendar[col].iloc[0]
        return None

    def _parse_calendar_data(self, calendar):
        """Parses calendar data to extract earnings date and EPS estimate."""
        earnings_date = None
        eps_estimate = None
        
        if isinstance(calendar, dict):
            earnings_date = self._extract_earnings_date_from_dict(calendar)
            eps_estimate = self._extract_eps_estimate_from_dict(calendar)
        elif hasattr(calendar, 'iloc') and len(calendar) > 0:
            earnings_date = self._extract_earnings_date_from_dataframe(calendar)
            eps_estimate = self._extract_eps_estimate_from_dataframe(calendar)

        return earnings_date, eps_estimate

    def _format_earnings_date(self, earnings_date):
        """Formats earnings date to string format."""
        return earnings_date.strftime('%Y-%m-%d') if earnings_date is not None else None

    def _get_forward_pe_from_info(self, info):
        """Extracts forward P/E ratio from stock info, trying multiple keys."""
        forward_pe = info.get("forwardPE")
        
        if forward_pe is None:
            alt_pe_keys = ['forwardEps', 'trailingPE', 'priceToEarningsRatio']
            for key in alt_pe_keys:
                if key in info and info[key] is not None:
                    return info[key]
        
        return forward_pe

    def _get_peg_ratio_from_info(self, info):
        """Extracts PEG ratio from stock info, trying multiple keys."""
        peg_ratio = info.get("pegRatio")
        
        if peg_ratio is None:
            peg_ratio = info.get("trailingPegRatio")
        
        return peg_ratio

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

            earnings_date, eps_estimate = self._parse_calendar_data(calendar)
            valuation = self.fetch_valuation_metrics(ticker)

            return {
                "nextEarningsDate": self._format_earnings_date(earnings_date),
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
            
            forward_pe = self._get_forward_pe_from_info(info)
            peg_ratio = self._get_peg_ratio_from_info(info)
            
            return {
                "forwardPE": forward_pe,
                "pegRatio": peg_ratio
            }
        except Exception:
            return {"forwardPE": None, "pegRatio": None}