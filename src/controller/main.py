import sys
from dotenv import load_dotenv
from src.model.edgar_data_filings.sec_data_processor.manager import SECDataManager
from src.model.utils.env_validation import EnvValidation, EnvValidationError
from src.model.notifier.notifications import EmailNotifier

def main():
    """
    Main function to process SEC financial data for specified stocks.
    
    Loads environment variables, validates required configuration,
    initializes the SEC data manager, and retrieves financial data split
    into raw data and calculated metrics.
    
    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (raw_data_df, calculated_metrics_df)
                     or (empty DataFrame, empty DataFrame) if no data retrieved.
                      
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
    raw_df, metrics_df = manager.get_split_financial_dataframes(STOCKS)
    
    if raw_df.empty and metrics_df.empty:
        print("No financial data retrieved.")
        return raw_df, metrics_df
        
    return raw_df, metrics_df

if __name__ == "__main__":
    """
    Entry point for the SEC data processing script.
    
    Output:
        Creates two CSV files in src/model/sec_data_processor/ directory:
        - 'raw_financial_data.csv': Contains raw financial data
        - 'calculated_metrics.csv': Contains calculated financial metrics
    """
    raw_df, metrics_df = main()
        
    if (raw_df is not None and not raw_df.empty) or (metrics_df is not None and not metrics_df.empty):
        raw_output_file = "src/model/edgar_data_filings/sec_data_processor/raw_financial_data.csv"
        metrics_output_file = "src/model/edgar_data_filings/sec_data_processor/calculated_metrics.csv"
        
        if not raw_df.empty:
            raw_df.to_csv(raw_output_file, index=False)
            
        if not metrics_df.empty:
            metrics_df.to_csv(metrics_output_file, index=False)
        
        notifier = EmailNotifier()
        result = notifier.send_email(raw_df, metrics_df)
        
        if result[0]:
            status, body, headers = result
            print(f"Email sent with split data! Status code: {status}")
        else:
            print("Email failed to send.")
    else:
        print("No data to save or send.")