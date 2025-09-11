from typing import List, Tuple, Dict, Any
import pandas as pd
from datetime import datetime

from src.model.utils.http_client import HttpClient
from src.model.data_pipeline.data_aggregator.edgar_data_filings.ticker_retriever.cache import FileCache
from src.model.data_pipeline.data_aggregator.edgar_data_filings.ticker_retriever.ticker_service import TickerMappingService
from src.model.data_pipeline.data_aggregator.edgar_data_filings.sec_data_processor.extractor import SECDataExtractor
from src.model.data_pipeline.data_aggregator.edgar_data_filings.sec_data_processor.cleaner import SECDataCleaner
from src.model.data_pipeline.data_aggregator.edgar_data_filings.sec_data_processor.processor import SECDataProcessor
from src.model.data_pipeline.data_aggregator.sentiment_analysis.corporate_sentiment import CorporateSentimentAnalyzer
from src.model.data_pipeline.data_aggregator.sentiment_analysis.retail_sentiment import RetailSentimentAnalyzer
from src.model.data_pipeline.data_aggregator.ticker_news.news import TickerNews
from src.model.data_pipeline.data_aggregator.sector_analysis.sector_performance import SectorPerformance
from src.model.data_pipeline.data_aggregator.earnings_tracker.stock_earnings import EarningsFetcher
from src.model.notifier.notifications import EmailNotifier
from src.model.utils.logger_config import LoggerSetup
from src.model.utils.progress_tracker import ProgressTracker
from src.model.data_pipeline.database.data_validator import DataValidator
from src.model.data_pipeline.database.data_repository import DataRepository
from src.model.data_pipeline.database.db_manager import DatabaseManager
from decouple import config


class DataManager:
    """
    Streamlined manager class for retrieving, cleaning, and processing SEC financial data
    with consolidated validation and database operations.
    """

    def __init__(self, user_agent: str) -> None:
        """Initialize the DataManager with required services."""
        self.logger = LoggerSetup.setup_logger(__name__)
        self._initialize_services(user_agent)
        self.logger.info("DataManager initialized successfully")

    def _initialize_services(self, user_agent: str) -> None:
        """Initialize all required services and components."""
        # HTTP and caching services
        self.http_client = HttpClient(user_agent)
        self.cache = FileCache()
        
        # Data processing services
        self._initialize_data_processors()
        
        # Analysis services
        self._initialize_analyzers()
        
        # Database and notification services
        self._initialize_infrastructure()

    def _initialize_data_processors(self) -> None:
        """Initialize SEC data processing components."""
        self.ticker_service = TickerMappingService(self.http_client, self.cache)
        ticker_mapping = self.ticker_service.get_ticker_to_cik_mapping()
        
        self.extractor = SECDataExtractor(self.http_client, ticker_mapping)
        self.cleaner = SECDataCleaner()
        self.processor = SECDataProcessor()

    def _initialize_analyzers(self) -> None:
        """Initialize sentiment and analysis components."""
        self.corporate_sentiment_analyzer = CorporateSentimentAnalyzer()
        self.retail_sentiment_analyzer = RetailSentimentAnalyzer()
        self.ticker_news = TickerNews()
        self.quarterly_earnings = EarningsFetcher()
        self.sector_analyzer = SectorPerformance

    def _initialize_infrastructure(self) -> None:
        """Initialize database, validation, and notification components."""
        self.notifier = EmailNotifier()
        self.validator = DataValidator()
        self.db_manager = DatabaseManager()
        self.repository = DataRepository(self.db_manager)

    def _extract_raw_data(self, ticker: str, periods: int) -> List[Dict]:
        """Extract raw financial data from SEC filings."""
        raw_records = self.extractor.extract_raw_financial_data(ticker, periods)
        if not raw_records:
            self.logger.warning(f"No raw financial records found for {ticker}")
        return raw_records

    def _process_raw_records(self, raw_records: List[Dict], ticker: str) -> Dict[str, List[Dict]]:
        """Clean and enhance raw financial records."""
        cleaned_records = self.cleaner.clean_financial_records(raw_records)
        enhanced_records = self.processor.process_records_with_metrics(cleaned_records)
        return {ticker: enhanced_records}

    def _create_dataframes(self, processed_records: Dict[str, List[Dict]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Create and validate raw and metrics DataFrames."""
        raw_df, metrics_df = self.processor.create_split_dataframes(processed_records)
        
        cleaned_raw_df = self.validator.clean_dataframe(raw_df)
        cleaned_metrics_df = self.validator.clean_dataframe(metrics_df)
        
        return cleaned_raw_df, cleaned_metrics_df

    def _get_cleaned_financial_data(self, ticker: str, periods: int = 8) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieve and clean financial data once, returning both raw and metrics DataFrames.
        Eliminates duplicate cleaning operations.
        """
        try:
            self.logger.info(f"Retrieving financial data for {ticker} with {periods} periods")
            
            raw_records = self._extract_raw_data(ticker, periods)
            if not raw_records:
                return pd.DataFrame(), pd.DataFrame()
            
            processed_records = self._process_raw_records(raw_records, ticker)
            cleaned_raw_df, cleaned_metrics_df = self._create_dataframes(processed_records)
            
            self.logger.info(f"Financial data processed for {ticker} - Raw: {len(cleaned_raw_df)} rows, Metrics: {len(cleaned_metrics_df)} rows")
            return cleaned_raw_df, cleaned_metrics_df
            
        except Exception as e:
            self.logger.error(f"Error retrieving financial data for {ticker}: {e}")
            return pd.DataFrame(), pd.DataFrame()

    def _fetch_corporate_sentiment(self, ticker: str) -> float:
        """Fetch corporate sentiment score."""
        return float(self.corporate_sentiment_analyzer.fetch_sentiment(ticker))

    def _fetch_retail_sentiment(self, ticker: str) -> float:
        """Fetch retail sentiment score (placeholder implementation)."""
        return -0.15  # TODO: Replace with actual retail sentiment

    def _get_sentiment_data(self, ticker: str) -> Tuple[float, float]:
        """Get both corporate and retail sentiment scores."""
        try:
            self.logger.info(f"Fetching sentiment data for {ticker}")
            
            corporate_sentiment = self._fetch_corporate_sentiment(ticker)
            retail_sentiment = self._fetch_retail_sentiment(ticker)

            self.logger.info(f"Sentiment scores for {ticker} - Corporate: {corporate_sentiment}, Retail: {retail_sentiment}")
            return corporate_sentiment, retail_sentiment
        except Exception as e:
            self.logger.error(f"Error fetching sentiment for {ticker}: {e}")
            return 0.0, 0.0

    def _create_default_sector_data(self, ticker: str) -> Dict[str, Any]:
        """Create default sector performance data when retrieval fails."""
        return {
            "ticker": ticker,
            "sector": "Unknown",
            "sector_etf": "N/A",
            "ticker_1y_performance_pct": 0.0,
            "sector_1y_performance_pct": 0.0,
        }

    def _get_sector_performance(self, ticker: str) -> Dict[str, Any]:
        """Get sector performance data for the given ticker."""
        try:
            self.logger.info(f"Fetching sector performance for {ticker}")
            sector_analyzer = self.sector_analyzer(ticker)
            performance_data = sector_analyzer.get_sector_performance()
            self.logger.info(f"Successfully retrieved sector performance for {ticker}")
            return performance_data
        except Exception as e:
            self.logger.error(f"Error retrieving sector performance for {ticker}: {e}")
            return self._create_default_sector_data(ticker)

    def _collect_sentiment_data(self, ticker: str, data_package: Dict[str, Any], progress_tracker: ProgressTracker, progress_steps: List[str]) -> None:
        """Collect sentiment data and update progress."""
        corporate_sentiment, retail_sentiment = self._get_sentiment_data(ticker)
        data_package.update({
            'corporate_sentiment': corporate_sentiment,
            'retail_sentiment': retail_sentiment
        })
        progress_tracker.step(progress_steps[0])

    def _collect_news_data(self, ticker: str, data_package: Dict[str, Any], progress_tracker: ProgressTracker, progress_steps: List[str]) -> None:
        """Collect news data and update progress."""
        data_package['ticker_news_df'] = self.ticker_news.get_ticker_news(ticker)
        progress_tracker.step(progress_steps[1])

    def _collect_sector_data(self, ticker: str, data_package: Dict[str, Any], progress_tracker: ProgressTracker, progress_steps: List[str]) -> None:
        """Collect sector performance data and update progress."""
        data_package['sector_performance_data'] = self._get_sector_performance(ticker)
        progress_tracker.step(progress_steps[2])

    def _collect_earnings_data(self, ticker: str, data_package: Dict[str, Any], progress_tracker: ProgressTracker, progress_steps: List[str]) -> None:
        """Collect earnings data and estimates, update progress."""
        data_package['earnings_df'] = self.quarterly_earnings.fetch_earnings(ticker)
        progress_tracker.step(progress_steps[3])
        
        data_package['earnings_estimate'] = self.quarterly_earnings.fetch_next_earnings(ticker)
        progress_tracker.step(progress_steps[4])

    def _collect_financial_data(self, ticker: str, data_package: Dict[str, Any], progress_tracker: ProgressTracker, progress_steps: List[str]) -> None:
        """Collect financial data and update progress."""
        data_package['raw_df'], data_package['metrics_df'] = self._get_cleaned_financial_data(ticker)
        progress_tracker.step(progress_steps[5])

    def collect_all_ticker_data(self, ticker: str, progress_tracker: ProgressTracker) -> Tuple[Dict[str, Any], bool]:
        """
        Collect all data for a ticker with progress tracking.
        Returns (data_package, success)
        """
        progress_steps = self.get_processing_steps()
        data_package = {}
        
        try:
            self._collect_sentiment_data(ticker, data_package, progress_tracker, progress_steps)
            self._collect_news_data(ticker, data_package, progress_tracker, progress_steps)
            self._collect_sector_data(ticker, data_package, progress_tracker, progress_steps)
            self._collect_earnings_data(ticker, data_package, progress_tracker, progress_steps)
            self._collect_financial_data(ticker, data_package, progress_tracker, progress_steps)
            
            return data_package, True
            
        except Exception as e:
            self.logger.error(f"Data collection failed for {ticker}: {e}")
            return {}, False

    def _validate_data_package(self, ticker: str, data_package: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate the complete data package."""
        return self.validator.validate_ticker_data_package(
            data_package['corporate_sentiment'],
            data_package['retail_sentiment'],
            data_package['ticker_news_df'],
            data_package['sector_performance_data'],
            data_package['earnings_df'],
            data_package['raw_df'],
            data_package['metrics_df']
        )

    def _save_ticker_data(self, ticker: str, data_package: Dict[str, Any]) -> Tuple[bool, str]:
        """Save ticker data to database."""
        return self.repository.save_complete_ticker_data(ticker, data_package)

    def _handle_processing_failure(self, ticker: str, start_time: datetime, stage: str, error_message: str) -> None:
        """Handle processing failures with logging."""
        self._log_failed_processing(ticker, start_time, stage, error_message)
        if stage != "VALIDATION_FAILED":  # Don't raise for validation failures
            raise Exception(f"Processing failed at {stage}: {error_message}")

    def process_ticker(self, ticker: str, progress_tracker: ProgressTracker) -> None:
        """
        Main method to process a ticker using consolidated repository pattern.
        Processes all data in a single transaction for consistency.
        """
        start_time = datetime.now()
        progress_steps = self.get_processing_steps()
        
        if not progress_tracker.total_steps:
            progress_tracker.total_steps = len(progress_steps)
        
        try:
            # Collect all data
            data_package, success = self.collect_all_ticker_data(ticker, progress_tracker)
            if not success:
                self._handle_processing_failure(ticker, start_time, "DATA_COLLECTION_FAILED", "Failed to collect ticker data")
                return
            
            # Validate data package
            is_valid, validation_reason = self._validate_data_package(ticker, data_package)
            if not is_valid:
                self._handle_processing_failure(ticker, start_time, "VALIDATION_FAILED", validation_reason)
                return
            
            progress_tracker.step(progress_steps[6])
            
            # Save to database
            success, error_message = self._save_ticker_data(ticker, data_package)
            if not success:
                self._handle_processing_failure(ticker, start_time, "DATABASE_FAILED", error_message)
                return
            
            progress_tracker.step(progress_steps[7])
            
            # Send notification and log success
            self._send_email_and_log(ticker, data_package, start_time, progress_tracker, progress_steps)
            
        except Exception as e:
            self._log_failed_processing(ticker, start_time, "FAILED", str(e))
            raise

    def _generate_notification_data_hash(self, ticker: str, data_package: Dict[str, Any]) -> str:
        """Generate data hash for notification tracking."""
        return self.repository.generate_data_hash([
            ticker, 
            data_package['corporate_sentiment'], 
            data_package['retail_sentiment'],
            data_package['ticker_news_df'].to_dict(), 
            data_package['sector_performance_data'],
            data_package['earnings_df'].to_dict(), 
            data_package['earnings_estimate'],
            data_package['raw_df'].to_dict(), 
            data_package['metrics_df'].to_dict()
        ])

    def _send_notification(self, ticker: str, data_package: Dict[str, Any]) -> None:
        """Send email notification with collected data."""
        self.notifier.send_email(
            ticker=ticker,
            corporate_sentiment=data_package['corporate_sentiment'],
            retail_sentiment=data_package['retail_sentiment'],
            news_df=data_package['ticker_news_df'],
            sector_performance=data_package['sector_performance_data'],
            raw_df=data_package['raw_df'],
            metrics_df=data_package['metrics_df'],
            earnings_df=data_package['earnings_df'],
            earnings_estimate=data_package['earnings_estimate'],
        )

    def _log_success(self, ticker: str, processing_time: int, data_hash: str) -> None:
        """Log successful processing result."""
        self.repository.log_processing_result(
            ticker=ticker,
            recipient=config('USER_EMAIL'),
            processing_time=processing_time,
            data_hash=data_hash,
            status="SUCCESS"
        )

    def _send_email_and_log(self, ticker: str, data_package: Dict[str, Any], start_time: datetime, 
                           progress_tracker: ProgressTracker, progress_steps: List[str]) -> None:
        """Send email and log results using repository."""
        data_hash = self._generate_notification_data_hash(ticker, data_package)
        
        self._send_notification(ticker, data_package)
        
        processing_time = (datetime.now() - start_time).seconds
        self._log_success(ticker, processing_time, data_hash)
        
        progress_tracker.step(progress_steps[8])
        self.logger.info(f"Successfully processed {ticker} with consolidated database operations")

    def _log_failed_processing(self, ticker: str, start_time: datetime, status: str, error_message: str):
        """Log failed processing attempts using repository."""
        processing_time = (datetime.now() - start_time).seconds
        self.repository.log_processing_result(
            ticker=ticker,
            recipient=config('USER_EMAIL'),
            processing_time=processing_time,
            data_hash="",
            status=status,
            error_message=error_message
        )
        self.logger.warning(f"Processing failed for {ticker}: {error_message}")

    def get_processing_steps(self) -> List[str]:
        """Returns the list of processing steps for progress tracking."""
        return [
            "Retrieving sentiment data",
            "Retrieving news data", 
            "Retrieving sector performance data",
            "Retrieving earnings data",
            "Retrieving next earnings estimate",
            "Processing financial data",
            "Validating data package",
            "Saving data to database",
            "Sending email notification"
        ]

    def get_latest_data_summary(self, ticker: str) -> Dict[str, Any]:
        """Get a summary of the latest stored data for a ticker using repository."""
        return self.repository.get_latest_data_summary(ticker)

    def __del__(self):
        """Cleanup database connections on deletion."""
        try:
            if hasattr(self, 'db_manager'):
                self.db_manager.close_pool()
        except:
            pass