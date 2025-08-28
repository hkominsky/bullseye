from dataclasses import dataclass

@dataclass
class Filing:
    ticker: str
    form_type: str
    filing_date: str
    accession_number: str
    filing_url: str

@dataclass
class FinancialRecord:
    ticker: str
    date: str
    value: float
