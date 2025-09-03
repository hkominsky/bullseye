import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

class NewsSentimentAnalyzer:
    """
    Fetch institutional news for a given ticker and compute sentiment scores.
    Uses Alpha Vantage News API.
    """

    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("Alpha Vantage API key not set.")

    def fetch_news(self, ticker: str, limit: int = 50) -> pd.DataFrame:
        url = f"https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "apikey": self.api_key,
        }
        r = requests.get(url, params=params)
        data = r.json().get("feed", [])
        articles = [{"title": a["title"], "published_at": a["time_published"], "sentiment": a["overall_sentiment_score"]} for a in data[:limit]]
        return pd.DataFrame(articles)

    def average_sentiment(self, news_df: pd.DataFrame) -> float:
        if news_df.empty:
            return 0.0
        return news_df["sentiment"].astype(float).mean()
