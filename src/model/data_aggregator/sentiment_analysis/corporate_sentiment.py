import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()


class CorporateSentimentAnalyzer:
    """
    A class to analyze sentiment from financial news articles for publicly traded companies.
    """

    def __init__(self):
        """
        Initialize the CorporateSentimentAnalyzer with API credentials and configuration.
        """
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("Alpha Vantage API key not set. Please set ALPHA_VANTAGE_API_KEY in your environment.")

        try:
            self.limit = int(os.getenv("NEWS_SENTIMENT_LIMIT", "50"))
        except ValueError:
            raise ValueError("NEWS_SENTIMENT_LIMIT must be an integer.")

    def fetch_sentiment(self, ticker: str) -> float:
        """
        Fetch and analyze sentiment data for a given stock ticker.
        """
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "apikey": self.api_key,
        }
        
        r = requests.get(url, params=params)
        data = r.json().get("feed", [])

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
            return 0.0
            
        return news_df["sentiment"].astype(float).mean()