from typing import Dict, List, Tuple
import pandas as pd

from src.model.utils.http_client import HttpClient
from src.model.data_aggregator.edgar_data_filings.ticker_retriever.cache import FileCache
from src.model.data_aggregator.edgar_data_filings.ticker_retriever.ticker_service import TickerMappingService
from src.model.data_aggregator.edgar_data_filings.sec_data_processor.extractor import SECDataExtractor
from src.model.data_aggregator.edgar_data_filings.sec_data_processor.cleaner import SECDataCleaner
from src.model.data_aggregator.edgar_data_filings.sec_data_processor.processor import SECDataProcessor
from src.model.data_aggregator.sentiment_analyzers.corporate_sentiment import CorporateSentimentAnalyzer
from src.model.data_aggregator.sentiment_analyzers.retail_sentiment import RetailSentimentAnalyzer
from src.model.data_aggregator.ticker_news.news import TickerNews
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

        Args:
            user_agent (str): The user agent string for SEC API requests.
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
        retail_sentiment = float(self.retail_sentiment_analyzer.fetch_sentiment(ticker))
        return corporate_sentiment, retail_sentiment

    def save_data(self, ticker: str, raw_df: pd.DataFrame, metrics_df: pd.DataFrame) -> None:
        """Save raw and metrics DataFrames to CSV files."""
        raw_output_file = f"src/model/data_aggregator/edgar_data_filings/sec_data_processor/{ticker}_raw_financial_data.csv"
        metrics_output_file = f"src/model/data_aggregator/edgar_data_filings/sec_data_processor/{ticker}_calculated_metrics.csv"

        if not raw_df.empty:
            raw_df.to_csv(raw_output_file, index=False)
        if not metrics_df.empty:
            metrics_df.to_csv(metrics_output_file, index=False)

    def process_stock(self, ticker: str) -> None:
        """
        Process financial data and sentiment for a single stock:
        - Retrieve dataframes
        - Save CSVs
        - Send email notification (now includes sentiments + news)
        """
        corporate_sentiment, retail_sentiment = self.get_sentiment(ticker)
        ticker_news_df = self.ticker_news.get_ticker_news(ticker)  # expected: newest first
        raw_df, metrics_df = self.get_financial_dataframes(ticker)

        if raw_df.empty or metrics_df.empty:
            print(f"[{ticker}] No financial data retrieved.")
            return

        if ticker_news_df is None or ticker_news_df.empty:
            print(f"[{ticker}] No news available from TickerNews(). Proceeding without news.")
            return
            
        # Save CSVs
        self.save_data(ticker, raw_df, metrics_df)

        self.notifier.send_email(
            ticker=ticker,
            corporate_sentiment=corporate_sentiment,
            retail_sentiment=retail_sentiment,
            news_df=ticker_news_df,
            metrics_df=metrics_df,
        )