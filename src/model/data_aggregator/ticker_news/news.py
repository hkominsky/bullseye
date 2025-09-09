import requests
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.model.utils.logger_config import LoggerSetup


class TickerNews:
    """
    Class for retrieving news articles for a specified ticker using Finnhub API.
    """
    
    def __init__(self):
        self.logger = LoggerSetup.setup_logger(__name__)
        
        load_dotenv()
        self.api_key = os.getenv('FINNHUB_API_KEY')
        self.base_url = "https://finnhub.io/api/v1"
        
        if not self.api_key:
            self.logger.error("FINNHUB_API_KEY not found in environment variables")
            raise ValueError("FINNHUB_API_KEY not found in environment variables")
        
        self.logger.info("TickerNews initialized successfully")
    
    def get_ticker_news(self, ticker: str) -> pd.DataFrame:
        """
        Fetch the top 5 recent news headlines for a given ticker.
        """
        try:
            self.logger.info(f"Fetching news for ticker: {ticker}")
            
            data = self._fetch_api_data(ticker)
            
            if not data:
                self.logger.warning(f"No news found for {ticker}")
                return pd.DataFrame()
            
            news_articles = self._process_news_articles(data)
            
            df = pd.DataFrame(news_articles)
            self.logger.info(f"Successfully retrieved {len(df)} news articles for {ticker}")
            return df
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error fetching news for {ticker}: {e}")
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error fetching news for {ticker}: {e}")
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
        
        self.logger.debug(f"Making API request to Finnhub for {ticker} from {from_date} to {to_date}")
        
        response = requests.get(f"{self.base_url}/company-news", params=params)
        response.raise_for_status()
        
        data = response.json()
        self.logger.debug(f"Received {len(data)} articles from Finnhub API for {ticker}")
        return data
    
    def _process_news_articles(self, data: list) -> list:
        """
        Process raw news articles into structured format.
        Sorts by date and keeps top 5.
        """
        articles = []
        valid_articles = 0
        
        for article in data:
            if self._is_valid_article(article):
                formatted_article = self._format_article(article)
                articles.append(formatted_article)
                valid_articles += 1
        
        self.logger.debug(f"Processed {valid_articles} valid articles out of {len(data)} total articles")
        
        articles = sorted(articles, key=lambda x: x['published_at'], reverse=True)
        top_articles = articles[:5]
        
        self.logger.debug(f"Returning top {len(top_articles)} articles")
        return top_articles
    
    def _is_valid_article(self, article: dict) -> bool:
        """Basic validation for article quality."""
        headline = article.get('headline', '').strip()
        summary = article.get('summary', '').strip()
        
        if not headline:
            self.logger.debug("Article rejected: no headline")
            return False
        
        if len(summary) < 20:
            self.logger.debug(f"Article rejected: summary too short ({len(summary)} chars)")
            return False
        
        return True
    
    def _format_article(self, article: dict) -> dict:
        """Format a raw article into a structured dictionary."""
        formatted = {
            'headline': article.get('headline', '').strip(),
            'summary': article.get('summary', '').strip(),
            'url': article.get('url', '').strip(),
            'published_at': pd.to_datetime(article.get('datetime'), unit='s')
        }
        
        self.logger.debug(f"Formatted article: {formatted['headline'][:50]}...")
        return formatted