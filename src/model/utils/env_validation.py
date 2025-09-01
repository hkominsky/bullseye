import os


class EnvValidationError(Exception):
    pass


class EnvValidation:

    @staticmethod
    def validate_env_vars(required_vars):
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
        stocks = [s.strip().upper() for s in stocks_str.split(",") if s.strip()]
        if not stocks:
            raise EnvValidationError(
                "STOCKS environment variable must contain at least one symbol."
            )
        return stocks
