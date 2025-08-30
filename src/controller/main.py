import os
from dotenv import load_dotenv
from src.model.sec_data_processor.processor import SECDataProcessor
from src.model.notifier.notifications import ConsoleNotifier, EmailNotifier

def main():
    load_dotenv()

    USER_EMAIL = os.getenv("USER_EMAIL")
    STOCKS = os.getenv("STOCKS").split(",")
    USER_AGENT = os.getenv("USER_AGENT")

    notifiers = [
        ConsoleNotifier(),
        EmailNotifier(USER_EMAIL)
    ]
    
    processor = SECDataProcessor(USER_AGENT, notifiers)
    
    processor.print_filings_for_tickers(STOCKS)
    df = processor.get_financial_dataframe(STOCKS)
    print(df.head())

if __name__ == "__main__":
    main()
