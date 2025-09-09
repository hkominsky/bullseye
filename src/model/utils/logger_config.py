import logging
from pathlib import Path
from typing import Optional


class LoggerSetup:
    """
    Centralized logger configuration.
    Provides a simple interface for creating consistent loggers.
    """

    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    LOG_DIR = PROJECT_ROOT / "logs"

    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    @classmethod
    def setup_logger(
        cls,
        name: str,
        level: int = logging.INFO,
        filename: Optional[str] = None,
        force_clean: bool = False,
        console: bool = False
    ) -> logging.Logger:
        """
        Create and configure a logger with file handlers.
        """
        cls._ensure_log_dir()
        logger = logging.getLogger(name)

        if force_clean:
            cls._clear_handlers(logger)
        elif logger.handlers:
            return logger

        logger.setLevel(level)
        cls._attach_handlers(logger, name, filename, level, console)
        logger.propagate = False  # prevent double logging
        return logger

    @classmethod
    def _ensure_log_dir(cls) -> None:
        """Ensure that the log directory exists."""
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _clear_handlers(cls, logger: logging.Logger) -> None:
        """Remove all existing handlers from the logger."""
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()

    @classmethod
    def _attach_handlers(
        cls,
        logger: logging.Logger,
        name: str,
        filename: Optional[str],
        level: int,
        console: bool
    ) -> None:
        """Attach file and optional console handlers."""
        formatter = cls._get_formatter()

        # Always attach file handler
        file_handler = cls._get_file_handler(name, filename, level, formatter)
        logger.addHandler(file_handler)

        # Optional console handler
        if console:
            console_handler = cls._get_console_handler(level, formatter)
            logger.addHandler(console_handler)

    @classmethod
    def _get_formatter(cls) -> logging.Formatter:
        """Return the standard log formatter."""
        return logging.Formatter(cls.LOG_FORMAT, cls.DATE_FORMAT)

    @classmethod
    def _get_file_handler(
        cls,
        name: str,
        filename: Optional[str],
        level: int,
        formatter: logging.Formatter
    ) -> logging.FileHandler:
        """Create and configure a file handler."""
        if filename is None:
            filename = name.split('.')[-1] + ".log"

        file_path = cls.LOG_DIR / filename
        handler = logging.FileHandler(file_path, encoding="utf-8")
        handler.setLevel(level)
        handler.setFormatter(formatter)
        return handler

    @classmethod
    def _get_console_handler(
        cls,
        level: int,
        formatter: logging.Formatter
    ) -> logging.StreamHandler:
        """Create and configure a console (stdout) handler."""
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(formatter)
        return handler
