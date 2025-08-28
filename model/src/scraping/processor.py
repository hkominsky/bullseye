from http_client import HttpClient
from cache import FileCache
from ticker_service import TickerMappingService
from sec_service import SECDataService
from models import Filing, FinancialRecord
import pandas as pd
from typing import List

class SECDataProcessor:
    def __init__(self, user_agent: str):
        self.http_client = HttpClient(user_agent)
        self.cache = FileCache()
        self.ticker_service = TickerMappingService(self.http_client, self.cache)
        
        ticker_mapping = self.ticker_service.get_ticker_to_cik_mapping()
        self.sec_service = SECDataService(self.http_client, ticker_mapping)
    
    def get_filings(self, tickers: List[str]) -> None:
        for ticker in tickers:
            self.sec_service.get_recent_filings(ticker)
    
    def get_financial_dataframe(self, tickers: List[str]) -> pd.DataFrame:
        records = []
        for ticker in tickers:
            financial_records = self.sec_service.get_financials(ticker)
            if financial_records:
                for record in financial_records:
                    records.append({
                        "ticker": record.ticker,
                        "date": record.date,
                        "value": record.value
                    })
        return pd.DataFrame(records)
