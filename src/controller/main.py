import sys
from dotenv import load_dotenv
from src.model.sec_data_processor.manager import SECDataManager
from src.model.utils.env_validation import EnvValidation, EnvValidationError


def main():
    """
    Main function to process SEC financial data for specified stocks.
    
    Loads environment variables, validates required configuration,
    initializes the SEC data manager, and retrieves financial data.
    
    Returns:
        pd.DataFrame: DataFrame containing financial data for all specified stocks,
                     or empty DataFrame if no data retrieved.
                     
    Raises:
        SystemExit: If required environment variables are missing or invalid.
        
    Note:
        Requires the following environment variables:
        - USER_EMAIL: Email address for SEC API identification
        - STOCKS: Comma-separated list of stock ticker symbols
        - USER_AGENT: User agent string for SEC API requests
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
    df = manager.get_financial_dataframe(STOCKS)

    if df.empty:
        print("No financial data retrieved.")
        return df
    
    return df


if __name__ == "__main__":
    """
    Entry point for the SEC data processing script.
    
    Executes the main data retrieval process and saves results to CSV file.
    Handles the complete workflow from environment setup to data storage.
    
    Process:
    1. Execute main() to retrieve financial data
    2. Validate data availability
    3. Save DataFrame to CSV file for persistence
    4. Print completion status
    
    Output:
        Creates 'financial_data.csv' in src/model/sec_data_processor/ directory
        containing all retrieved financial data.
        
    Future enhancements:
        - SQL database storage implementation
        - Notification system for data updates
    """
    df = main()
    
    if df is not None and not df.empty:
        # Save DataFrame to CSV
        output_file = "src/model/sec_data_processor/financial_data.csv"
        df.to_csv(output_file, index=False)
        
        # TODO: add SQL storage and notifiers