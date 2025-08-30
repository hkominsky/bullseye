import logging
import requests
from requests.exceptions import HTTPError, Timeout, ConnectionError, RequestException

logger = logging.getLogger(__name__)

class HttpClient:
    def __init__(self, user_agent: str, timeout: int = 10):
        self.headers = {"User-Agent": user_agent}
        self.timeout = timeout
    
    def get(self, url: str) -> requests.Response | None:
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response
        except HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response else "unknown"
            logger.error(f"HTTP {status_code} error for URL: {url} | {http_err}")
        except ConnectionError as conn_err:
            logger.error(f"Connection error for URL: {url} | {conn_err}")
        except Timeout:
            logger.error(f"Request timed out after {self.timeout}s for URL: {url}")
        except RequestException as req_err:
            logger.error(f"Request failed: {req_err} | URL: {url}")
        return None