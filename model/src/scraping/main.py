# sec_fetcher/main.py
from processor import SECDataProcessor

def main():
    STOCKS = ['AAPL', 'GOOGL', 'MSFT']
    USER_AGENT = "Hugh Kominsky hugh.kominsky@gmail.com"
    
    processor = SECDataProcessor(USER_AGENT)
    
    processor.get_filings(STOCKS)

if __name__ == "__main__":
    main()
