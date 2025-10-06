import pytest
import sys
from unittest.mock import Mock, patch, call
from src.controller.manual_email import manual_email


class TestManualEmail:
    """Test suite for manual_email function"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies"""
        with patch('src.controller.manual_email.load_dotenv') as mock_load_dotenv, \
             patch('src.controller.manual_email.LoggerSetup') as mock_logger_setup, \
             patch('src.controller.manual_email.EnvValidation') as mock_env_validation, \
             patch('src.controller.manual_email.DataManager') as mock_data_manager, \
             patch('src.controller.manual_email.ProgressTracker') as mock_progress_tracker:
            
            mock_logger = Mock()
            mock_logger_setup.setup_logger.return_value = mock_logger
            
            yield {
                'load_dotenv': mock_load_dotenv,
                'logger_setup': mock_logger_setup,
                'logger': mock_logger,
                'env_validation': mock_env_validation,
                'data_manager': mock_data_manager,
                'progress_tracker': mock_progress_tracker
            }
    
    def test_manual_email_success_single_ticker(self, mock_dependencies):
        """Test successful processing of a single ticker"""
        mock_dependencies['env_validation'].validate_env_vars.return_value = {
            'USER_EMAIL': 'test@example.com',
            'TICKERS': 'AAPL',
            'USER_AGENT': 'TestAgent/1.0'
        }
        mock_dependencies['env_validation'].parse_tickers.return_value = ['AAPL']
        
        mock_manager_instance = Mock()
        mock_dependencies['data_manager'].return_value = mock_manager_instance
        
        mock_tracker_instance = Mock()
        mock_dependencies['progress_tracker'].return_value = mock_tracker_instance
        
        result = manual_email()
        
        assert isinstance(result, dict)
        mock_dependencies['load_dotenv'].assert_called_once()
        mock_dependencies['env_validation'].validate_env_vars.assert_called_once_with(
            ["USER_EMAIL", "TICKERS", "USER_AGENT"]
        )
        mock_dependencies['env_validation'].parse_tickers.assert_called_once_with('AAPL')
        mock_dependencies['data_manager'].assert_called_once_with('TestAgent/1.0')
        mock_manager_instance.process_ticker.assert_called_once_with('AAPL', mock_tracker_instance)
        mock_tracker_instance.start.assert_called_once_with('AAPL')
        mock_tracker_instance.complete.assert_called_once_with('AAPL')
    
    def test_manual_email_success_multiple_tickers(self, mock_dependencies):
        """Test successful processing of multiple tickers"""
        mock_dependencies['env_validation'].validate_env_vars.return_value = {
            'USER_EMAIL': 'test@example.com',
            'TICKERS': 'AAPL,GOOGL,MSFT',
            'USER_AGENT': 'TestAgent/1.0'
        }
        mock_dependencies['env_validation'].parse_tickers.return_value = ['AAPL', 'GOOGL', 'MSFT']
        
        mock_manager_instance = Mock()
        mock_dependencies['data_manager'].return_value = mock_manager_instance
        
        mock_tracker_instance = Mock()
        mock_dependencies['progress_tracker'].return_value = mock_tracker_instance
        
        result = manual_email()
        
        assert isinstance(result, dict)
        assert mock_manager_instance.process_ticker.call_count == 3
        assert mock_dependencies['progress_tracker'].call_count == 3
        
        expected_calls = [call('AAPL'), call('GOOGL'), call('MSFT')]
        mock_tracker_instance.start.assert_has_calls(expected_calls)
        mock_tracker_instance.complete.assert_has_calls(expected_calls)
    
    def test_manual_email_env_validation_error(self, mock_dependencies):
        """Test that EnvValidationError causes sys.exit(1)"""
        from src.model.utils.env_validation import EnvValidationError
        
        mock_dependencies['env_validation'].validate_env_vars.side_effect = EnvValidationError(
            "Missing required environment variable: USER_EMAIL"
        )
        
        with pytest.raises(SystemExit) as exc_info:
            manual_email()
        
        assert exc_info.value.code == 1
        mock_dependencies['logger'].error.assert_called_once()
        assert "Environment validation failed" in str(mock_dependencies['logger'].error.call_args)
    
    def test_manual_email_missing_user_email(self, mock_dependencies):
        """Test handling of missing USER_EMAIL environment variable"""
        from src.model.utils.env_validation import EnvValidationError
        
        mock_dependencies['env_validation'].validate_env_vars.side_effect = EnvValidationError(
            "USER_EMAIL is required"
        )
        
        with pytest.raises(SystemExit) as exc_info:
            manual_email()
        
        assert exc_info.value.code == 1
        mock_dependencies['data_manager'].assert_not_called()
    
    def test_manual_email_missing_tickers(self, mock_dependencies):
        """Test handling of missing TICKERS environment variable"""
        from src.model.utils.env_validation import EnvValidationError
        
        mock_dependencies['env_validation'].validate_env_vars.side_effect = EnvValidationError(
            "TICKERS is required"
        )
        
        with pytest.raises(SystemExit) as exc_info:
            manual_email()
        
        assert exc_info.value.code == 1
    
    def test_manual_email_missing_user_agent(self, mock_dependencies):
        """Test handling of missing USER_AGENT environment variable"""
        from src.model.utils.env_validation import EnvValidationError
        
        mock_dependencies['env_validation'].validate_env_vars.side_effect = EnvValidationError(
            "USER_AGENT is required"
        )
        
        with pytest.raises(SystemExit) as exc_info:
            manual_email()
        
        assert exc_info.value.code == 1
    
    def test_manual_email_ticker_processing_failure(self, mock_dependencies):
        """Test that processing continues when a ticker fails"""
        mock_dependencies['env_validation'].validate_env_vars.return_value = {
            'USER_EMAIL': 'test@example.com',
            'TICKERS': 'AAPL,INVALID,GOOGL',
            'USER_AGENT': 'TestAgent/1.0'
        }
        mock_dependencies['env_validation'].parse_tickers.return_value = ['AAPL', 'INVALID', 'GOOGL']
        
        mock_manager_instance = Mock()
        mock_dependencies['data_manager'].return_value = mock_manager_instance
        
        mock_tracker_instance = Mock()
        mock_dependencies['progress_tracker'].return_value = mock_tracker_instance
        
        def side_effect(ticker, tracker):
            if ticker == 'INVALID':
                raise ValueError("Invalid ticker symbol")
        
        mock_manager_instance.process_ticker.side_effect = side_effect
        
        result = manual_email()
        
        assert isinstance(result, dict)
        assert mock_manager_instance.process_ticker.call_count == 3
        mock_dependencies['logger'].error.assert_called_once()
        assert "Failed to process ticker INVALID" in str(mock_dependencies['logger'].error.call_args)
        
        assert mock_tracker_instance.complete.call_count == 2
    
    def test_manual_email_all_tickers_fail(self, mock_dependencies):
        """Test processing when all tickers fail"""
        mock_dependencies['env_validation'].validate_env_vars.return_value = {
            'USER_EMAIL': 'test@example.com',
            'TICKERS': 'BAD1,BAD2',
            'USER_AGENT': 'TestAgent/1.0'
        }
        mock_dependencies['env_validation'].parse_tickers.return_value = ['BAD1', 'BAD2']
        
        mock_manager_instance = Mock()
        mock_dependencies['data_manager'].return_value = mock_manager_instance
        
        mock_tracker_instance = Mock()
        mock_dependencies['progress_tracker'].return_value = mock_tracker_instance
        
        mock_manager_instance.process_ticker.side_effect = Exception("Network error")
        
        result = manual_email()
        
        assert isinstance(result, dict)
        assert mock_dependencies['logger'].error.call_count == 2
        assert mock_tracker_instance.complete.call_count == 0
    
    def test_manual_email_logging_flow(self, mock_dependencies):
        """Test that appropriate logging occurs throughout execution"""
        mock_dependencies['env_validation'].validate_env_vars.return_value = {
            'USER_EMAIL': 'test@example.com',
            'TICKERS': 'AAPL',
            'USER_AGENT': 'TestAgent/1.0'
        }
        mock_dependencies['env_validation'].parse_tickers.return_value = ['AAPL']
        
        mock_manager_instance = Mock()
        mock_dependencies['data_manager'].return_value = mock_manager_instance
        
        mock_tracker_instance = Mock()
        mock_dependencies['progress_tracker'].return_value = mock_tracker_instance
        
        manual_email()
        
        logger = mock_dependencies['logger']
        
        info_calls = [str(call) for call in logger.info.call_args_list]
        
        assert any("Starting SEC data processing application" in call for call in info_calls)
        assert any("Validating environment variables" in call for call in info_calls)
        assert any("Environment validation successful" in call for call in info_calls)
        assert any("Processing ticker: AAPL" in call for call in info_calls)
        assert any("Successfully completed processing for AAPL" in call for call in info_calls)
        assert any("SEC data processing application completed" in call for call in info_calls)
    
    def test_manual_email_progress_tracker_lifecycle(self, mock_dependencies):
        """Test that ProgressTracker is properly initialized and used for each ticker"""
        mock_dependencies['env_validation'].validate_env_vars.return_value = {
            'USER_EMAIL': 'test@example.com',
            'TICKERS': 'AAPL,GOOGL',
            'USER_AGENT': 'TestAgent/1.0'
        }
        mock_dependencies['env_validation'].parse_tickers.return_value = ['AAPL', 'GOOGL']
        
        mock_manager_instance = Mock()
        mock_dependencies['data_manager'].return_value = mock_manager_instance
        
        tracker_instances = [Mock(), Mock()]
        mock_dependencies['progress_tracker'].side_effect = tracker_instances
        
        manual_email()
        
        assert mock_dependencies['progress_tracker'].call_count == 2
        
        tracker_instances[0].start.assert_called_once_with('AAPL')
        tracker_instances[0].complete.assert_called_once_with('AAPL')
        tracker_instances[1].start.assert_called_once_with('GOOGL')
        tracker_instances[1].complete.assert_called_once_with('GOOGL')
    
    def test_manual_email_data_manager_initialization(self, mock_dependencies):
        """Test that DataManager is initialized with correct user agent"""
        mock_dependencies['env_validation'].validate_env_vars.return_value = {
            'USER_EMAIL': 'test@example.com',
            'TICKERS': 'AAPL',
            'USER_AGENT': 'CustomAgent/2.0'
        }
        mock_dependencies['env_validation'].parse_tickers.return_value = ['AAPL']
        
        mock_manager_instance = Mock()
        mock_dependencies['data_manager'].return_value = mock_manager_instance
        
        mock_tracker_instance = Mock()
        mock_dependencies['progress_tracker'].return_value = mock_tracker_instance
        
        manual_email()
        
        mock_dependencies['data_manager'].assert_called_once_with('CustomAgent/2.0')
    
    def test_manual_email_returns_empty_dict(self, mock_dependencies):
        """Test that manual_email returns an empty dictionary"""
        mock_dependencies['env_validation'].validate_env_vars.return_value = {
            'USER_EMAIL': 'test@example.com',
            'TICKERS': 'AAPL',
            'USER_AGENT': 'TestAgent/1.0'
        }
        mock_dependencies['env_validation'].parse_tickers.return_value = ['AAPL']
        
        mock_manager_instance = Mock()
        mock_dependencies['data_manager'].return_value = mock_manager_instance
        
        mock_tracker_instance = Mock()
        mock_dependencies['progress_tracker'].return_value = mock_tracker_instance
        
        result = manual_email()
        
        assert result == {}
        assert isinstance(result, dict)