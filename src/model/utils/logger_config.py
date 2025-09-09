import logging
from pathlib import Path
from typing import Optional


class LoggerSetup:
    """
    Centralized logger configuration. Provides a simple interface 
    for creating consistent loggers.
    """

    LOG_DIR = Path("logs")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    @classmethod
    def setup_logger(
        cls, 
        name: str, 
        level: int = logging.INFO,
        filename: Optional[str] = None
    ) -> logging.Logger:
        """
        Create and configure a logger with a file handler.
        """
        cls._ensure_log_dir()
        
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        if logger.handlers:
            return logger
        
        formatter = cls._get_formatter()
        file_handler = cls._get_file_handler(name, filename, level, formatter)
        
        logger.addHandler(file_handler)
        return logger

    @classmethod
    def _ensure_log_dir(cls) -> None:
        """
        Ensure that the log directory exists.
        Creates the directory if it does not already exist.
        """
        cls.LOG_DIR.mkdir(exist_ok=True)

    @classmethod
    def _get_formatter(cls) -> logging.Formatter:
        """
        Create a formatter for log messages.
        """
        return logging.Formatter(cls.LOG_FORMAT, cls.DATE_FORMAT)

    @classmethod
    def _get_file_handler(
        cls, 
        name: str, 
        filename: Optional[str], 
        level: int, 
        formatter: logging.Formatter
    ) -> logging.FileHandler:
        """
        Create a file handler for logging.
        """
        if filename is None:
            filename = name.split('.')[-1] + ".log"
        
        file_path = cls.LOG_DIR / filename
        handler = logging.FileHandler(file_path)
        handler.setLevel(level)
        handler.setFormatter(formatter)
        return handler
