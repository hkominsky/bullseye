from typing import Dict, Any
from http_client import HttpClient
from cache import CacheInterface

class TickerMappingService:
    SEC_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
    DEFAULT_CACHE_FILE = "company_tickers.json"
    DEFAULT_REFRESH_DAYS = 30
    
    def __init__(self, http_client: HttpClient, cache: CacheInterface):
        self.http_client = http_client
        self.cache = cache
    
    def get_ticker_to_cik_mapping(self, 
                                  cache_file: str = DEFAULT_CACHE_FILE,
                                  refresh_days: int = DEFAULT_REFRESH_DAYS) -> Dict[str, str]:
        if self.cache.is_expired(cache_file, refresh_days):
            self._refresh_cache(cache_file)
        
        ticker_data = self.cache.read(cache_file)
        return self._build_ticker_mapping(ticker_data)
    
    def _refresh_cache(self, cache_file: str) -> None:
        response = self.http_client.get(self.SEC_TICKER_URL)
        self.cache.write(cache_file, response.text)
    
    def _build_ticker_mapping(self, ticker_data: Dict[str, Any]) -> Dict[str, str]:
        return {
            entry["ticker"].upper(): str(entry["cik_str"]).zfill(10)
            for entry in ticker_data.values()
        }
