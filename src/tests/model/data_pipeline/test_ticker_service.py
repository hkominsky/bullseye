import pytest
from unittest.mock import Mock, patch
from src.model.data_pipeline.data_aggregator.sec_data_filings.ticker_retriever.ticker_mapping_service import TickerMappingService


class TestTickerMappingService:
    
    @pytest.fixture
    def mock_http_client(self):
        return Mock()
    
    @pytest.fixture
    def mock_cache(self):
        cache = Mock()
        cache.is_expired.return_value = False
        cache.read.return_value = {
            "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
            "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
            "2": {"cik_str": 1652044, "ticker": "GOOGL", "title": "Alphabet Inc."}
        }
        return cache
    
    @pytest.fixture
    def service(self, mock_http_client, mock_cache):
        with patch('src.model.data_pipeline.data_aggregator.sec_data_filings.ticker_retriever.ticker_mapping_service.LoggerSetup'):
            return TickerMappingService(mock_http_client, mock_cache)
    
    def test_init(self, mock_http_client, mock_cache):
        with patch('src.model.data_pipeline.data_aggregator.sec_data_filings.ticker_retriever.ticker_mapping_service.LoggerSetup'):
            service = TickerMappingService(mock_http_client, mock_cache)
            assert service.http_client == mock_http_client
            assert service.cache == mock_cache
    
    def test_get_ticker_to_cik_mapping_cache_valid(self, service, mock_cache):
        mock_cache.is_expired.return_value = False
        
        mapping = service.get_ticker_to_cik_mapping()
        
        assert 'AAPL' in mapping
        assert 'MSFT' in mapping
        assert 'GOOGL' in mapping
        assert mapping['AAPL'] == '0000320193'
        assert mapping['MSFT'] == '0000789019'
        assert mapping['GOOGL'] == '0001652044'
        mock_cache.read.assert_called_once()
    
    def test_get_ticker_to_cik_mapping_cache_expired(self, service, mock_cache, mock_http_client):
        mock_cache.is_expired.return_value = True
        mock_response = Mock()
        mock_response.text = '{"0": {"cik_str": 320193, "ticker": "AAPL"}}'
        mock_http_client.get.return_value = mock_response
        
        mapping = service.get_ticker_to_cik_mapping()
        
        mock_http_client.get.assert_called_once_with(service.SEC_TICKER_URL)
        mock_cache.write.assert_called_once()
        assert 'AAPL' in mapping
    
    def test_get_ticker_to_cik_mapping_custom_cache_file(self, service, mock_cache):
        mock_cache.is_expired.return_value = False
        custom_file = "custom_cache.json"
        
        mapping = service.get_ticker_to_cik_mapping(cache_file=custom_file)
        
        mock_cache.is_expired.assert_called_with(custom_file, service.DEFAULT_REFRESH_DAYS)
        mock_cache.read.assert_called_with(custom_file)
    
    def test_get_ticker_to_cik_mapping_custom_refresh_days(self, service, mock_cache):
        mock_cache.is_expired.return_value = False
        custom_days = 60
        
        mapping = service.get_ticker_to_cik_mapping(refresh_days=custom_days)
        
        mock_cache.is_expired.assert_called_with(service.DEFAULT_CACHE_FILE, custom_days)
    
    def test_refresh_cache_success(self, service, mock_http_client, mock_cache):
        mock_response = Mock()
        mock_response.text = '{"0": {"cik_str": 320193, "ticker": "AAPL"}}'
        mock_http_client.get.return_value = mock_response
        cache_file = "test_cache.json"
        
        service._refresh_cache(cache_file)
        
        mock_http_client.get.assert_called_once_with(service.SEC_TICKER_URL)
        mock_cache.write.assert_called_once_with(cache_file, mock_response.text)
    
    def test_refresh_cache_http_error(self, service, mock_http_client, mock_cache):
        mock_http_client.get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception, match="Network error"):
            service._refresh_cache("test_cache.json")
    
    def test_build_ticker_mapping_success(self, service):
        ticker_data = {
            "0": {"cik_str": 320193, "ticker": "aapl", "title": "Apple Inc."},
            "1": {"cik_str": 789019, "ticker": "msft", "title": "Microsoft Corp"},
            "2": {"cik_str": 1652044, "ticker": "googl", "title": "Alphabet Inc."}
        }
        
        mapping = service._build_ticker_mapping(ticker_data)
        
        assert mapping['AAPL'] == '0000320193'
        assert mapping['MSFT'] == '0000789019'
        assert mapping['GOOGL'] == '0001652044'
    
    def test_build_ticker_mapping_uppercase_tickers(self, service):
        ticker_data = {
            "0": {"cik_str": 320193, "ticker": "aapl"},
            "1": {"cik_str": 789019, "ticker": "MsFt"}
        }
        
        mapping = service._build_ticker_mapping(ticker_data)
        
        assert 'AAPL' in mapping
        assert 'MSFT' in mapping
        assert 'aapl' not in mapping
        assert 'MsFt' not in mapping
    
    def test_build_ticker_mapping_zero_padded_cik(self, service):
        ticker_data = {
            "0": {"cik_str": 1234, "ticker": "TEST"}
        }
        
        mapping = service._build_ticker_mapping(ticker_data)
        
        assert mapping['TEST'] == '0000001234'
        assert len(mapping['TEST']) == 10
    
    def test_build_ticker_mapping_already_padded_cik(self, service):
        ticker_data = {
            "0": {"cik_str": 1234567890, "ticker": "TEST"}
        }
        
        mapping = service._build_ticker_mapping(ticker_data)
        
        assert mapping['TEST'] == '1234567890'
        assert len(mapping['TEST']) == 10
    
    def test_build_ticker_mapping_empty_data(self, service):
        ticker_data = {}
        
        mapping = service._build_ticker_mapping(ticker_data)
        
        assert mapping == {}
    
    def test_build_ticker_mapping_missing_fields(self, service):
        ticker_data = {
            "0": {"cik_str": 320193}
        }
        
        with pytest.raises(Exception):
            service._build_ticker_mapping(ticker_data)
    
    def test_build_ticker_mapping_invalid_structure(self, service):
        ticker_data = {
            "0": "invalid_structure"
        }
        
        with pytest.raises(Exception):
            service._build_ticker_mapping(ticker_data)
    
    def test_default_cache_file_constant(self, service):
        assert service.DEFAULT_CACHE_FILE is not None
        assert isinstance(service.DEFAULT_CACHE_FILE, str)
    
    def test_default_refresh_days_constant(self, service):
        assert service.DEFAULT_REFRESH_DAYS == 30
    
    def test_sec_ticker_url_constant(self, service):
        assert service.SEC_TICKER_URL == "https://www.sec.gov/files/company_tickers.json"
    
    def test_get_ticker_to_cik_mapping_integration(self, service, mock_cache, mock_http_client):
        mock_cache.is_expired.return_value = True
        mock_response = Mock()
        mock_response.text = '{"0": {"cik_str": 320193, "ticker": "AAPL"}}'
        mock_http_client.get.return_value = mock_response
        mock_cache.read.return_value = {"0": {"cik_str": 320193, "ticker": "AAPL"}}
        
        mapping = service.get_ticker_to_cik_mapping()
        
        assert 'AAPL' in mapping
        assert mapping['AAPL'] == '0000320193'
        mock_cache.is_expired.assert_called_once()
        mock_http_client.get.assert_called_once()
        mock_cache.write.assert_called_once()
        mock_cache.read.assert_called_once()
    
    def test_multiple_tickers_same_company(self, service):
        ticker_data = {
            "0": {"cik_str": 320193, "ticker": "AAPL"},
            "1": {"cik_str": 320193, "ticker": "APPL"}
        }
        
        mapping = service._build_ticker_mapping(ticker_data)
        
        assert mapping['AAPL'] == '0000320193'
        assert mapping['APPL'] == '0000320193'
        assert len(mapping) == 2
    
    def test_refresh_cache_with_default_file(self, service, mock_http_client, mock_cache):
        mock_response = Mock()
        mock_response.text = '{"0": {"cik_str": 320193, "ticker": "AAPL"}}'
        mock_http_client.get.return_value = mock_response
        
        service._refresh_cache(service.DEFAULT_CACHE_FILE)
        
        mock_cache.write.assert_called_once_with(service.DEFAULT_CACHE_FILE, mock_response.text)