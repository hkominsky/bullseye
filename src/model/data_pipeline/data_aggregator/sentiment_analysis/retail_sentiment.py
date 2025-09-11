import os
import tweepy
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv
from src.model.utils.logger_config import LoggerSetup

load_dotenv()


class RetailSentimentAnalyzer:
    """
    Class allows for the computation of retail sentiment from Twitter API data relating to the ticker.
    """

    def __init__(self):
        """
        Initialize Twitter API client and sentiment analyzer.
        """
        self.logger = LoggerSetup.setup_logger(__name__)
        
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.num_tweets = int(os.getenv("NUM_TWEETS_SENTIMENT", "100"))

        if not all([api_key, api_secret, access_token, access_token_secret]):
            self.logger.error("Twitter API credentials are not set in environment variables")
            raise ValueError("Twitter API credentials are not set in the environment variables.")

        try:
            auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
            self.api = tweepy.API(auth)
            self.analyzer = SentimentIntensityAnalyzer()
            self.logger.info(f"RetailSentimentAnalyzer initialized with tweet limit: {self.num_tweets}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Twitter API client: {e}")
            raise

    def fetch_sentiment(self, ticker: str) -> float:
        """
        Fetches relevant scores to compute sentiment score then returns it.
        """
        try:
            self.logger.info(f"Starting sentiment analysis for ticker: {ticker}")
            
            tweets_df = self.fetch_tweets(ticker, self.num_tweets)
            tweets_df = self.compute_sentiment(tweets_df)
            sentiment_score = self.average_sentiment(tweets_df)
            
            self.logger.info(f"Completed sentiment analysis for {ticker}: {sentiment_score:.4f}")
            return sentiment_score
        except Exception as e:
            self.logger.error(f"Error in fetch_sentiment for {ticker}: {e}")
            return 0.0

    def fetch_tweets(self, ticker: str, count: int) -> pd.DataFrame:
        """
        Fetch recent tweets mentioning the ticker.
        """
        try:
            self.logger.debug(f"Fetching {count} tweets for ticker: {ticker}")
            query = f"${ticker} -filter:retweets"
            
            tweets = tweepy.Cursor(
                self.api.search_tweets,
                q=query,
                lang="en",
                tweet_mode="extended"
            ).items(count)
            
            data = [{"tweet": t.full_text, "created_at": t.created_at} for t in tweets]
            tweets_df = pd.DataFrame(data)
            
            self.logger.debug(f"Successfully fetched {len(tweets_df)} tweets for {ticker}")
            return tweets_df
        except Exception as e:
            self.logger.error(f"Error fetching tweets for {ticker}: {e}")
            return pd.DataFrame()

    def compute_sentiment(self, tweets_df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze sentiment of tweets and add a sentiment score column.
        """
        if tweets_df.empty:
            self.logger.warning("No tweets to analyze sentiment for")
            tweets_df["sentiment"] = []
            return tweets_df
        
        try:
            self.logger.debug(f"Computing sentiment for {len(tweets_df)} tweets")
            tweets_df["sentiment"] = tweets_df["tweet"].apply(
                lambda x: self.analyzer.polarity_scores(x)["compound"]
            )
            self.logger.debug("Sentiment computation completed")
            return tweets_df
        except Exception as e:
            self.logger.error(f"Error computing sentiment: {e}")
            tweets_df["sentiment"] = 0.0
            return tweets_df

    def average_sentiment(self, tweets_df: pd.DataFrame) -> float:
        """
        Compute average sentiment score for a set of tweets.
        """
        if tweets_df.empty:
            self.logger.warning("No tweets available for sentiment averaging")
            return 0.0
        
        try:
            avg_sentiment = tweets_df["sentiment"].mean()
            self.logger.debug(f"Average sentiment calculated: {avg_sentiment:.4f} from {len(tweets_df)} tweets")
            return avg_sentiment
        except Exception as e:
            self.logger.error(f"Error calculating average sentiment: {e}")
            return 0.0