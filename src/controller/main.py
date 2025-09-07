import sys
from dotenv import load_dotenv
import pandas as pd

from src.model.data_aggregator.manager import SECDataManager
from src.model.utils.env_validation import EnvValidation, EnvValidationError


def main():
    """
    Main function to process SEC financial data for specified stocks.

    Raises:
        SystemExit: If required environment variables are missing or invalid.
    """
    load_dotenv()
    required_vars = ["USER_EMAIL", "STOCKS", "USER_AGENT"]

    try:
        env = EnvValidation.validate_env_vars(required_vars)
        STOCKS = EnvValidation.parse_stocks(env["STOCKS"])
    except EnvValidationError as e:
        print(f"Error: {e}")
        sys.exit(1)

    manager = SECDataManager(env["USER_AGENT"])
    results = {}

    for stock in STOCKS:
        manager.process_stock(stock)

    return results


if __name__ == "__main__":
    """
    Entry point for the SEC data processing script.

    Output:
        Creates per-stock CSV files in src/model/sec_data_processor/ directory:
        - '<TICKER>_raw_financial_data.csv': Contains raw financial data
        - '<TICKER>_calculated_metrics.csv': Contains calculated financial metrics
        Sends per-stock emails with attached data.
    """
    all_results = main()
