from typing import Dict, Any
import os
from src.model.utils.http_client import HttpClient
from src.model.data_aggregator.edgar_data_filings.ticker_retriever.cache import CacheInterface


class TickerMappingService:
    """
    Service for retrieving and caching mappings between stock tickers and CIKs
    (Central Index Key identifiers) from the SEC.

    This service fetches the official ticker-to-CIK mapping from the SEC,
    caches it locally in JSON format, and provides lookup functionality.
    It uses a configurable cache backend that implements the CacheInterface.
    """

    SEC_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
    DEFAULT_CACHE_FILE = os.path.join("src", "model", "data_aggregator", "edgar_data_filings", "ticker_retriever", "company_tickers.json")
    DEFAULT_REFRESH_DAYS = 30

    def __init__(self, http_client: HttpClient, cache: CacheInterface):
        """
        Initialize the TickerMappingService.
        """
        self.http_client = http_client
        self.cache = cache

    def get_ticker_to_cik_mapping(
        self,
        cache_file: str = DEFAULT_CACHE_FILE,
        refresh_days: int = DEFAULT_REFRESH_DAYS
    ) -> Dict[str, str]:
        """
        Retrieve the mapping of stock tickers to CIK identifiers.

        If the cache is expired (or missing), the data is refreshed from the SEC.
        Otherwise, the mapping is read directly from the local cache.
        """
        if self.cache.is_expired(cache_file, refresh_days):
            self._refresh_cache(cache_file)

        ticker_data = self.cache.read(cache_file)
        return self._build_ticker_mapping(ticker_data)

    def _refresh_cache(self, cache_file: str) -> None:
        """
        Refresh the cached ticker data from the SEC.

        This method fetches the latest ticker-to-CIK mapping and overwrites
        the local cache file.
        """
        response = self.http_client.get(self.SEC_TICKER_URL)
        self.cache.write(cache_file, response.text)

    def _build_ticker_mapping(self, ticker_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Build the mapping of tickers to CIKs from SEC JSON data.
        """
        return {
            entry["ticker"].upper(): str(entry["cik_str"]).zfill(10)
            for entry in ticker_data.values()
        }
