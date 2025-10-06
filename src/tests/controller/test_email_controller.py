import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.controller.email_controller import EmailController


class TestEmailController:
    """Test suite for EmailController"""
    
    @pytest.fixture
    def controller(self):
        """Create a fresh EmailController instance for each test"""
        with patch('src.controller.email_controller.load_dotenv'):
            return EmailController()
    
    @pytest.fixture
    def mock_data_manager(self):
        """Create a mock DataManager"""
        with patch('src.controller.email_controller.DataManager') as mock:
            yield mock
    
    @pytest.fixture
    def mock_progress_tracker(self):
        """Create a mock ProgressTracker"""
        with patch('src.controller.email_controller.ProgressTracker') as mock:
            yield mock
    
    def test_init_loads_dotenv(self):
        """Test that initialization loads environment variables"""
        with patch('src.controller.email_controller.load_dotenv') as mock_load:
            controller = EmailController()
            mock_load.assert_called_once()
    
    def test_send_stock_emails_success(self, controller, mock_data_manager, mock_progress_tracker):
        """Test successful email sending for all tickers"""
        tickers = ["AAPL", "GOOGL", "MSFT"]
        user_email = "test@example.com"
        user_agent = "TestAgent/1.0"
        
        mock_manager_instance = Mock()
        mock_data_manager.return_value = mock_manager_instance
        mock_tracker_instance = Mock()
        mock_progress_tracker.return_value = mock_tracker_instance
        
        result = controller.send_stock_emails(tickers, user_email, user_agent)
        
        assert result["total"] == 3
        assert len(result["success"]) == 3
        assert len(result["failed"]) == 0
        assert result["user_email"] == user_email
        assert "timestamp" in result
        assert all(ticker in result["success"] for ticker in tickers)
        
        mock_data_manager.assert_called_once_with(user_agent)
        assert mock_manager_instance.process_ticker.call_count == 3
    
    def test_send_stock_emails_partial_failure(self, controller, mock_data_manager, mock_progress_tracker):
        """Test email sending with some ticker failures"""
        tickers = ["AAPL", "INVALID", "GOOGL"]
        user_email = "test@example.com"
        user_agent = "TestAgent/1.0"
        
        mock_manager_instance = Mock()
        mock_data_manager.return_value = mock_manager_instance
        mock_tracker_instance = Mock()
        mock_progress_tracker.return_value = mock_tracker_instance
        
        def side_effect(ticker, tracker):
            if ticker == "INVALID":
                raise ValueError("Invalid ticker symbol")
        
        mock_manager_instance.process_ticker.side_effect = side_effect
        
        result = controller.send_stock_emails(tickers, user_email, user_agent)
        
        assert result["total"] == 3
        assert len(result["success"]) == 2
        assert len(result["failed"]) == 1
        assert "AAPL" in result["success"]
        assert "GOOGL" in result["success"]
        assert result["failed"][0]["ticker"] == "INVALID"
        assert "Invalid ticker symbol" in result["failed"][0]["error"]
    
    def test_send_stock_emails_all_failures(self, controller, mock_data_manager, mock_progress_tracker):
        """Test email sending when all tickers fail"""
        tickers = ["BAD1", "BAD2"]
        user_email = "test@example.com"
        user_agent = "TestAgent/1.0"
        
        mock_manager_instance = Mock()
        mock_data_manager.return_value = mock_manager_instance
        mock_tracker_instance = Mock()
        mock_progress_tracker.return_value = mock_tracker_instance
        
        mock_manager_instance.process_ticker.side_effect = Exception("Network error")
        
        result = controller.send_stock_emails(tickers, user_email, user_agent)
        
        assert result["total"] == 2
        assert len(result["success"]) == 0
        assert len(result["failed"]) == 2
    
    def test_send_stock_emails_empty_list(self, controller, mock_data_manager):
        """Test email sending with empty ticker list"""
        result = controller.send_stock_emails([], "test@example.com", "Agent/1.0")
        
        assert result["total"] == 0
        assert len(result["success"]) == 0
        assert len(result["failed"]) == 0
        mock_data_manager.assert_called_once()
    
    def test_send_stock_emails_progress_tracking(self, controller, mock_data_manager, mock_progress_tracker):
        """Test that progress tracker is properly used"""
        tickers = ["AAPL"]
        mock_manager_instance = Mock()
        mock_data_manager.return_value = mock_manager_instance
        mock_tracker_instance = Mock()
        mock_progress_tracker.return_value = mock_tracker_instance
        
        controller.send_stock_emails(tickers, "test@example.com", "Agent/1.0")
        
        mock_tracker_instance.start.assert_called_once_with("AAPL")
        mock_tracker_instance.complete.assert_called_once_with("AAPL")
    
    @patch.dict('os.environ', {'USER_AGENT': 'CustomAgent/2.0'})
    def test_send_watchlist_emails_success(self, controller, mock_data_manager, mock_progress_tracker):
        """Test successful watchlist email sending"""
        watchlist = ["AAPL", "TSLA"]
        user_email = "test@example.com"
        
        mock_manager_instance = Mock()
        mock_data_manager.return_value = mock_manager_instance
        mock_tracker_instance = Mock()
        mock_progress_tracker.return_value = mock_tracker_instance
        
        result = controller.send_watchlist_emails(watchlist, user_email)
        
        assert result["total"] == 2
        assert len(result["success"]) == 2
        mock_data_manager.assert_called_once_with('CustomAgent/2.0')
    
    def test_send_watchlist_emails_empty(self, controller):
        """Test watchlist email sending with empty list"""
        result = controller.send_watchlist_emails([], "test@example.com")
        
        assert result["total"] == 0
        assert "error" in result
        assert result["error"] == "Watchlist is empty"
        assert len(result["success"]) == 0
        assert len(result["failed"]) == 0
    
    @patch.dict('os.environ', {'USER_AGENT': 'CustomAgent/2.0'})
    def test_send_custom_emails_success(self, controller, mock_data_manager, mock_progress_tracker):
        """Test successful custom email sending"""
        tickers = ["NFLX", "AMD"]
        user_email = "test@example.com"
        
        mock_manager_instance = Mock()
        mock_data_manager.return_value = mock_manager_instance
        mock_tracker_instance = Mock()
        mock_progress_tracker.return_value = mock_tracker_instance
        
        result = controller.send_custom_emails(tickers, user_email)
        
        assert result["total"] == 2
        assert len(result["success"]) == 2
        mock_data_manager.assert_called_once_with('CustomAgent/2.0')
    
    def test_send_custom_emails_empty(self, controller):
        """Test custom email sending with empty list"""
        result = controller.send_custom_emails([], "test@example.com")
        
        assert result["total"] == 0
        assert "error" in result
        assert result["error"] == "No tickers provided"
        assert len(result["success"]) == 0
        assert len(result["failed"]) == 0
    
    @patch.dict('os.environ', {}, clear=True)
    def test_default_user_agent_when_env_missing(self, controller, mock_data_manager, mock_progress_tracker):
        """Test that default user agent is used when env var is missing"""
        mock_manager_instance = Mock()
        mock_data_manager.return_value = mock_manager_instance
        mock_tracker_instance = Mock()
        mock_progress_tracker.return_value = mock_tracker_instance
        
        controller.send_watchlist_emails(["AAPL"], "test@example.com")
        
        mock_data_manager.assert_called_once_with('StockDashboard/1.0')
    
    def test_timestamp_format(self, controller, mock_data_manager, mock_progress_tracker):
        """Test that timestamp is in ISO format"""
        mock_manager_instance = Mock()
        mock_data_manager.return_value = mock_manager_instance
        mock_tracker_instance = Mock()
        mock_progress_tracker.return_value = mock_tracker_instance
        
        result = controller.send_stock_emails(["AAPL"], "test@example.com", "Agent/1.0")
        
        timestamp = datetime.fromisoformat(result["timestamp"])
        assert isinstance(timestamp, datetime)
    
    def test_logging_calls(self, controller, mock_data_manager, mock_progress_tracker):
        """Test that appropriate logging occurs"""
        mock_manager_instance = Mock()
        mock_data_manager.return_value = mock_manager_instance
        mock_tracker_instance = Mock()
        mock_progress_tracker.return_value = mock_tracker_instance
        
        with patch.object(controller.logger, 'info') as mock_info:
            with patch.object(controller.logger, 'error') as mock_error:
                controller.send_stock_emails(["AAPL"], "test@example.com", "Agent/1.0")
                
                assert mock_info.call_count >= 3