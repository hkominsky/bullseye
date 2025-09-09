import os
import tweepy
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv

load_dotenv()


class RetailSentimentAnalyzer:
    """
    Class allows for the computation of retail sentiment from Twitter API data relating to the ticker.
    """

    def __init__(self):
        """
        Initialize Twitter API client and sentiment analyzer.
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
        Fetches relevant scores to compute sentiment score then returns it.
        """

        tweets_df = self.fetch_tweets(ticker, self.num_tweets)
        tweets_df = self.compute_sentiment(tweets_df)
        return self.average_sentiment(tweets_df)

    def fetch_tweets(self, ticker: str, count: int) -> pd.DataFrame:
        """
        Fetch recent tweets mentioning the ticker.
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
        """
        if tweets_df.empty:
            return 0.0
        return tweets_df["sentiment"].mean()
