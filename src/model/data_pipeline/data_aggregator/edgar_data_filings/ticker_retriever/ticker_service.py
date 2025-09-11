from typing import Dict, Any
import os
from src.model.utils.http_client import HttpClient
from src.model.data_pipeline.data_aggregator.edgar_data_filings.ticker_retriever.cache import CacheInterface
from src.model.utils.logger_config import LoggerSetup


class TickerMappingService:
    """
    Service for retrieving and caching mappings between stock tickers and CIKs from the SEC.
    """

    SEC_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
    DEFAULT_CACHE_FILE = os.path.join("src", "model", "data_pipeline", "data_aggregator", "edgar_data_filings", "ticker_retriever", "company_tickers.json")
    DEFAULT_REFRESH_DAYS = 30

    def __init__(self, http_client: HttpClient, cache: CacheInterface):
        """
        Initialize the TickerMappingService.
        """
        self.logger = LoggerSetup.setup_logger(__name__)
        self.http_client = http_client
        self.cache = cache
        self.logger.info("TickerMappingService initialized")

    def get_ticker_to_cik_mapping(
        self,
        cache_file: str = DEFAULT_CACHE_FILE,
        refresh_days: int = DEFAULT_REFRESH_DAYS
    ) -> Dict[str, str]:
        """
        Retrieve the mapping of stock tickers to CIK identifiers.

        If the cache is expired (or missing), the data is refreshed.
        Otherwise, the mapping is read directly from the local cache.
        """
        self.logger.info(f"Retrieving ticker-to-CIK mapping from cache: {cache_file}")
        
        if self.cache.is_expired(cache_file, refresh_days):
            self.logger.info("Cache is expired, refreshing ticker data")
            self._refresh_cache(cache_file)
        else:
            self.logger.info("Using cached ticker data")

        ticker_data = self.cache.read(cache_file)
        mapping = self._build_ticker_mapping(ticker_data)
        self.logger.info(f"Successfully built ticker mapping with {len(mapping)} entries")
        return mapping

    def _refresh_cache(self, cache_file: str) -> None:
        """
        Fetches the latest ticker-to-CIK mapping and overwrites the local cache file.
        """
        try:
            self.logger.info(f"Fetching fresh ticker data from SEC: {self.SEC_TICKER_URL}")
            response = self.http_client.get(self.SEC_TICKER_URL)
            self.cache.write(cache_file, response.text)
            self.logger.info(f"Successfully refreshed cache file: {cache_file}")
        except Exception as e:
            self.logger.error(f"Failed to refresh cache: {e}")
            raise

    def _build_ticker_mapping(self, ticker_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Build the mapping of tickers to CIKs from SEC JSON data.
        """
        try:
            self.logger.debug("Building ticker-to-CIK mapping from SEC data")
            mapping = {
                entry["ticker"].upper(): str(entry["cik_str"]).zfill(10)
                for entry in ticker_data.values()
            }
            self.logger.debug(f"Built mapping for {len(mapping)} tickers")
            return mapping
        except Exception as e:
            self.logger.error(f"Error building ticker mapping: {e}")
            raise