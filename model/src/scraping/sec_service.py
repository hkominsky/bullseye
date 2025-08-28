from typing import List, Dict, Optional, Any
from http_client import HttpClient
from models import Filing, FinancialRecord
import requests

class SECDataService:
    SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{}.json"
    SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{}.json"
    EDGAR_BASE_URL = "https://www.sec.gov/Archives/edgar/data"
    
    def __init__(self, http_client: HttpClient, ticker_mapping: Dict[str, str]):
        self.http_client = http_client
        self.ticker_mapping = ticker_mapping
    
    def get_recent_filings(self, ticker: str, form_types: List[str] = None) -> List[Filing]:
        if form_types is None:
            form_types = ["10-K", "10-Q"]
        cik = self._get_cik(ticker)
        url = self.SEC_SUBMISSIONS_URL.format(cik)
        response = self.http_client.get(url)
        data = response.json()
        return self._parse_filings(ticker, data, form_types)
    
    def get_financials(self, ticker: str, metric: str = "Revenues", limit: int = 5) -> Optional[List[FinancialRecord]]:
        cik = self._get_cik(ticker)
        url = self.SEC_COMPANY_FACTS_URL.format(cik)
        try:
            response = self.http_client.get(url)
            facts = response.json()
            return self._extract_financial_records(ticker, facts, metric, limit)
        except (requests.RequestException, KeyError):
            return None
    
    def _get_cik(self, ticker: str) -> str:
        if ticker not in self.ticker_mapping:
            raise ValueError(f"Unknown ticker: {ticker}")
        return self.ticker_mapping[ticker]
    
    def _parse_filings(self, ticker: str, data: Dict[str, Any], form_types: List[str]) -> List[Filing]:
        filings = []
        recent = data["filings"]["recent"]
        for form, date, accession in zip(
            recent["form"], 
            recent["filingDate"], 
            recent["accessionNumber"]
        ):
            if form in form_types:
                filing_url = self._build_filing_url(self._get_cik(ticker), accession)
                filings.append(Filing(
                    ticker=ticker,
                    form_type=form,
                    filing_date=date,
                    accession_number=accession,
                    filing_url=filing_url
                ))
        return filings
    
    def _build_filing_url(self, cik: str, accession: str) -> str:
        clean_accession = accession.replace('-', '')
        return f"{self.EDGAR_BASE_URL}/{int(cik)}/{clean_accession}/{accession}-index.htm"
    
    def _extract_financial_records(self, ticker: str, facts: Dict[str, Any], metric: str, limit: int) -> List[FinancialRecord]:
        try:
            revenues = facts["facts"]["us-gaap"][metric]["units"]["USD"]
            records = []
            for revenue_data in revenues[:limit]:
                records.append(FinancialRecord(
                    ticker=ticker,
                    date=revenue_data["end"],
                    value=revenue_data["val"]
                ))
            return records
        except KeyError:
            return []
