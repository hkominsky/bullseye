from typing import Any, Optional, List
import pandas as pd
from datetime import date
from src.model.utils.logger_config import LoggerSetup


class DataValidator:
    """Centralized data validation and cleaning for all financial data types."""
    
    def __init__(self):
        self.logger = LoggerSetup.setup_logger(__name__)
    
    @staticmethod
    def safe_decimal(value: Any, max_digits: int = 15, decimal_places: int = 6) -> Optional[float]:
        """Safely convert value to decimal within PostgreSQL limits."""
        if pd.isna(value) or value is None:
            return None
        try:
            float_val = float(value)
            max_val = 10**(max_digits - decimal_places) - 1
            if abs(float_val) > max_val:
                return max_val if float_val > 0 else -max_val
            return float_val
        except (ValueError, TypeError, OverflowError):
            return None
    
    @staticmethod
    def safe_date(value: Any) -> Optional[date]:
        """Safely convert value to date."""
        if pd.isna(value) or value is None:
            return None
        try:
            if isinstance(value, date):
                return value
            return pd.to_datetime(value).date()
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def safe_bigint(value: Any) -> Optional[int]:
        """Safely convert value to bigint within PostgreSQL limits."""
        if pd.isna(value) or value is None:
            return None
        try:
            int_val = int(float(value))
            return max(-9223372036854775808, min(9223372036854775807, int_val))
        except (ValueError, TypeError, OverflowError):
            return None
    
    @staticmethod
    def safe_string(value: Any, max_length: int = None) -> Optional[str]:
        """Safely convert value to string with optional length limit."""
        if pd.isna(value) or value is None:
            return None
        try:
            str_val = str(value)
            if max_length and len(str_val) > max_length:
                return str_val[:max_length]
            return str_val
        except (ValueError, TypeError):
            return None
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean a DataFrame by removing invalid values and standardizing formats."""
        if df.empty:
            return df
        
        cleaned_df = df.copy()
        
        cleaned_df = cleaned_df.replace([float('inf'), float('-inf')], pd.NA)
        
        numeric_columns = cleaned_df.select_dtypes(include=['number']).columns
        for col in numeric_columns:
            cleaned_df[col] = cleaned_df[col].apply(self.safe_decimal)
        
        date_columns = [col for col in cleaned_df.columns if 'date' in col.lower()]
        for col in date_columns:
            cleaned_df[col] = cleaned_df[col].apply(self.safe_date)
        
        return cleaned_df
    
    def validate_ticker_data_package(self, corporate_sentiment: float, retail_sentiment: float, 
                                   ticker_news_df: pd.DataFrame, sector_performance_data: dict, 
                                   earnings_df: pd.DataFrame, raw_df: pd.DataFrame, 
                                   metrics_df: pd.DataFrame) -> tuple[bool, str]:
        """
        Comprehensive validation of all ticker data components.
        Returns (is_valid, reason_if_invalid)
        """
        dataframes = {
            "Raw financial data": raw_df,
            "Metrics data": metrics_df,
            "News data": ticker_news_df,
            "Earnings data": earnings_df
        }
        
        for name, df in dataframes.items():
            if df is None or df.empty:
                return False, f"{name} is empty or None"
        
        sentiments = {
            "Corporate sentiment": corporate_sentiment,
            "Retail sentiment": retail_sentiment
        }
        
        for name, value in sentiments.items():
            if value is None or not isinstance(value, (int, float)) or pd.isna(value):
                return False, f"{name} is invalid or None"
        
        if not sector_performance_data or not isinstance(sector_performance_data, dict):
            return False, "Sector performance data is empty or invalid"
        
        return True, ""
    
    def prepare_raw_financial_data(self, ticker: str, raw_df: pd.DataFrame) -> List[tuple]:
        """Prepare and validate raw financial data for database insertion."""
        if raw_df.empty:
            return []
        
        raw_data = []
        for _, row in raw_df.iterrows():
            raw_data.append((
                ticker,
                self.safe_date(row.get('date')),
                self.safe_string(row.get('period')),
                self.safe_string(row.get('form_type')),
                self.safe_bigint(row.get('revenue')),
                self.safe_bigint(row.get('cost_of_revenue')),
                self.safe_bigint(row.get('gross_profit')),
                self.safe_bigint(row.get('operating_income')),
                self.safe_bigint(row.get('net_income')),
                self.safe_bigint(row.get('total_assets')),
                self.safe_bigint(row.get('current_assets')),
                self.safe_bigint(row.get('cash_and_equivalents')),
                self.safe_bigint(row.get('total_liabilities')),
                self.safe_bigint(row.get('current_liabilities')),
                self.safe_bigint(row.get('shareholders_equity'))
            ))
        return raw_data
    
    def prepare_metrics_data(self, ticker: str, metrics_df: pd.DataFrame) -> List[tuple]:
        """Prepare and validate metrics data for database insertion."""
        if metrics_df.empty:
            return []
        
        metrics_data = []
        for _, row in metrics_df.iterrows():
            metrics_data.append((
                ticker,
                self.safe_string(row.get('period')),
                self.safe_bigint(row.get('working_capital')),
                self.safe_decimal(row.get('asset_turnover')),
                self.safe_decimal(row.get('altman_z_score')),
                self.safe_bigint(row.get('piotroski_f_score')),
                self.safe_decimal(row.get('gross_margin')),
                self.safe_decimal(row.get('operating_margin')),
                self.safe_decimal(row.get('net_margin')),
                self.safe_decimal(row.get('current_ratio')),
                self.safe_decimal(row.get('quick_ratio')),
                self.safe_decimal(row.get('debt_to_equity')),
                self.safe_decimal(row.get('return_on_assets')),
                self.safe_decimal(row.get('return_on_equity')),
                self.safe_bigint(row.get('free_cash_flow')),
                self.safe_decimal(row.get('earnings_per_share')),
                self.safe_decimal(row.get('book_value_per_share')),
                self.safe_decimal(row.get('revenue_per_share')),
                self.safe_decimal(row.get('cash_per_share')),
                self.safe_decimal(row.get('fcf_per_share')),
                self.safe_decimal(row.get('stock_price')),
                self.safe_bigint(row.get('market_cap')),
                self.safe_bigint(row.get('enterprise_value')),
                self.safe_decimal(row.get('price_to_earnings')),
                self.safe_decimal(row.get('price_to_book')),
                self.safe_decimal(row.get('price_to_sales')),
                self.safe_decimal(row.get('ev_to_revenue')),
                self.safe_decimal(row.get('ev_to_ebitda')),
                self.safe_decimal(row.get('price_to_fcf')),
                self.safe_decimal(row.get('market_to_book_premium'))
            ))
        return metrics_data
    
    def prepare_news_articles_data(self, ticker: str, news_df: pd.DataFrame) -> List[tuple]:
        """Prepare and validate news articles data for database insertion."""
        if news_df.empty:
            return []
        
        articles_data = []
        for _, row in news_df.iterrows():
            articles_data.append((
                ticker,
                self.safe_string(row.get('headline'), 1000),
                self.safe_string(row.get('summary')),
                self.safe_string(row.get('url'), 2000),
                self.safe_date(row.get('published_at'))
            ))
        return articles_data
    
    def prepare_earnings_data(self, ticker: str, earnings_df: pd.DataFrame) -> List[tuple]:
        """Prepare and validate earnings data for database insertion."""
        if earnings_df.empty:
            return []
        
        earnings_data = []
        for _, row in earnings_df.iterrows():
            earnings_data.append((
                ticker,
                self.safe_date(row.get('fiscalDateEnding')),
                self.safe_decimal(row.get('reportedEPS')),
                self.safe_decimal(row.get('estimatedEPS')),
                self.safe_decimal(row.get('surprisePercentage')),
                self.safe_decimal(row.get('oneDayReturn')),
                self.safe_decimal(row.get('fiveDayReturn'))
            ))
        return earnings_data