import requests
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

class TickerNews:
    """
    Class for retrieving news articles for a specified ticker using Finnhub API.
    Free tier: 60 calls/minute, much better than Alpha Vantage's 25/day.
    """
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('FINNHUB_API_KEY')
        self.base_url = "https://finnhub.io/api/v1"
        
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY not found in environment variables")
    
    def get_ticker_news(self, ticker: str) -> pd.DataFrame:
        """
        Fetch the top 5 recent news headlines for a given ticker.
        Returns a DataFrame with columns: 'headline', 'summary', 'url', 'published_at'.
        """
        try:
            data = self._fetch_api_data(ticker)
            
            if not data:
                print(f"No news found for {ticker}")
                return pd.DataFrame()
            
            news_articles = self._process_news_articles(data, ticker)
            
            df = pd.DataFrame(news_articles)
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching news for {ticker}: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            return pd.DataFrame()
    
    def _fetch_api_data(self, ticker: str) -> list:
        """Fetch company news from Finnhub API."""
        from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        params = {
            'symbol': ticker.upper(),
            'from': from_date,
            'to': to_date,
            'token': self.api_key
        }
        
        response = requests.get(f"{self.base_url}/company-news", params=params)
        response.raise_for_status()
        return response.json()
    
    def _process_news_articles(self, data: list, ticker: str) -> list:
        """
        Process raw news articles into structured format.
        Sorts by date and keeps top 5.
        """
        articles = []
        
        for article in data:
            if self._is_valid_article(article):
                formatted_article = self._format_article(article)
                articles.append(formatted_article)
        
        articles = sorted(articles, key=lambda x: x['published_at'], reverse=True)
        
        return articles[:5]
    
    def _is_valid_article(self, article: dict) -> bool:
        """Basic validation for article quality."""
        headline = article.get('headline', '').strip()
        summary = article.get('summary', '').strip()
        
        if not headline:
            return False
        
        if len(summary) < 20:
            return False
        
        return True
    
    def _format_article(self, article: dict) -> dict:
        """Format a raw article into a structured dictionary."""
        return {
            'headline': article.get('headline', '').strip(),
            'summary': article.get('summary', '').strip(),
            'url': article.get('url', '').strip(),
            'published_at': pd.to_datetime(article.get('datetime'), unit='s')
        }