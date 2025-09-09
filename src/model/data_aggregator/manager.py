from typing import List, Tuple
import pandas as pd

from src.model.utils.http_client import HttpClient
from src.model.data_aggregator.edgar_data_filings.ticker_retriever.cache import FileCache
from src.model.data_aggregator.edgar_data_filings.ticker_retriever.ticker_service import TickerMappingService
from src.model.data_aggregator.edgar_data_filings.sec_data_processor.extractor import SECDataExtractor
from src.model.data_aggregator.edgar_data_filings.sec_data_processor.cleaner import SECDataCleaner
from src.model.data_aggregator.edgar_data_filings.sec_data_processor.processor import SECDataProcessor
from src.model.data_aggregator.sentiment_analysis.corporate_sentiment import CorporateSentimentAnalyzer
from src.model.data_aggregator.sentiment_analysis.retail_sentiment import RetailSentimentAnalyzer
from src.model.data_aggregator.ticker_news.news import TickerNews
from src.model.data_aggregator.sector_analysis.sector_performance import SectorPerformance
from src.model.data_aggregator.earnings_tracker.stock_earnings import EarningsFetcher
from src.model.notifier.notifications import EmailNotifier
from src.model.utils.models import FinancialRecord


class SECDataManager:
    """
    Manager class for retrieving, cleaning, and processing SEC financial data
    and sentiment for individual stock tickers.
    """

    def __init__(self, user_agent: str) -> None:
        """
        Initialize the SECDataManager with required services.
        """
        self.http_client = HttpClient(user_agent)
        self.cache = FileCache()
        self.ticker_service = TickerMappingService(self.http_client, self.cache)

        ticker_mapping = self.ticker_service.get_ticker_to_cik_mapping()
        self.extractor = SECDataExtractor(self.http_client, ticker_mapping)
        self.cleaner = SECDataCleaner()
        self.processor = SECDataProcessor()
        self.corporate_sentiment_analyzer = CorporateSentimentAnalyzer()
        self.retail_sentiment_analyzer = RetailSentimentAnalyzer()
        self.ticker_news = TickerNews()
        self.quarterly_earnings = EarningsFetcher()
        self.notifier = EmailNotifier()

    def get_comprehensive_financial_data(
        self, ticker: str, periods: int = 8
    ) -> List[FinancialRecord]:
        """Retrieve, clean, and process financial data for a single ticker."""
        try:
            raw_records = self.extractor.extract_raw_financial_data(ticker, periods)
            cleaned_records = self.cleaner.clean_financial_records(raw_records)
            enhanced_records = self.processor.process_records_with_metrics(cleaned_records)
            return enhanced_records
        except Exception as e:
            print(f"Error retrieving financial data for {ticker}: {e}")
            return []

    def get_financial_dataframes(self, ticker: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get financial data for a single ticker split into raw and metrics DataFrames."""
        records = self.get_comprehensive_financial_data(ticker)

        if not records:
            return pd.DataFrame(), pd.DataFrame()

        raw_df, metrics_df = self.processor.create_split_dataframes({ticker: records})

        cleaned_raw_df = self.cleaner.clean_dataframe(raw_df)
        cleaned_metrics_df = self.cleaner.clean_dataframe(metrics_df)

        return cleaned_raw_df, cleaned_metrics_df

    def get_sentiment(self, ticker: str) -> Tuple[float, float]:
        """Get both corporate (news-based) and retail (social media-based) sentiment scores."""
        corporate_sentiment = float(self.corporate_sentiment_analyzer.fetch_sentiment(ticker))
        #TODO: Need to get twitter dev api key for this to change.
        #retail_sentiment = float(self.retail_sentiment_analyzer.fetch_sentiment(ticker))
        retail_sentiment = -0.15
        return corporate_sentiment, retail_sentiment

    def get_sector_performance(self, ticker: str) -> dict:
        """Get sector performance data for the given ticker."""
        try:
            sector_analyzer = SectorPerformance(ticker)
            return sector_analyzer.get_sector_performance()
        except Exception as e:
            print(f"Error retrieving sector performance for {ticker}: {e}")
            return {
                "ticker": ticker,
                "sector": "Unknown",
                "sector_etf": "N/A",
                "ticker_1y_performance_pct": 0.0,
                "sector_1y_performance_pct": 0.0,
            }

    def _validate_email_data(self, corporate_sentiment: float, retail_sentiment: float, 
                        ticker_news_df: pd.DataFrame, sector_performance_data: dict, 
                        earnings_df: pd.DataFrame, raw_df: pd.DataFrame, 
                        metrics_df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validate all data components before sending email.
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
            if value is None or not isinstance(value, (int, float)):
                return False, f"{name} is invalid or None"
        
        if not sector_performance_data or not isinstance(sector_performance_data, dict):
            return False, "Sector performance data is empty or invalid"
        
        return True, ""

    def process_stock(self, ticker: str) -> None:
        """
        Validates stock data before sending information then sends as an email.
        """
        corporate_sentiment, retail_sentiment = self.get_sentiment(ticker)
        ticker_news_df = self.ticker_news.get_ticker_news(ticker)
        sector_performance_data = self.get_sector_performance(ticker)
        earnings_df = self.quarterly_earnings.fetch_earnings(ticker)
        earnings_estimate = self.quarterly_earnings.fetch_next_earnings(ticker)
        raw_df, metrics_df = self.get_financial_dataframes(ticker)

        is_valid, validation_reason = self._validate_email_data(
            corporate_sentiment, retail_sentiment, ticker_news_df, 
            sector_performance_data, earnings_df, raw_df, metrics_df
        )

        if not is_valid:
            print(f"[{ticker}] Email not sent: {validation_reason}")
            return

        try:
            self.notifier.send_email(
                ticker=ticker,
                corporate_sentiment=corporate_sentiment,
                retail_sentiment=retail_sentiment,
                news_df=ticker_news_df,
                sector_performance=sector_performance_data,
                raw_df=raw_df,
                metrics_df=metrics_df,
                earnings_df=earnings_df,
                earnings_estimate=earnings_estimate,
            )
            print(f"[{ticker}] Email sent successfully")
        except Exception as e:
            print(f"[{ticker}] Email not sent: Error occurred during email sending - {e}")