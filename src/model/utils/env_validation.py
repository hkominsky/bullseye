import os
import logging
from model.utils.logger_config import LoggerSetup


class EnvValidationError(Exception):
    """
    Custom exception raised when environment variable validation fails.
    """
    pass


class EnvValidation:
    """
    Static utility class for validating and parsing environment variables.
    """
    
    _logger = None
    
    @classmethod
    def _get_logger(cls) -> logging.Logger:
        if cls._logger is None:
            cls._logger = LoggerSetup.setup_logger(
                name=__name__,
                level=logging.INFO,
                filename="env_validation.log"
            )
        return cls._logger

    @staticmethod
    def validate_env_vars(required_vars):
        logger = EnvValidation._get_logger()
        logger.info(f"Validating environment variables: {required_vars}")
        
        missing = []
        env_values = {}

        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing.append(var)
                logger.warning(f"Missing environment variable: {var}")
            else:
                env_values[var] = value
                logger.debug(f"Found environment variable: {var}")

        if missing:
            error_msg = f"Missing required environment variables: {', '.join(missing)}"
            logger.error(error_msg)
            raise EnvValidationError(error_msg)

        logger.info(f"All {len(required_vars)} required environment variables validated successfully")
        return env_values

    @staticmethod
    def parse_stocks(stocks_str):
        logger = EnvValidation._get_logger()
        logger.info(f"Parsing stock symbols from string: {stocks_str}")
        
        stocks = [s.strip().upper() for s in stocks_str.split(",") if s.strip()]
        
        if not stocks:
            error_msg = "STOCKS environment variable must contain at least one symbol."
            logger.error(error_msg)
            raise EnvValidationError(error_msg)
        
        logger.info(f"Successfully parsed {len(stocks)} stock symbols: {stocks}")
        return stocks