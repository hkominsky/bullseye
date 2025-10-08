import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from src.model.data_pipeline.corporate_sentiment_analyzer import CorporateSentimentAnalyzer


class TestCorporateSentimentAnalyzer:
    
    @pytest.fixture
    def mock_env(self):
        with patch.dict('os.environ', {
            'ALPHA_VANTAGE_API_KEY': 'test_api_key',
            'NEWS_SENTIMENT_LIMIT': '50'
        }):
            yield
    
    @pytest.fixture
    def analyzer(self, mock_env):
        with patch('src.model.data_pipeline.corporate_sentiment_analyzer.load_dotenv'):
            with patch('src.model.data_pipeline.corporate_sentiment_analyzer.LoggerSetup'):
                return CorporateSentimentAnalyzer()
    
    def test_init_success(self, mock_env):
        with patch('src.model.data_pipeline.corporate_sentiment_analyzer.load_dotenv'):
            with patch('src.model.data_pipeline.corporate_sentiment_analyzer.LoggerSetup'):
                analyzer = CorporateSentimentAnalyzer()
                assert analyzer.api_key == 'test_api_key'
                assert analyzer.limit == 50
    
    def test_init_missing_api_key(self):
        with patch.dict('os.environ', {}, clear=True):
            with patch('src.model.data_pipeline.corporate_sentiment_analyzer.load_dotenv'):
                with patch('src.model.data_pipeline.corporate_sentiment_analyzer.LoggerSetup'):
                    with pytest.raises(ValueError, match="Alpha Vantage API key not set"):
                        CorporateSentimentAnalyzer()
    
    def test_init_default_limit(self):
        with patch.dict('os.environ', {'ALPHA_VANTAGE_API_KEY': 'test_key'}):
            with patch('src.model.data_pipeline.corporate_sentiment_analyzer.load_dotenv'):
                with patch('src.model.data_pipeline.corporate_sentiment_analyzer.LoggerSetup'):
                    analyzer = CorporateSentimentAnalyzer()
                    assert analyzer.limit == 50
    
    def test_init_custom_limit(self):
        with patch.dict('os.environ', {
            'ALPHA_VANTAGE_API_KEY': 'test_key',
            'NEWS_SENTIMENT_LIMIT': '100'
        }):
            with patch('src.model.data_pipeline.corporate_sentiment_analyzer.load_dotenv'):
                with patch('src.model.data_pipeline.corporate_sentiment_analyzer.LoggerSetup'):
                    analyzer = CorporateSentimentAnalyzer()
                    assert analyzer.limit == 100
    
    def test_init_invalid_limit(self):
        with patch.dict('os.environ', {
            'ALPHA_VANTAGE_API_KEY': 'test_key',
            'NEWS_SENTIMENT_LIMIT': 'invalid'
        }):
            with patch('src.model.data_pipeline.corporate_sentiment_analyzer.load_dotenv'):
                with patch('src.model.data_pipeline.corporate_sentiment_analyzer.LoggerSetup'):
                    with pytest.raises(ValueError, match="NEWS_SENTIMENT_LIMIT must be an integer"):
                        CorporateSentimentAnalyzer()
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_success(self, mock_get, analyzer):
        mock_response = Mock()
        mock_response.json.return_value = {
            "feed": [
                {
                    "title": "Article 1",
                    "time_published": "20240101T120000",
                    "overall_sentiment_score": 0.5
                },
                {
                    "title": "Article 2",
                    "time_published": "20240101T130000",
                    "overall_sentiment_score": 0.3
                },
                {
                    "title": "Article 3",
                    "time_published": "20240101T140000",
                    "overall_sentiment_score": 0.7
                }
            ]
        }
        mock_get.return_value = mock_response
        
        sentiment = analyzer.fetch_sentiment('AAPL')
        
        assert sentiment == pytest.approx(0.5, rel=0.01)
        mock_get.assert_called_once()
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_empty_feed(self, mock_get, analyzer):
        mock_response = Mock()
        mock_response.json.return_value = {"feed": []}
        mock_get.return_value = mock_response
        
        sentiment = analyzer.fetch_sentiment('AAPL')
        
        assert sentiment == 0.0
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_no_feed_key(self, mock_get, analyzer):
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        
        sentiment = analyzer.fetch_sentiment('AAPL')
        
        assert sentiment == 0.0
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_api_error(self, mock_get, analyzer):
        mock_get.side_effect = requests.RequestException("API Error")
        
        sentiment = analyzer.fetch_sentiment('AAPL')
        
        assert sentiment == 0.0
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_http_error(self, mock_get, analyzer):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        sentiment = analyzer.fetch_sentiment('AAPL')
        
        assert sentiment == 0.0
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_json_error(self, mock_get, analyzer):
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        sentiment = analyzer.fetch_sentiment('AAPL')
        
        assert sentiment == 0.0
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_positive_score(self, mock_get, analyzer):
        mock_response = Mock()
        mock_response.json.return_value = {
            "feed": [
                {"title": "Good News", "time_published": "20240101T120000", "overall_sentiment_score": 0.8},
                {"title": "Great News", "time_published": "20240101T130000", "overall_sentiment_score": 0.9}
            ]
        }
        mock_get.return_value = mock_response
        
        sentiment = analyzer.fetch_sentiment('AAPL')
        
        assert sentiment == pytest.approx(0.85, rel=0.01)
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_negative_score(self, mock_get, analyzer):
        mock_response = Mock()
        mock_response.json.return_value = {
            "feed": [
                {"title": "Bad News", "time_published": "20240101T120000", "overall_sentiment_score": -0.6},
                {"title": "Worse News", "time_published": "20240101T130000", "overall_sentiment_score": -0.4}
            ]
        }
        mock_get.return_value = mock_response
        
        sentiment = analyzer.fetch_sentiment('AAPL')
        
        assert sentiment == pytest.approx(-0.5, rel=0.01)
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_mixed_scores(self, mock_get, analyzer):
        mock_response = Mock()
        mock_response.json.return_value = {
            "feed": [
                {"title": "Article 1", "time_published": "20240101T120000", "overall_sentiment_score": 0.5},
                {"title": "Article 2", "time_published": "20240101T130000", "overall_sentiment_score": -0.3},
                {"title": "Article 3", "time_published": "20240101T140000", "overall_sentiment_score": 0.1}
            ]
        }
        mock_get.return_value = mock_response
        
        sentiment = analyzer.fetch_sentiment('AAPL')
        
        assert sentiment == pytest.approx(0.1, rel=0.01)
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_respects_limit(self, mock_get):
        with patch.dict('os.environ', {
            'ALPHA_VANTAGE_API_KEY': 'test_key',
            'NEWS_SENTIMENT_LIMIT': '2'
        }):
            with patch('src.model.data_pipeline.corporate_sentiment_analyzer.load_dotenv'):
                with patch('src.model.data_pipeline.corporate_sentiment_analyzer.LoggerSetup'):
                    analyzer = CorporateSentimentAnalyzer()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "feed": [
                {"title": "Article 1", "time_published": "20240101T120000", "overall_sentiment_score": 0.5},
                {"title": "Article 2", "time_published": "20240101T130000", "overall_sentiment_score": 0.3},
                {"title": "Article 3", "time_published": "20240101T140000", "overall_sentiment_score": 0.9}
            ]
        }
        mock_get.return_value = mock_response
        
        sentiment = analyzer.fetch_sentiment('AAPL')
        
        assert sentiment == pytest.approx(0.4, rel=0.01)
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_api_params(self, mock_get, analyzer):
        mock_response = Mock()
        mock_response.json.return_value = {"feed": []}
        mock_get.return_value = mock_response
        
        analyzer.fetch_sentiment('MSFT')
        
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://www.alphavantage.co/query"
        assert call_args[1]['params']['function'] == "NEWS_SENTIMENT"
        assert call_args[1]['params']['tickers'] == "MSFT"
        assert call_args[1]['params']['apikey'] == 'test_api_key'
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_single_article(self, mock_get, analyzer):
        mock_response = Mock()
        mock_response.json.return_value = {
            "feed": [
                {"title": "Only Article", "time_published": "20240101T120000", "overall_sentiment_score": 0.6}
            ]
        }
        mock_get.return_value = mock_response
        
        sentiment = analyzer.fetch_sentiment('AAPL')
        
        assert sentiment == pytest.approx(0.6, rel=0.01)
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_zero_scores(self, mock_get, analyzer):
        mock_response = Mock()
        mock_response.json.return_value = {
            "feed": [
                {"title": "Neutral 1", "time_published": "20240101T120000", "overall_sentiment_score": 0.0},
                {"title": "Neutral 2", "time_published": "20240101T130000", "overall_sentiment_score": 0.0}
            ]
        }
        mock_get.return_value = mock_response
        
        sentiment = analyzer.fetch_sentiment('AAPL')
        
        assert sentiment == 0.0
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_string_scores(self, mock_get, analyzer):
        mock_response = Mock()
        mock_response.json.return_value = {
            "feed": [
                {"title": "Article 1", "time_published": "20240101T120000", "overall_sentiment_score": "0.5"},
                {"title": "Article 2", "time_published": "20240101T130000", "overall_sentiment_score": "0.3"}
            ]
        }
        mock_get.return_value = mock_response
        
        sentiment = analyzer.fetch_sentiment('AAPL')
        
        assert sentiment == pytest.approx(0.4, rel=0.01)
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_general_exception(self, mock_get, analyzer):
        mock_get.side_effect = Exception("Unexpected error")
        
        sentiment = analyzer.fetch_sentiment('AAPL')
        
        assert sentiment == 0.0
    
    @patch('src.model.data_pipeline.corporate_sentiment_analyzer.requests.get')
    def test_fetch_sentiment_dataframe_creation(self, mock_get, analyzer):
        mock_response = Mock()
        mock_response.json.return_value = {
            "feed": [
                {"title": "Test Article", "time_published": "20240101T120000", "overall_sentiment_score": 0.5}
            ]
        }
        mock_get.return_value = mock_response
        
        with patch('src.model.data_pipeline.corporate_sentiment_analyzer.pd.DataFrame') as mock_df:
            mock_df_instance = Mock()
            mock_df_instance.empty = False
            mock_df_instance.__getitem__.return_value.astype.return_value.mean.return_value = 0.5
            mock_df.return_value = mock_df_instance
            
            sentiment = analyzer.fetch_sentiment('AAPL')
            
            mock_df.assert_called_once()