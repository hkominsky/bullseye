import pytest
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from src.model.data_pipeline.ticker_news import TickerNews


class TestTickerNews:
    
    @pytest.fixture
    def mock_env(self):
        with patch.dict('os.environ', {'FINNHUB_API_KEY': 'test_api_key'}):
            yield
    
    @pytest.fixture
    def ticker_news(self, mock_env):
        with patch('src.model.data_pipeline.ticker_news.load_dotenv'):
            with patch('src.model.data_pipeline.ticker_news.LoggerSetup'):
                return TickerNews()
    
    @pytest.fixture
    def sample_api_response(self):
        return [
            {
                'headline': 'Company announces strong Q4 results',
                'summary': 'The company reported better than expected earnings for Q4 2024.',
                'url': 'https://example.com/article1',
                'datetime': 1704067200
            },
            {
                'headline': 'New product launch scheduled',
                'summary': 'The company will launch a revolutionary new product next month.',
                'url': 'https://example.com/article2',
                'datetime': 1703980800
            }
        ]
    
    def test_init_success(self, mock_env):
        with patch('src.model.data_pipeline.ticker_news.load_dotenv'):
            with patch('src.model.data_pipeline.ticker_news.LoggerSetup'):
                tn = TickerNews()
                assert tn.api_key == 'test_api_key'
                assert tn.base_url == "https://finnhub.io/api/v1"
    
    def test_init_missing_api_key(self):
        with patch.dict('os.environ', {}, clear=True):
            with patch('src.model.data_pipeline.ticker_news.load_dotenv'):
                with patch('src.model.data_pipeline.ticker_news.LoggerSetup'):
                    with pytest.raises(ValueError, match="FINNHUB_API_KEY not found"):
                        TickerNews()
    
    @patch('src.model.data_pipeline.ticker_news.requests.get')
    def test_get_ticker_news_success(self, mock_get, ticker_news, sample_api_response):
        mock_response = Mock()
        mock_response.json.return_value = sample_api_response
        mock_get.return_value = mock_response
        
        result = ticker_news.get_ticker_news('AAPL')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'headline' in result.columns
        assert 'summary' in result.columns
        assert 'url' in result.columns
        assert 'published_at' in result.columns
    
    @patch('src.model.data_pipeline.ticker_news.requests.get')
    def test_get_ticker_news_empty_response(self, mock_get, ticker_news):
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        result = ticker_news.get_ticker_news('AAPL')
        
        assert result.empty
    
    @patch('src.model.data_pipeline.ticker_news.requests.get')
    def test_get_ticker_news_network_error(self, mock_get, ticker_news):
        mock_get.side_effect = Exception("Network error")
        
        result = ticker_news.get_ticker_news('AAPL')
        
        assert result.empty
    
    @patch('src.model.data_pipeline.ticker_news.requests.get')
    def test_get_ticker_news_http_error(self, mock_get, ticker_news):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response
        
        result = ticker_news.get_ticker_news('AAPL')
        
        assert result.empty
    
    @patch('src.model.data_pipeline.ticker_news.requests.get')
    def test_fetch_api_data_params(self, mock_get, ticker_news):
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        ticker_news._fetch_api_data('AAPL')
        
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://finnhub.io/api/v1/company-news"
        assert call_args[1]['params']['symbol'] == 'AAPL'
        assert call_args[1]['params']['token'] == 'test_api_key'
        assert 'from' in call_args[1]['params']
        assert 'to' in call_args[1]['params']
    
    @patch('src.model.data_pipeline.ticker_news.requests.get')
    def test_fetch_api_data_uppercase_ticker(self, mock_get, ticker_news):
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        ticker_news._fetch_api_data('aapl')
        
        call_args = mock_get.call_args
        assert call_args[1]['params']['symbol'] == 'AAPL'
    
    @patch('src.model.data_pipeline.ticker_news.requests.get')
    def test_fetch_api_data_date_range(self, mock_get, ticker_news):
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        ticker_news._fetch_api_data('AAPL')
        
        call_args = mock_get.call_args
        from_date = datetime.strptime(call_args[1]['params']['from'], '%Y-%m-%d')
        to_date = datetime.strptime(call_args[1]['params']['to'], '%Y-%m-%d')
        
        assert (datetime.now() - from_date).days >= 29
        assert (datetime.now() - to_date).days <= 1
    
    def test_is_valid_article_valid(self, ticker_news):
        article = {
            'headline': 'Valid headline',
            'summary': 'This is a valid summary with more than 20 characters.'
        }
        
        assert ticker_news._is_valid_article(article) == True
    
    def test_is_valid_article_no_headline(self, ticker_news):
        article = {
            'headline': '',
            'summary': 'This is a valid summary with more than 20 characters.'
        }
        
        assert ticker_news._is_valid_article(article) == False
    
    def test_is_valid_article_short_summary(self, ticker_news):
        article = {
            'headline': 'Valid headline',
            'summary': 'Short summary'
        }
        
        assert ticker_news._is_valid_article(article) == False
    
    def test_is_valid_article_whitespace_headline(self, ticker_news):
        article = {
            'headline': '   ',
            'summary': 'This is a valid summary with more than 20 characters.'
        }
        
        assert ticker_news._is_valid_article(article) == False
    
    def test_is_valid_article_exactly_20_chars_summary(self, ticker_news):
        article = {
            'headline': 'Valid headline',
            'summary': '12345678901234567890'
        }
        
        assert ticker_news._is_valid_article(article) == False
    
    def test_is_valid_article_21_chars_summary(self, ticker_news):
        article = {
            'headline': 'Valid headline',
            'summary': '123456789012345678901'
        }
        
        assert ticker_news._is_valid_article(article) == True
    
    def test_format_article(self, ticker_news):
        article = {
            'headline': 'Test Headline',
            'summary': 'Test summary with enough characters.',
            'url': 'https://example.com',
            'datetime': 1704067200
        }
        
        result = ticker_news._format_article(article)
        
        assert result['headline'] == 'Test Headline'
        assert result['summary'] == 'Test summary with enough characters.'
        assert result['url'] == 'https://example.com'
        assert isinstance(result['published_at'], pd.Timestamp)
    
    def test_format_article_strips_whitespace(self, ticker_news):
        article = {
            'headline': '  Test Headline  ',
            'summary': '  Test summary  ',
            'url': '  https://example.com  ',
            'datetime': 1704067200
        }
        
        result = ticker_news._format_article(article)
        
        assert result['headline'] == 'Test Headline'
        assert result['summary'] == 'Test summary'
        assert result['url'] == 'https://example.com'
    
    def test_format_article_missing_fields(self, ticker_news):
        article = {'datetime': 1704067200}
        
        result = ticker_news._format_article(article)
        
        assert result['headline'] == ''
        assert result['summary'] == ''
        assert result['url'] == ''
    
    def test_process_news_articles_sorts_by_date(self, ticker_news):
        data = [
            {
                'headline': 'Older article',
                'summary': 'Summary for the older article here.',
                'url': 'https://example.com/old',
                'datetime': 1703980800
            },
            {
                'headline': 'Newer article',
                'summary': 'Summary for the newer article here.',
                'url': 'https://example.com/new',
                'datetime': 1704067200
            }
        ]
        
        result = ticker_news._process_news_articles(data)
        
        assert result[0]['headline'] == 'Newer article'
        assert result[1]['headline'] == 'Older article'
    
    def test_process_news_articles_limits_to_5(self, ticker_news):
        data = [
            {
                'headline': f'Article {i}',
                'summary': f'Summary for article {i} with enough characters.',
                'url': f'https://example.com/{i}',
                'datetime': 1704067200 - i * 86400
            }
            for i in range(10)
        ]
        
        result = ticker_news._process_news_articles(data)
        
        assert len(result) == 5
    
    def test_process_news_articles_filters_invalid(self, ticker_news):
        data = [
            {
                'headline': 'Valid article',
                'summary': 'Valid summary with enough characters.',
                'url': 'https://example.com/valid',
                'datetime': 1704067200
            },
            {
                'headline': '',
                'summary': 'No headline here with enough characters.',
                'url': 'https://example.com/invalid',
                'datetime': 1703980800
            },
            {
                'headline': 'Another valid',
                'summary': 'Short'
            }
        ]
        
        result = ticker_news._process_news_articles(data)
        
        assert len(result) == 1
        assert result[0]['headline'] == 'Valid article'
    
    def test_process_news_articles_empty_list(self, ticker_news):
        result = ticker_news._process_news_articles([])
        
        assert result == []
    
    @patch('src.model.data_pipeline.ticker_news.requests.get')
    def test_get_ticker_news_more_than_5_articles(self, mock_get, ticker_news):
        articles = [
            {
                'headline': f'Article {i}',
                'summary': f'Summary for article {i} with enough characters.',
                'url': f'https://example.com/{i}',
                'datetime': 1704067200 - i * 86400
            }
            for i in range(10)
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = articles
        mock_get.return_value = mock_response
        
        result = ticker_news.get_ticker_news('AAPL')
        
        assert len(result) == 5
    
    @patch('src.model.data_pipeline.ticker_news.requests.get')
    def test_get_ticker_news_dataframe_columns(self, mock_get, ticker_news, sample_api_response):
        mock_response = Mock()
        mock_response.json.return_value = sample_api_response
        mock_get.return_value = mock_response
        
        result = ticker_news.get_ticker_news('AAPL')
        
        expected_columns = {'headline', 'summary', 'url', 'published_at'}
        assert set(result.columns) == expected_columns
    
    @patch('src.model.data_pipeline.ticker_news.requests.get')
    def test_get_ticker_news_published_at_type(self, mock_get, ticker_news, sample_api_response):
        mock_response = Mock()
        mock_response.json.return_value = sample_api_response
        mock_get.return_value = mock_response
        
        result = ticker_news.get_ticker_news('AAPL')
        
        assert pd.api.types.is_datetime64_any_dtype(result['published_at'])
    
    @patch('src.model.data_pipeline.ticker_news.requests.get')
    def test_get_ticker_news_descending_order(self, mock_get, ticker_news):
        articles = [
            {
                'headline': f'Article {i}',
                'summary': f'Summary for article {i} with enough characters.',
                'url': f'https://example.com/{i}',
                'datetime': 1704067200 - i * 86400
            }
            for i in range(3)
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = articles
        mock_get.return_value = mock_response
        
        result = ticker_news.get_ticker_news('AAPL')
        
        assert result['published_at'].is_monotonic_decreasing