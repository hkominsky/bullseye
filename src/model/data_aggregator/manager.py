from typing import List, Dict
import pandas as pd

from src.model.utils.http_client import HttpClient
from src.model.data_aggregatoredgar_data_filings.ticker_retriever.cache import FileCache
from src.model.data_aggregatoredgar_data_filings.ticker_retriever.ticker_service import TickerMappingService
from src.model.data_aggregator.edgar_data_filings.sec_data_processor.extractor import SECDataExtractor
from src.model.data_aggregator.edgar_data_filings.sec_data_processor.cleaner import SECDataCleaner
from src.model.data_aggregator.edgar_data_filings.sec_data_processor.processor import SECDataProcessor
from src.model.data_aggregator.sentiment_analyzers.corporate_sentiment.py import NewsSentimentAnalyzer
from src.model.data_aggregator.sentiment_analyzers.retail_sentiment.py import RetailSentimentAnalyzer
from src.model.utils.models import FinancialRecord


class SECDataManager:
    """
    Manager class for retrieving, cleaning, and processing SEC financial data for a set of tickers.
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
        self.news_analyzer = NewsSentimentAnalyzer()

    def get_comprehensive_financial_data(
        self, tickers: List[str], periods: int = 8
    ) -> Dict[str, List[FinancialRecord]]:
        """
        Retrieve, clean, and process financial data for a list of tickers.

        Args:
            tickers (List[str]): A list of stock ticker symbols.
            periods (int, optional): Number of reporting periods to retrieve. Defaults to 8.

        Returns:
            Dict[str, List[FinancialRecord]]: Dictionary mapping each ticker to its list of processed financial records.
        """
        financial_data: Dict[str, List[FinancialRecord]] = {}

        for ticker in tickers:
            try:
                raw_records = self.extractor.extract_raw_financial_data(ticker, periods)
                cleaned_records = self.cleaner.clean_financial_records(raw_records)
                enhanced_records = self.processor.process_records_with_metrics(cleaned_records)
                financial_data[ticker] = enhanced_records
            except Exception as e:
                print(f"Error retrieving financial data for {ticker}: {e}")
                financial_data[ticker] = []

        return financial_data

    def get_financial_dataframe(self, tickers: List[str]) -> pd.DataFrame:
        """
        Get financial data for tickers in a cleaned Pandas DataFrame format.

        Args:
            tickers (List[str]): A list of stock ticker symbols.

        Returns:
            pd.DataFrame: Cleaned financial data in tabular format.
        """
        financial_data = self.get_comprehensive_financial_data(tickers)
        df = self.processor.create_financial_dataframe(financial_data)
        cleaned_df = self.cleaner.clean_dataframe(df)
        return cleaned_df

    def get_split_financial_dataframes(self, tickers: List[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get financial data for tickers split into raw data and calculated metrics DataFrames.
        
        Args:
            tickers (List[str]): A list of stock ticker symbols.
            
        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (raw_data_df, calculated_metrics_df)
        """
        financial_data = self.get_comprehensive_financial_data(tickers)
        raw_df, metrics_df = self.processor.create_split_dataframes(financial_data)
        
        # Clean both DataFrames
        cleaned_raw_df = self.cleaner.clean_dataframe(raw_df)
        cleaned_metrics_df = self.cleaner.clean_dataframe(metrics_df)
        
        return cleaned_raw_df, cleaned_metrics_df