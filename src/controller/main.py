import sys
from dotenv import load_dotenv

from src.model.data_aggregator.manager import SECDataManager
from src.model.utils.env_validation import EnvValidation, EnvValidationError
from src.model.utils.logger_config import LoggerSetup


def main():
    """
    Main function to process SEC financial data for specified stocks.
    """
    logger = LoggerSetup.setup_logger(__name__)
    logger.info("Starting SEC data processing application")
    
    load_dotenv()
    required_vars = ["USER_EMAIL", "STOCKS", "USER_AGENT"]

    try:
        logger.info("Validating environment variables")
        env = EnvValidation.validate_env_vars(required_vars)
        STOCKS = EnvValidation.parse_stocks(env["STOCKS"])
        logger.info(f"Environment validation successful. Processing {len(STOCKS)} stocks: {STOCKS}")
    except EnvValidationError as e:
        logger.error(f"Environment validation failed: {e}")
        sys.exit(1)

    manager = SECDataManager(env["USER_AGENT"])
    results = {}

    for stock in STOCKS:
        logger.info(f"Processing stock: {stock}")
        try:
            manager.process_stock(stock)
            logger.info(f"Successfully completed processing for {stock}")
        except Exception as e:
            logger.error(f"Failed to process stock {stock}: {e}")

    logger.info("SEC data processing application completed")
    return results
 

if __name__ == "__main__":
    """
    Entry point for the SEC data processing script. Sends per-stock emails with attached data.
    """
    all_results = main()