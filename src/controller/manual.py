import sys
from dotenv import load_dotenv
from src.model.data_pipeline.data_manager import DataManager
from src.model.utils.env_validation import EnvValidation, EnvValidationError
from src.model.utils.logger_config import LoggerSetup
from src.model.utils.progress_tracker import ProgressTracker


def manual_email():
    """
    Main function to process SEC financial data for specified tickers.
    """
    logger = LoggerSetup.setup_logger(__name__)
    logger.info("Starting SEC data processing application")
    
    load_dotenv()
    required_vars = ["USER_EMAIL", "TICKERS", "USER_AGENT"]

    try:
        logger.info("Validating environment variables")
        env = EnvValidation.validate_env_vars(required_vars)
        TICKERS = EnvValidation.parse_tickers(env["TICKERS"])
        logger.info(f"Environment validation successful. Processing {len(TICKERS)} tickers: {TICKERS}")
    except EnvValidationError as e:
        logger.error(f"Environment validation failed: {e}")
        sys.exit(1)

    manager = DataManager(env["USER_AGENT"])
    results = {}

    for ticker in TICKERS:
        logger.info(f"Processing ticker: {ticker}")        
        progress_tracker = ProgressTracker()
        progress_tracker.start(ticker)
        
        try:
            manager.process_ticker(ticker, progress_tracker)
            logger.info(f"Successfully completed processing for {ticker}")
            progress_tracker.complete(ticker)
        except Exception as e:
            logger.error(f"Failed to process ticker {ticker}: {e}")

    logger.info("SEC data processing application completed")
    return results


if __name__ == "__main__":
    """
    Entry point for the SEC data processing script. Sends per-ticker emails with attached data.
    """
    all_results = manual_email()