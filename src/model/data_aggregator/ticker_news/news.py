import yfinance as yf
import pandas as pd

class TickerNews:
    """
    Class for retrieving a summary of the three most recent news articles 
    regarding a specified ticker.
    """

    def get_ticker_news(self, ticker: str) -> pd.DataFrame:
        """
        Fetch the top 3 recent news headlines for a given ticker, including a short summary and URL.

        Returns a DataFrame with columns: 'headline', 'summary', 'url'.
        """
        stock = yf.Ticker(ticker)

        news_articles = stock.news[:3]

        news = []
        for article in news_articles:
            headline = article.get('title', '')
            summary = article.get('summary', '') 
            url = article.get('link', '')
            news.append({'headline': headline, 'summary': summary, 'url': url})

        return pd.DataFrame(news)
