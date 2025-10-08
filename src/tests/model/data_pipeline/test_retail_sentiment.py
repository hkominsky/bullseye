import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from src.model.data_pipeline.retail_sentiment_analyzer import RetailSentimentAnalyzer


class TestRetailSentimentAnalyzer:
    
    @pytest.fixture
    def mock_env(self):
        with patch.dict('os.environ', {
            'TWITTER_API_KEY': 'test_api_key',
            'TWITTER_API_SECRET': 'test_api_secret',
            'TWITTER_ACCESS_TOKEN': 'test_access_token',
            'TWITTER_ACCESS_TOKEN_SECRET': 'test_access_token_secret',
            'NUM_TWEETS_SENTIMENT': '100'
        }):
            yield
    
    @pytest.fixture
    def analyzer(self, mock_env):
        with patch('src.model.data_pipeline.retail_sentiment_analyzer.load_dotenv'):
            with patch('src.model.data_pipeline.retail_sentiment_analyzer.LoggerSetup'):
                with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.OAuth1UserHandler'):
                    with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.API'):
                        return RetailSentimentAnalyzer()
    
    def test_init_success(self, mock_env):
        with patch('src.model.data_pipeline.retail_sentiment_analyzer.load_dotenv'):
            with patch('src.model.data_pipeline.retail_sentiment_analyzer.LoggerSetup'):
                with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.OAuth1UserHandler') as mock_auth:
                    with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.API') as mock_api:
                        analyzer = RetailSentimentAnalyzer()
                        assert analyzer.num_tweets == 100
                        mock_auth.assert_called_once()
                        mock_api.assert_called_once()
    
    def test_init_missing_credentials(self):
        with patch.dict('os.environ', {}, clear=True):
            with patch('src.model.data_pipeline.retail_sentiment_analyzer.load_dotenv'):
                with patch('src.model.data_pipeline.retail_sentiment_analyzer.LoggerSetup'):
                    with pytest.raises(ValueError, match="Twitter API credentials are not set"):
                        RetailSentimentAnalyzer()
    
    def test_init_missing_api_key(self):
        with patch.dict('os.environ', {
            'TWITTER_API_SECRET': 'test_secret',
            'TWITTER_ACCESS_TOKEN': 'test_token',
            'TWITTER_ACCESS_TOKEN_SECRET': 'test_token_secret'
        }):
            with patch('src.model.data_pipeline.retail_sentiment_analyzer.load_dotenv'):
                with patch('src.model.data_pipeline.retail_sentiment_analyzer.LoggerSetup'):
                    with pytest.raises(ValueError, match="Twitter API credentials are not set"):
                        RetailSentimentAnalyzer()
    
    def test_init_custom_num_tweets(self):
        with patch.dict('os.environ', {
            'TWITTER_API_KEY': 'test_key',
            'TWITTER_API_SECRET': 'test_secret',
            'TWITTER_ACCESS_TOKEN': 'test_token',
            'TWITTER_ACCESS_TOKEN_SECRET': 'test_token_secret',
            'NUM_TWEETS_SENTIMENT': '200'
        }):
            with patch('src.model.data_pipeline.retail_sentiment_analyzer.load_dotenv'):
                with patch('src.model.data_pipeline.retail_sentiment_analyzer.LoggerSetup'):
                    with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.OAuth1UserHandler'):
                        with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.API'):
                            analyzer = RetailSentimentAnalyzer()
                            assert analyzer.num_tweets == 200
    
    def test_init_default_num_tweets(self):
        with patch.dict('os.environ', {
            'TWITTER_API_KEY': 'test_key',
            'TWITTER_API_SECRET': 'test_secret',
            'TWITTER_ACCESS_TOKEN': 'test_token',
            'TWITTER_ACCESS_TOKEN_SECRET': 'test_token_secret'
        }):
            with patch('src.model.data_pipeline.retail_sentiment_analyzer.load_dotenv'):
                with patch('src.model.data_pipeline.retail_sentiment_analyzer.LoggerSetup'):
                    with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.OAuth1UserHandler'):
                        with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.API'):
                            analyzer = RetailSentimentAnalyzer()
                            assert analyzer.num_tweets == 100
    
    def test_init_tweepy_exception(self, mock_env):
        with patch('src.model.data_pipeline.retail_sentiment_analyzer.load_dotenv'):
            with patch('src.model.data_pipeline.retail_sentiment_analyzer.LoggerSetup'):
                with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.OAuth1UserHandler', side_effect=Exception("Auth failed")):
                    with pytest.raises(Exception):
                        RetailSentimentAnalyzer()
    
    def test_fetch_tweets_success(self, analyzer):
        mock_tweet1 = Mock()
        mock_tweet1.full_text = "AAPL stock is great!"
        mock_tweet1.created_at = "2024-01-01"
        
        mock_tweet2 = Mock()
        mock_tweet2.full_text = "AAPL to the moon!"
        mock_tweet2.created_at = "2024-01-02"
        
        with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.Cursor') as mock_cursor:
            mock_cursor.return_value.items.return_value = [mock_tweet1, mock_tweet2]
            
            result = analyzer.fetch_tweets('AAPL', 2)
            
            assert len(result) == 2
            assert 'tweet' in result.columns
            assert 'created_at' in result.columns
            assert result['tweet'].iloc[0] == "AAPL stock is great!"
    
    def test_fetch_tweets_empty_result(self, analyzer):
        with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.Cursor') as mock_cursor:
            mock_cursor.return_value.items.return_value = []
            
            result = analyzer.fetch_tweets('AAPL', 10)
            
            assert result.empty
    
    def test_fetch_tweets_exception(self, analyzer):
        with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.Cursor', side_effect=Exception("API Error")):
            result = analyzer.fetch_tweets('AAPL', 10)
            
            assert result.empty
    
    def test_fetch_tweets_query_format(self, analyzer):
        with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.Cursor') as mock_cursor:
            mock_cursor.return_value.items.return_value = []
            
            analyzer.fetch_tweets('MSFT', 10)
            
            call_kwargs = mock_cursor.call_args[1]
            assert '$MSFT' in call_kwargs['q']
            assert '-filter:retweets' in call_kwargs['q']
            assert call_kwargs['lang'] == 'en'
            assert call_kwargs['tweet_mode'] == 'extended'
    
    def test_compute_sentiment_success(self, analyzer):
        tweets_df = pd.DataFrame({
            'tweet': ['This is great!', 'This is terrible!', 'This is okay.']
        })
        
        with patch.object(analyzer.analyzer, 'polarity_scores') as mock_scores:
            mock_scores.side_effect = [
                {'compound': 0.8},
                {'compound': -0.7},
                {'compound': 0.1}
            ]
            
            result = analyzer.compute_sentiment(tweets_df)
            
            assert 'sentiment' in result.columns
            assert len(result) == 3
            assert result['sentiment'].iloc[0] == 0.8
            assert result['sentiment'].iloc[1] == -0.7
            assert result['sentiment'].iloc[2] == 0.1
    
    def test_compute_sentiment_empty_dataframe(self, analyzer):
        tweets_df = pd.DataFrame()
        
        result = analyzer.compute_sentiment(tweets_df)
        
        assert 'sentiment' in result.columns
        assert result.empty
    
    def test_compute_sentiment_exception(self, analyzer):
        tweets_df = pd.DataFrame({'tweet': ['Test tweet']})
        
        with patch.object(analyzer.analyzer, 'polarity_scores', side_effect=Exception("Analysis failed")):
            result = analyzer.compute_sentiment(tweets_df)
            
            assert 'sentiment' in result.columns
            assert result['sentiment'].iloc[0] == 0.0
    
    def test_average_sentiment_success(self, analyzer):
        tweets_df = pd.DataFrame({
            'sentiment': [0.5, 0.3, 0.7, 0.1]
        })
        
        result = analyzer.average_sentiment(tweets_df)
        
        assert result == pytest.approx(0.4, rel=0.01)
    
    def test_average_sentiment_empty_dataframe(self, analyzer):
        tweets_df = pd.DataFrame()
        
        result = analyzer.average_sentiment(tweets_df)
        
        assert result == 0.0
    
    def test_average_sentiment_all_positive(self, analyzer):
        tweets_df = pd.DataFrame({
            'sentiment': [0.8, 0.9, 0.7]
        })
        
        result = analyzer.average_sentiment(tweets_df)
        
        assert result == pytest.approx(0.8, rel=0.01)
    
    def test_average_sentiment_all_negative(self, analyzer):
        tweets_df = pd.DataFrame({
            'sentiment': [-0.6, -0.8, -0.7]
        })
        
        result = analyzer.average_sentiment(tweets_df)
        
        assert result == pytest.approx(-0.7, rel=0.01)
    
    def test_average_sentiment_mixed(self, analyzer):
        tweets_df = pd.DataFrame({
            'sentiment': [0.5, -0.3, 0.1, -0.1]
        })
        
        result = analyzer.average_sentiment(tweets_df)
        
        assert result == pytest.approx(0.05, rel=0.01)
    
    def test_average_sentiment_exception(self, analyzer):
        tweets_df = pd.DataFrame({'sentiment': ['invalid']})
        
        result = analyzer.average_sentiment(tweets_df)
        
        assert result == 0.0
    
    def test_fetch_sentiment_full_flow(self, analyzer):
        mock_tweet = Mock()
        mock_tweet.full_text = "AAPL is amazing!"
        mock_tweet.created_at = "2024-01-01"
        
        with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.Cursor') as mock_cursor:
            mock_cursor.return_value.items.return_value = [mock_tweet]
            
            with patch.object(analyzer.analyzer, 'polarity_scores', return_value={'compound': 0.6}):
                result = analyzer.fetch_sentiment('AAPL')
                
                assert result == pytest.approx(0.6, rel=0.01)
    
    def test_fetch_sentiment_no_tweets(self, analyzer):
        with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.Cursor') as mock_cursor:
            mock_cursor.return_value.items.return_value = []
            
            result = analyzer.fetch_sentiment('AAPL')
            
            assert result == 0.0
    
    def test_fetch_sentiment_exception(self, analyzer):
        with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.Cursor', side_effect=Exception("Error")):
            result = analyzer.fetch_sentiment('AAPL')
            
            assert result == 0.0
    
    def test_fetch_sentiment_uses_num_tweets(self, analyzer):
        analyzer.num_tweets = 50
        
        with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.Cursor') as mock_cursor:
            mock_cursor.return_value.items.return_value = []
            
            analyzer.fetch_sentiment('AAPL')
            
            mock_cursor.return_value.items.assert_called_once_with(50)
    
    def test_compute_sentiment_vader_scores(self, analyzer):
        tweets_df = pd.DataFrame({
            'tweet': ['I love this stock!']
        })
        
        with patch.object(analyzer.analyzer, 'polarity_scores') as mock_scores:
            mock_scores.return_value = {
                'compound': 0.6,
                'pos': 0.7,
                'neg': 0.0,
                'neu': 0.3
            }
            
            result = analyzer.compute_sentiment(tweets_df)
            
            assert result['sentiment'].iloc[0] == 0.6
            mock_scores.assert_called_once_with('I love this stock!')
    
    def test_fetch_tweets_count_parameter(self, analyzer):
        with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.Cursor') as mock_cursor:
            mock_cursor.return_value.items.return_value = []
            
            analyzer.fetch_tweets('AAPL', 25)
            
            mock_cursor.return_value.items.assert_called_once_with(25)
    
    def test_average_sentiment_single_tweet(self, analyzer):
        tweets_df = pd.DataFrame({'sentiment': [0.5]})
        
        result = analyzer.average_sentiment(tweets_df)
        
        assert result == 0.5
    
    def test_fetch_sentiment_integration(self, analyzer):
        mock_tweets = [Mock(full_text=f"Tweet {i}", created_at="2024-01-01") for i in range(3)]
        
        with patch('src.model.data_pipeline.retail_sentiment_analyzer.tweepy.Cursor') as mock_cursor:
            mock_cursor.return_value.items.return_value = mock_tweets
            
            with patch.object(analyzer.analyzer, 'polarity_scores') as mock_scores:
                mock_scores.side_effect = [
                    {'compound': 0.5},
                    {'compound': 0.3},
                    {'compound': 0.7}
                ]
                
                result = analyzer.fetch_sentiment('AAPL')
                
                assert result == pytest.approx(0.5, rel=0.01)