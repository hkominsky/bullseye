import logging
import requests
from requests.exceptions import HTTPError, Timeout, ConnectionError, RequestException
from src.model.utils.logger_config import LoggerSetup


class HttpClient:
    """
    A simple HTTP client wrapper with built-in error handling and logging.
    """

    def __init__(self, user_agent: str, timeout: int = 10, log_level: int = logging.INFO):
        self.headers = {"User-Agent": user_agent}
        self.timeout = timeout
        
        self.logger = LoggerSetup.setup_logger(
            name=__name__,
            level=log_level,
            filename="http_client.log"
        )
        
        self.logger.info(f"HttpClient initialized with timeout: {timeout}s")

    def get(self, url: str) -> requests.Response | None:
        self.logger.debug(f"Making GET request to: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            self.logger.info(f"Successful GET request to {url} - Status: {response.status_code}")
            return response
            
        except HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response else "unknown"
            self.logger.error(f"HTTP {status_code} error for URL: {url} | {http_err}")
        except ConnectionError as conn_err:
            self.logger.error(f"Connection error for URL: {url} | {conn_err}")
        except Timeout:
            self.logger.error(f"Request timed out after {self.timeout}s for URL: {url}")
        except RequestException as req_err:
            self.logger.error(f"Request failed: {req_err} | URL: {url}")
            
        return None