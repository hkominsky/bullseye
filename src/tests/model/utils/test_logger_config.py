import pytest
import logging
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from src.model.utils.logger_config import LoggerSetup


class TestLoggerSetup:
    
    @pytest.fixture
    def mock_log_dir(self, tmp_path):
        with patch.object(LoggerSetup, 'LOG_DIR', tmp_path):
            yield tmp_path
    
    def test_setup_logger_basic(self, mock_log_dir):
        logger = LoggerSetup.setup_logger('test_logger')
        
        assert logger.name == 'test_logger'
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1
    
    def test_setup_logger_custom_level(self, mock_log_dir):
        logger = LoggerSetup.setup_logger('test_logger', level=logging.DEBUG)
        
        assert logger.level == logging.DEBUG
    
    def test_setup_logger_custom_filename(self, mock_log_dir):
        logger = LoggerSetup.setup_logger('test_logger', filename='custom.log')
        
        log_file = mock_log_dir / 'custom.log'
        assert log_file.exists()
    
    def test_setup_logger_default_filename(self, mock_log_dir):
        logger = LoggerSetup.setup_logger('module.submodule.logger_name')
        
        log_file = mock_log_dir / 'logger_name.log'
        assert log_file.exists()
    
    def test_setup_logger_with_console(self, mock_log_dir):
        logger = LoggerSetup.setup_logger('test_logger', console=True)
        
        assert len(logger.handlers) == 2
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    
    def test_setup_logger_without_console(self, mock_log_dir):
        logger = LoggerSetup.setup_logger('test_logger', console=False)
        
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.FileHandler)
    
    def test_setup_logger_returns_existing(self, mock_log_dir):
        logger1 = LoggerSetup.setup_logger('test_logger')
        logger2 = LoggerSetup.setup_logger('test_logger')
        
        assert logger1 is logger2
        assert len(logger1.handlers) == 1
    
    def test_setup_logger_force_clean(self, mock_log_dir):
        logger1 = LoggerSetup.setup_logger('test_logger')
        initial_handlers = len(logger1.handlers)
        
        logger2 = LoggerSetup.setup_logger('test_logger', force_clean=True)
        
        assert logger1 is logger2
        assert len(logger2.handlers) == initial_handlers
    
    def test_setup_logger_propagate_false(self, mock_log_dir):
        logger = LoggerSetup.setup_logger('test_logger')
        
        assert logger.propagate == False
    
    def test_ensure_log_dir_creates_directory(self, tmp_path):
        log_dir = tmp_path / 'new_logs'
        with patch.object(LoggerSetup, 'LOG_DIR', log_dir):
            LoggerSetup._ensure_log_dir()
            
            assert log_dir.exists()
            assert log_dir.is_dir()
    
    def test_ensure_log_dir_existing_directory(self, tmp_path):
        with patch.object(LoggerSetup, 'LOG_DIR', tmp_path):
            LoggerSetup._ensure_log_dir()
            LoggerSetup._ensure_log_dir()
            
            assert tmp_path.exists()
    
    def test_clear_handlers(self, mock_log_dir):
        logger = logging.getLogger('test_clear')
        handler1 = logging.FileHandler(mock_log_dir / 'test1.log')
        handler2 = logging.FileHandler(mock_log_dir / 'test2.log')
        logger.addHandler(handler1)
        logger.addHandler(handler2)
        
        LoggerSetup._clear_handlers(logger)
        
        assert len(logger.handlers) == 0
    
    def test_get_formatter(self):
        formatter = LoggerSetup._get_formatter()
        
        assert isinstance(formatter, logging.Formatter)
        assert formatter._fmt == LoggerSetup.LOG_FORMAT
        assert formatter.datefmt == LoggerSetup.DATE_FORMAT
    
    def test_get_file_handler(self, mock_log_dir):
        formatter = LoggerSetup._get_formatter()
        handler = LoggerSetup._get_file_handler(
            'test_logger', 
            'test.log', 
            logging.INFO, 
            formatter
        )
        
        assert isinstance(handler, logging.FileHandler)
        assert handler.level == logging.INFO
    
    def test_get_file_handler_default_filename(self, mock_log_dir):
        formatter = LoggerSetup._get_formatter()
        handler = LoggerSetup._get_file_handler(
            'module.test_logger', 
            None, 
            logging.INFO, 
            formatter
        )
        
        assert 'test_logger.log' in str(handler.baseFilename)
    
    def test_get_console_handler(self):
        formatter = LoggerSetup._get_formatter()
        handler = LoggerSetup._get_console_handler(logging.DEBUG, formatter)
        
        assert isinstance(handler, logging.StreamHandler)
        assert handler.level == logging.DEBUG
    
    def test_logger_can_write(self, mock_log_dir):
        logger = LoggerSetup.setup_logger('test_write')
        
        logger.info("Test message")
        logger.debug("Debug message")
        logger.error("Error message")
        
        log_file = mock_log_dir / 'test_write.log'
        assert log_file.exists()
        
        content = log_file.read_text()
        assert "Test message" in content
    
    def test_different_log_levels(self, mock_log_dir):
        logger_info = LoggerSetup.setup_logger('test_info', level=logging.INFO)
        logger_debug = LoggerSetup.setup_logger('test_debug', level=logging.DEBUG)
        logger_warning = LoggerSetup.setup_logger('test_warning', level=logging.WARNING)
        
        assert logger_info.level == logging.INFO
        assert logger_debug.level == logging.DEBUG
        assert logger_warning.level == logging.WARNING
    
    def test_log_format_contains_required_fields(self):
        assert '%(asctime)s' in LoggerSetup.LOG_FORMAT
        assert '%(name)s' in LoggerSetup.LOG_FORMAT
        assert '%(levelname)s' in LoggerSetup.LOG_FORMAT
        assert '%(message)s' in LoggerSetup.LOG_FORMAT
    
    def test_date_format_valid(self):
        formatter = LoggerSetup._get_formatter()
        assert formatter.datefmt == "%Y-%m-%d %H:%M:%S"
    
    def test_project_root_is_path(self):
        assert isinstance(LoggerSetup.PROJECT_ROOT, Path)
    
    def test_log_dir_is_path(self):
        assert isinstance(LoggerSetup.LOG_DIR, Path)
    
    def test_multiple_loggers_different_names(self, mock_log_dir):
        logger1 = LoggerSetup.setup_logger('logger1')
        logger2 = LoggerSetup.setup_logger('logger2')
        
        assert logger1 is not logger2
        assert logger1.name == 'logger1'
        assert logger2.name == 'logger2'
    
    def test_handler_encoding_utf8(self, mock_log_dir):
        logger = LoggerSetup.setup_logger('test_encoding')
        
        file_handler = logger.handlers[0]
        assert file_handler.encoding == 'utf-8'