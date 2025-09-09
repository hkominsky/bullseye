import os


class EnvValidationError(Exception):
    """
    Custom exception raised when environment variable validation fails.
    """
    pass


class EnvValidation:
    """
    Static utility class for validating and parsing environment variables.
    
    This class provides methods to ensure that required environment variables
    are present and to parse specific types of environment variable values.
    All methods are static and the class is not intended to be instantiated.
    """

    @staticmethod
    def validate_env_vars(required_vars):
        """
        Validate that all required environment variables are set and non-empty.
        """
        missing = []
        env_values = {}

        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing.append(var)
            else:
                env_values[var] = value

        if missing:
            raise EnvValidationError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        return env_values

    @staticmethod
    def parse_stocks(stocks_str):
        """
        Parse a comma-separated string of stock symbols into a list.
        """
        stocks = [s.strip().upper() for s in stocks_str.split(",") if s.strip()]
        if not stocks:
            raise EnvValidationError(
                "STOCKS environment variable must contain at least one symbol."
            )
        return stocks