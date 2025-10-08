import pytest
import requests
from unittest.mock import Mock, patch
from requests.exceptions import HTTPError, Timeout, ConnectionError, RequestException
from src.model.utils.http_client import HttpClient


class TestHttpClient:
    
    @pytest.fixture
    def client(self):
        with patch('src.model.utils.http_client.LoggerSetup'):
            return HttpClient("TestAgent/1.0", timeout=10)
    
    def test_init(self):
        with patch('src.model.utils.http_client.LoggerSetup'):
            client = HttpClient("TestAgent/1.0", timeout=15)
            assert client.headers == {"User-Agent": "TestAgent/1.0"}
            assert client.timeout == 15
    
    def test_init_default_timeout(self):
        with patch('src.model.utils.http_client.LoggerSetup'):
            client = HttpClient("TestAgent/1.0")
            assert client.timeout == 10
    
    @patch('src.model.utils.http_client.requests.get')
    def test_get_success(self, mock_get, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        response = client.get("http://example.com")
        
        assert response == mock_response
        mock_get.assert_called_once_with(
            "http://example.com",
            headers={"User-Agent": "TestAgent/1.0"},
            timeout=10
        )
    
    @patch('src.model.utils.http_client.requests.get')
    def test_get_http_error(self, mock_get, client):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.side_effect = HTTPError(response=mock_response)
        
        response = client.get("http://example.com")
        
        assert response is None
    
    @patch('src.model.utils.http_client.requests.get')
    def test_get_connection_error(self, mock_get, client):
        mock_get.side_effect = ConnectionError("Connection refused")
        
        response = client.get("http://example.com")
        
        assert response is None
    
    @patch('src.model.utils.http_client.requests.get')
    def test_get_timeout(self, mock_get, client):
        mock_get.side_effect = Timeout("Request timed out")
        
        response = client.get("http://example.com")
        
        assert response is None
    
    @patch('src.model.utils.http_client.requests.get')
    def test_get_request_exception(self, mock_get, client):
        mock_get.side_effect = RequestException("Generic request error")
        
        response = client.get("http://example.com")
        
        assert response is None
    
    @patch('src.model.utils.http_client.requests.get')
    def test_get_uses_headers(self, mock_get, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client.get("http://example.com")
        
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['headers'] == {"User-Agent": "TestAgent/1.0"}
    
    @patch('src.model.utils.http_client.requests.get')
    def test_get_uses_timeout(self, mock_get, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client.get("http://example.com")
        
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['timeout'] == 10
    
    @patch('src.model.utils.http_client.requests.get')
    def test_get_calls_raise_for_status(self, mock_get, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client.get("http://example.com")
        
        mock_response.raise_for_status.assert_called_once()
    
    @patch('src.model.utils.http_client.requests.get')
    def test_get_http_error_no_response(self, mock_get, client):
        http_error = HTTPError()
        http_error.response = None
        mock_get.side_effect = http_error
        
        response = client.get("http://example.com")
        
        assert response is None
    
    @patch('src.model.utils.http_client.requests.get')
    def test_get_different_status_codes(self, mock_get, client):
        for status_code in [200, 201, 204, 301, 302]:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_get.return_value = mock_response
            
            response = client.get("http://example.com")
            
            assert response == mock_response
    
    @patch('src.model.utils.http_client.requests.get')
    def test_get_multiple_urls(self, mock_get, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        urls = ["http://example1.com", "http://example2.com", "http://example3.com"]
        
        for url in urls:
            response = client.get(url)
            assert response == mock_response
        
        assert mock_get.call_count == 3
    
    def test_custom_timeout(self):
        with patch('src.model.utils.http_client.LoggerSetup'):
            client = HttpClient("TestAgent/1.0", timeout=30)
            assert client.timeout == 30
    
    def test_custom_user_agent(self):
        with patch('src.model.utils.http_client.LoggerSetup'):
            client = HttpClient("CustomAgent/2.0")
            assert client.headers == {"User-Agent": "CustomAgent/2.0"}