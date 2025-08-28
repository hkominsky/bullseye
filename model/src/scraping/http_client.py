import requests

class HttpClient:
    def __init__(self, user_agent: str):
        self.headers = {"User-Agent": user_agent}
    
    def get(self, url: str) -> requests.Response:
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response
