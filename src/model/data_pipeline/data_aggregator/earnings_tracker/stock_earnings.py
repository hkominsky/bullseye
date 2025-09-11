import pandas as pd
from dotenv import load_dotenv
import yfinance as yf
from src.model.utils.logger_config import LoggerSetup

load_dotenv()


class EarningsFetcher:
    """
    Class for retrieving historical and projected earnings call data for a ticker.
    """
    
    def __init__(self):
        self.logger = LoggerSetup.setup_logger(__name__)
        self.logger.info("EarningsFetcher initialized")
    
    def _get_stock_ticker(self, ticker: str):
        """Creates a yfinance Ticker object from the provided ticker symbol."""
        self.logger.debug(f"Creating yfinance Ticker object for {ticker}")
        return yf.Ticker(ticker.upper())

    def _safe_float(self, value):
        """Converts a value to float if it's not null, otherwise returns None."""
        result = float(value) if pd.notna(value) else None
        if result is not None:
            self.logger.debug(f"Converted value to float: {result}")
        return result

    def _calculate_surprise_percentage(self, reported_eps, estimated_eps):
        """Calculates the EPS surprise percentage."""
        if reported_eps is not None and estimated_eps not in (None, 0):
            surprise = ((reported_eps - estimated_eps) / estimated_eps) * 100
            self.logger.debug(f"Calculated EPS surprise: {surprise:.2f}% (Reported: {reported_eps}, Estimated: {estimated_eps})")
            return surprise
        return None

    def _build_earnings_record(self, index, row, stock):
        """Builds a single earnings record with all calculated metrics."""
        self.logger.debug(f"Building earnings record for date: {index.strftime('%Y-%m-%d')}")
        
        reported_eps = self._safe_float(row.get('epsActual'))
        estimated_eps = self._safe_float(row.get('epsEstimate'))
        
        surprise_percentage = self._calculate_surprise_percentage(reported_eps, estimated_eps)
        one_day_return, five_day_return = self._calculate_post_earnings_returns(stock, index)

        record = {
            'fiscalDateEnding': index.strftime('%Y-%m-%d'),
            'reportedEPS': reported_eps,
            'estimatedEPS': estimated_eps,
            'surprisePercentage': surprise_percentage,
            'oneDayReturn': one_day_return,
            'fiveDayReturn': five_day_return
        }
        
        self.logger.debug(f"Built earnings record: {record}")
        return record

    def _process_earnings_history(self, earnings_history, ticker: str):
        """Processes raw earnings history data and calculates surprise percentages and post-earnings returns."""
        self.logger.info(f"Processing earnings history for {ticker} with {len(earnings_history)} records")
        
        stock = self._get_stock_ticker(ticker)
        earnings_data = []

        for index, row in earnings_history.iterrows():
            earnings_record = self._build_earnings_record(index, row, stock)
            earnings_data.append(earnings_record)

        earnings_data.sort(key=lambda x: x['fiscalDateEnding'], reverse=True)
        self.logger.info(f"Processed {len(earnings_data)} earnings records for {ticker}")
        return earnings_data

    def _get_earnings_date_index(self, history, earnings_date):
        """Finds the index of the earnings date in the stock price history."""
        for i, date in enumerate(history.index):
            if date.date() >= earnings_date.date():
                self.logger.debug(f"Found earnings date index: {i} for date {earnings_date.date()}")
                return i
        self.logger.debug(f"No earnings date index found for {earnings_date.date()}")
        return None

    def _calculate_return_percentage(self, start_price, end_price):
        """Calculates percentage return between two prices."""
        return_pct = ((end_price - start_price) / start_price) * 100
        self.logger.debug(f"Calculated return: {return_pct:.2f}% (from {start_price} to {end_price})")
        return return_pct

    def _get_one_day_return(self, history, earnings_idx, earnings_close):
        """Calculates the one-day post-earnings return."""
        if earnings_idx + 1 < len(history):
            next_day_close = history['Close'].iloc[earnings_idx + 1]
            return self._calculate_return_percentage(earnings_close, next_day_close)
        self.logger.debug("Insufficient data for one-day return calculation")
        return None

    def _get_five_day_return(self, history, earnings_idx, earnings_close):
        """Calculates the five-day post-earnings return."""
        if earnings_idx + 5 < len(history):
            five_day_close = history['Close'].iloc[earnings_idx + 5]
            return self._calculate_return_percentage(earnings_close, five_day_close)
        elif len(history) > earnings_idx + 1:
            last_close = history['Close'].iloc[-1]
            self.logger.debug("Using last available close price for five-day return")
            return self._calculate_return_percentage(earnings_close, last_close)
        self.logger.debug("Insufficient data for five-day return calculation")
        return None

    def _calculate_post_earnings_returns(self, stock, earnings_date):
        """Calculates stock price returns for 1 and 5 days after an earnings announcement."""
        try:
            self.logger.debug(f"Calculating post-earnings returns for date: {earnings_date}")
            start_date = (earnings_date - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
            end_date = (earnings_date + pd.Timedelta(days=10)).strftime('%Y-%m-%d')
            
            history = stock.history(start=start_date, end=end_date)
            
            if history.empty:
                self.logger.warning(f"No price history found for period {start_date} to {end_date}")
                return None, None

            earnings_idx = self._get_earnings_date_index(history, earnings_date)
            
            if earnings_idx is None or earnings_idx >= len(history):
                self.logger.warning(f"Invalid earnings index for date {earnings_date}")
                return None, None
                
            earnings_close = history['Close'].iloc[earnings_idx]
            
            one_day_return = self._get_one_day_return(history, earnings_idx, earnings_close)
            five_day_return = self._get_five_day_return(history, earnings_idx, earnings_close)

            self.logger.debug(f"Post-earnings returns calculated - 1-day: {one_day_return}, 5-day: {five_day_return}")
            return one_day_return, five_day_return
            
        except Exception as e:
            self.logger.error(f"Error calculating post-earnings returns: {e}")
            return None, None

    def _create_empty_dataframe(self):
        """Creates an empty DataFrame with the standard earnings columns."""
        self.logger.debug("Creating empty earnings DataFrame")
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
                self.logger.debug(f"Added missing column: {col}")
        return df[important_cols]

    def _extract_earnings_date_from_dict(self, calendar):
        """Extracts earnings date from dictionary format calendar data."""
        date_keys = ['Earnings Date', 'Date', 'earnings_date']
        for key in date_keys:
            if key in calendar:
                earnings_date = calendar[key]
                if isinstance(earnings_date, list) and earnings_date:
                    self.logger.debug(f"Extracted earnings date from dict list: {earnings_date[0]}")
                    return earnings_date[0]
                self.logger.debug(f"Extracted earnings date from dict: {earnings_date}")
                return earnings_date
        return None

    def _extract_eps_estimate_from_dict(self, calendar):
        """Extracts EPS estimate from dictionary format calendar data."""
        estimate_keys = ['Earnings Average', 'EPS Estimate', 'EPS Est', 'Estimate']
        for key in estimate_keys:
            if key in calendar:
                eps_estimate = calendar[key]
                if isinstance(eps_estimate, list) and eps_estimate:
                    self.logger.debug(f"Extracted EPS estimate from dict list: {eps_estimate[0]}")
                    return eps_estimate[0]
                self.logger.debug(f"Extracted EPS estimate from dict: {eps_estimate}")
                return eps_estimate
        return None

    def _extract_earnings_date_from_dataframe(self, calendar):
        """Extracts earnings date from DataFrame format calendar data."""
        if 'Earnings Date' in calendar.columns:
            date = calendar['Earnings Date'].iloc[0]
            self.logger.debug(f"Extracted earnings date from DataFrame: {date}")
            return date
        elif 'Date' in calendar.columns:
            date = calendar['Date'].iloc[0]
            self.logger.debug(f"Extracted date from DataFrame: {date}")
            return date
        return None

    def _extract_eps_estimate_from_dataframe(self, calendar):
        """Extracts EPS estimate from DataFrame format calendar data."""
        eps_cols = ['Earnings Average', 'EPS Estimate', 'EPS Est', 'Estimate']
        for col in eps_cols:
            if col in calendar.columns:
                estimate = calendar[col].iloc[0]
                self.logger.debug(f"Extracted EPS estimate from DataFrame: {estimate}")
                return estimate
        return None

    def _parse_calendar_data(self, calendar):
        """Parses calendar data to extract earnings date and EPS estimate."""
        self.logger.debug("Parsing calendar data")
        earnings_date = None
        eps_estimate = None
        
        if isinstance(calendar, dict):
            self.logger.debug("Calendar data is dictionary format")
            earnings_date = self._extract_earnings_date_from_dict(calendar)
            eps_estimate = self._extract_eps_estimate_from_dict(calendar)
        elif hasattr(calendar, 'iloc') and len(calendar) > 0:
            self.logger.debug("Calendar data is DataFrame format")
            earnings_date = self._extract_earnings_date_from_dataframe(calendar)
            eps_estimate = self._extract_eps_estimate_from_dataframe(calendar)

        self.logger.debug(f"Parsed calendar data - Date: {earnings_date}, EPS Estimate: {eps_estimate}")
        return earnings_date, eps_estimate

    def _format_earnings_date(self, earnings_date):
        """Formats earnings date to string format."""
        formatted_date = earnings_date.strftime('%Y-%m-%d') if earnings_date is not None else None
        if formatted_date:
            self.logger.debug(f"Formatted earnings date: {formatted_date}")
        return formatted_date

    def _get_forward_pe_from_info(self, info):
        """Extracts forward P/E ratio from stock info, trying multiple keys."""
        forward_pe = info.get("forwardPE")
        
        if forward_pe is None:
            alt_pe_keys = ['forwardEps', 'trailingPE', 'priceToEarningsRatio']
            for key in alt_pe_keys:
                if key in info and info[key] is not None:
                    self.logger.debug(f"Found P/E ratio using alternative key {key}: {info[key]}")
                    return info[key]
        else:
            self.logger.debug(f"Found forward P/E: {forward_pe}")
        
        return forward_pe

    def _get_peg_ratio_from_info(self, info):
        """Extracts PEG ratio from stock info, trying multiple keys."""
        peg_ratio = info.get("pegRatio")
        
        if peg_ratio is None:
            peg_ratio = info.get("trailingPegRatio")
            if peg_ratio:
                self.logger.debug(f"Found PEG ratio using trailing key: {peg_ratio}")
        else:
            self.logger.debug(f"Found PEG ratio: {peg_ratio}")
        
        return peg_ratio

    def fetch_historical(self, ticker: str) -> dict:
        """Fetches historical earnings data for a stock ticker and returns it as a dictionary."""
        try:
            self.logger.info(f"Fetching historical earnings data for {ticker}")
            stock = self._get_stock_ticker(ticker)
            earnings_history = stock.earnings_history
            
            if earnings_history is None or earnings_history.empty:
                self.logger.warning(f"No earnings history found for {ticker}")
                return {"quarterlyEarnings": []}

            quarterly_data = self._process_earnings_history(earnings_history, ticker)
            self.logger.info(f"Successfully fetched {len(quarterly_data)} historical earnings records for {ticker}")
            return {"quarterlyEarnings": quarterly_data}
        except Exception as e:
            self.logger.error(f"Error fetching historical earnings for {ticker}: {e}")
            return {"quarterlyEarnings": []}

    def fetch_earnings(self, ticker: str, rows: int = 4) -> pd.DataFrame:
        """Fetches recent earnings data for a stock and returns it as a pandas DataFrame."""
        try:
            self.logger.info(f"Fetching {rows} recent earnings records for {ticker}")
            data = self.fetch_historical(ticker)
            quarterly = data.get("quarterlyEarnings", [])

            if not quarterly:
                self.logger.warning(f"No quarterly earnings data found for {ticker}")
                return self._create_empty_dataframe()

            df = pd.DataFrame(quarterly)
            df = self._ensure_dataframe_columns(df)
            result = df.head(rows)
            self.logger.info(f"Returning {len(result)} earnings records for {ticker}")
            return result
        except Exception as e:
            self.logger.error(f"Error fetching earnings DataFrame for {ticker}: {e}")
            return self._create_empty_dataframe()

    def fetch_next_earnings(self, ticker: str) -> dict:
        """Fetches upcoming earnings date and estimate along with valuation metrics for a stock."""
        try:
            self.logger.info(f"Fetching next earnings information for {ticker}")
            stock = self._get_stock_ticker(ticker)
            calendar = stock.calendar

            if calendar is None or (hasattr(calendar, 'empty') and calendar.empty):
                self.logger.warning(f"No calendar data found for {ticker}")
                return {"nextEarningsDate": None, "estimatedEPS": None, "forwardPE": None, "pegRatio": None}

            earnings_date, eps_estimate = self._parse_calendar_data(calendar)
            valuation = self.fetch_valuation_metrics(ticker)

            result = {
                "nextEarningsDate": self._format_earnings_date(earnings_date),
                "estimatedEPS": eps_estimate if pd.notna(eps_estimate) else None,
                "forwardPE": valuation.get("forwardPE"),
                "pegRatio": valuation.get("pegRatio")
            }
            
            self.logger.info(f"Successfully fetched next earnings data for {ticker}: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error fetching next earnings for {ticker}: {e}")
            return {"nextEarningsDate": None, "estimatedEPS": None, "forwardPE": None, "pegRatio": None}

    def fetch_valuation_metrics(self, ticker: str) -> dict:
        """Fetches forward P/E ratio and PEG ratio valuation metrics for a stock."""
        try:
            self.logger.debug(f"Fetching valuation metrics for {ticker}")
            stock = self._get_stock_ticker(ticker)
            info = stock.info
            
            forward_pe = self._get_forward_pe_from_info(info)
            peg_ratio = self._get_peg_ratio_from_info(info)
            
            result = {
                "forwardPE": forward_pe,
                "pegRatio": peg_ratio
            }
            
            self.logger.debug(f"Fetched valuation metrics for {ticker}: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error fetching valuation metrics for {ticker}: {e}")
            return {"forwardPE": None, "pegRatio": None}