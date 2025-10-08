import pytest
from unittest.mock import patch, Mock
from src.model.utils.env_validation import EnvValidation, EnvValidationError


class TestEnvValidation:
    
    def test_validate_env_vars_all_present(self):
        with patch.dict('os.environ', {
            'VAR1': 'value1',
            'VAR2': 'value2',
            'VAR3': 'value3'
        }):
            result = EnvValidation.validate_env_vars(['VAR1', 'VAR2', 'VAR3'])
            
            assert result == {'VAR1': 'value1', 'VAR2': 'value2', 'VAR3': 'value3'}
    
    def test_validate_env_vars_single_missing(self):
        with patch.dict('os.environ', {
            'VAR1': 'value1',
            'VAR2': 'value2'
        }, clear=True):
            with pytest.raises(EnvValidationError, match="Missing required environment variables: VAR3"):
                EnvValidation.validate_env_vars(['VAR1', 'VAR2', 'VAR3'])
    
    def test_validate_env_vars_multiple_missing(self):
        with patch.dict('os.environ', {
            'VAR1': 'value1'
        }, clear=True):
            with pytest.raises(EnvValidationError) as exc_info:
                EnvValidation.validate_env_vars(['VAR1', 'VAR2', 'VAR3'])
            
            assert 'VAR2' in str(exc_info.value)
            assert 'VAR3' in str(exc_info.value)
    
    def test_validate_env_vars_all_missing(self):
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(EnvValidationError):
                EnvValidation.validate_env_vars(['VAR1', 'VAR2'])
    
    def test_validate_env_vars_empty_list(self):
        result = EnvValidation.validate_env_vars([])
        assert result == {}
    
    def test_validate_env_vars_empty_string_value(self):
        with patch.dict('os.environ', {
            'VAR1': '',
            'VAR2': 'value2'
        }):
            with pytest.raises(EnvValidationError, match="VAR1"):
                EnvValidation.validate_env_vars(['VAR1', 'VAR2'])
    
    def test_parse_tickers_single(self):
        result = EnvValidation.parse_tickers('AAPL')
        assert result == ['AAPL']
    
    def test_parse_tickers_multiple(self):
        result = EnvValidation.parse_tickers('AAPL,MSFT,GOOGL')
        assert result == ['AAPL', 'MSFT', 'GOOGL']
    
    def test_parse_tickers_with_spaces(self):
        result = EnvValidation.parse_tickers('AAPL, MSFT , GOOGL')
        assert result == ['AAPL', 'MSFT', 'GOOGL']
    
    def test_parse_tickers_lowercase_converted(self):
        result = EnvValidation.parse_tickers('aapl,msft')
        assert result == ['AAPL', 'MSFT']
    
    def test_parse_tickers_mixed_case(self):
        result = EnvValidation.parse_tickers('AaPl,MsFt,GoOgL')
        assert result == ['AAPL', 'MSFT', 'GOOGL']
    
    def test_parse_tickers_empty_string(self):
        with pytest.raises(EnvValidationError, match="must contain at least one symbol"):
            EnvValidation.parse_tickers('')
    
    def test_parse_tickers_only_whitespace(self):
        with pytest.raises(EnvValidationError, match="must contain at least one symbol"):
            EnvValidation.parse_tickers('   ')
    
    def test_parse_tickers_empty_entries_ignored(self):
        result = EnvValidation.parse_tickers('AAPL,,MSFT,  ,GOOGL')
        assert result == ['AAPL', 'MSFT', 'GOOGL']
    
    def test_parse_tickers_trailing_comma(self):
        result = EnvValidation.parse_tickers('AAPL,MSFT,')
        assert result == ['AAPL', 'MSFT']
    
    def test_parse_tickers_leading_comma(self):
        result = EnvValidation.parse_tickers(',AAPL,MSFT')
        assert result == ['AAPL', 'MSFT']
    
    def test_parse_tickers_extra_whitespace(self):
        result = EnvValidation.parse_tickers('  AAPL  ,  MSFT  ')
        assert result == ['AAPL', 'MSFT']
    
    def test_env_validation_error_is_exception(self):
        assert issubclass(EnvValidationError, Exception)
    
    def test_env_validation_error_message(self):
        error = EnvValidationError("Test error message")
        assert str(error) == "Test error message"
    
    def test_validate_env_vars_preserves_values(self):
        with patch.dict('os.environ', {
            'API_KEY': 'secret123',
            'USER_EMAIL': 'test@example.com'
        }):
            result = EnvValidation.validate_env_vars(['API_KEY', 'USER_EMAIL'])
            
            assert result['API_KEY'] == 'secret123'
            assert result['USER_EMAIL'] == 'test@example.com'
    
    def test_parse_tickers_single_with_whitespace(self):
        result = EnvValidation.parse_tickers('  AAPL  ')
        assert result == ['AAPL']
    
    def test_get_logger_singleton(self):
        logger1 = EnvValidation._get_logger()
        logger2 = EnvValidation._get_logger()
        
        assert logger1 is logger2