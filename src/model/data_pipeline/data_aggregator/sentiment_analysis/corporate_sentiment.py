import requests
import pandas as pd
import os
from dotenv import load_dotenv
from src.model.utils.logger_config import LoggerSetup

load_dotenv()


class CorporateSentimentAnalyzer:
    """
    A class to analyze sentiment from financial news articles for publicly traded companies.
    """

    def __init__(self):
        """
        Initialize the CorporateSentimentAnalyzer with API credentials and configuration.
        """
        self.logger = LoggerSetup.setup_logger(__name__)
        
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            self.logger.error("Alpha Vantage API key not set in environment variables")
            raise ValueError("Alpha Vantage API key not set. Please set ALPHA_VANTAGE_API_KEY in your environment.")

        try:
            self.limit = int(os.getenv("NEWS_SENTIMENT_LIMIT", "50"))
            self.logger.info(f"CorporateSentimentAnalyzer initialized with limit: {self.limit}")
        except ValueError:
            self.logger.error("NEWS_SENTIMENT_LIMIT must be an integer")
            raise ValueError("NEWS_SENTIMENT_LIMIT must be an integer.")

    def fetch_sentiment(self, ticker: str) -> float:
        """
        Fetch and analyze sentiment data for a given stock ticker.
        """
        try:
            self.logger.info(f"Fetching sentiment data for ticker: {ticker}")
            
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": ticker,
                "apikey": self.api_key,
            }
            
            self.logger.debug(f"Making API request to Alpha Vantage for {ticker}")
            r = requests.get(url, params=params)
            r.raise_for_status()
            
            data = r.json().get("feed", [])
            self.logger.debug(f"Received {len(data)} articles from API for {ticker}")

            articles = [
                {
                    "title": a["title"],
                    "published_at": a["time_published"],
                    "sentiment": a["overall_sentiment_score"],
                }
                for a in data[:self.limit]
            ]

            news_df = pd.DataFrame(articles)
            if news_df.empty:
                self.logger.warning(f"No sentiment data found for {ticker}")
                return 0.0

            sentiment_score = news_df["sentiment"].astype(float).mean()
            self.logger.info(f"Calculated sentiment score for {ticker}: {sentiment_score:.4f} (based on {len(news_df)} articles)")
            return sentiment_score
            
        except requests.RequestException as e:
            self.logger.error(f"API request failed for {ticker}: {e}")
            return 0.0
        except Exception as e:
            self.logger.error(f"Error fetching sentiment for {ticker}: {e}")
            return 0.0