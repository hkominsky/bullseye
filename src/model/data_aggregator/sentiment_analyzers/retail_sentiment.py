import os
import tweepy
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv

load_dotenv()

class RetailSentimentAnalyzer:
    """
    A sentiment analysis tool for financial markets that:
    - Fetches tweets related to a given ticker symbol.
    - Computes sentiment scores for the tweets using VADER.
    - Returns the average sentiment score.
    
    Example:
        analyzer = RetailSentimentAnalyzer()
        sentiment = analyzer.fetch_sentiment("AAPL", 100)
        print(sentiment)
    """

    def __init__(self):
        """
        Initialize Twitter API client and sentiment analyzer using environment variables.
        Raises:
            ValueError: If any required API credentials are missing.
        """
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.num_tweets = int(os.getenv("NUM_TWEETS_SENTIMENT", "100"))

        if not all([api_key, api_secret, access_token, access_token_secret]):
            raise ValueError("Twitter API credentials are not set in the environment variables.")

        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
        self.api = tweepy.API(auth)

        self.analyzer = SentimentIntensityAnalyzer()

    def fetch_sentiment(self, ticker: str) -> float:
        """
        Orchestrates the sentiment analysis process:
        - Fetches tweets for the given ticker.
        - Computes sentiment scores.
        - Returns the average sentiment score.

        Args:
            ticker (str): Stock ticker symbol (e.g., "AAPL").

        Returns:
            float: Average sentiment score (−1.0 to +1.0).
        """

        tweets_df = self.fetch_tweets(ticker, self.num_tweets)
        tweets_df = self.compute_sentiment(tweets_df)
        return self.average_sentiment(tweets_df)

    def fetch_tweets(self, ticker: str, count: int) -> pd.DataFrame:
        """
        Fetch recent tweets mentioning the ticker.

        Args:
            ticker (str): Stock ticker symbol.
            count (int): Number of tweets to fetch.

        Returns:
            pd.DataFrame: DataFrame containing tweet text and creation time.
        """
        query = f"${ticker} -filter:retweets"
        tweets = tweepy.Cursor(
            self.api.search_tweets,
            q=query,
            lang="en",
            tweet_mode="extended"
        ).items(count)
        data = [{"tweet": t.full_text, "created_at": t.created_at} for t in tweets]
        return pd.DataFrame(data)

    def compute_sentiment(self, tweets_df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze sentiment of tweets and add a sentiment score column.

        Args:
            tweets_df (pd.DataFrame): DataFrame of tweets.

        Returns:
            pd.DataFrame: DataFrame with an added 'sentiment' column.
        """
        if tweets_df.empty:
            tweets_df["sentiment"] = []
            return tweets_df
        tweets_df["sentiment"] = tweets_df["tweet"].apply(
            lambda x: self.analyzer.polarity_scores(x)["compound"]
        )
        return tweets_df

    def average_sentiment(self, tweets_df: pd.DataFrame) -> float:
        """
        Compute average sentiment score for a set of tweets.

        Args:
            tweets_df (pd.DataFrame): DataFrame with sentiment scores.

        Returns:
            float: Average sentiment score (0.0 if no tweets).
        """
        if tweets_df.empty:
            return 0.0
        return tweets_df["sentiment"].mean()
