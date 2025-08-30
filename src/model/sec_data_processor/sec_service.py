from typing import List, Dict, Optional, Any
from model.utils.http_client import HttpClient
from model.utils.models import Filing, FinancialRecord, CompanyProfile
import requests
import re
from datetime import datetime


class SECDataService:
    SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{}.json"
    SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{}.json"
    EDGAR_BASE_URL = "https://www.sec.gov/Archives/edgar/data"
    
    # Comprehensive mapping of US-GAAP financial metrics
    FINANCIAL_METRICS = {
        # Income Statement
        'revenue': ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'],
        'cost_of_revenue': ['CostOfRevenue', 'CostOfGoodsAndServicesSold', 'CostOfSales'],
        'gross_profit': ['GrossProfit'],
        'operating_income': ['OperatingIncomeLoss', 'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest'],
        'net_income': ['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic'],
        'research_and_development': ['ResearchAndDevelopmentExpense'],
        'selling_general_admin': ['SellingGeneralAndAdministrativeExpense'],
        'interest_expense': ['InterestExpense'],
        
        # Balance Sheet
        'total_assets': ['Assets'],
        'current_assets': ['AssetsCurrent'],
        'cash_and_equivalents': ['CashAndCashEquivalentsAtCarryingValue', 'Cash', 'CashCashEquivalentsAndShortTermInvestments'],
        'accounts_receivable': ['AccountsReceivableNetCurrent', 'AccountsReceivableNet'],
        'inventory': ['InventoryNet'],
        'property_plant_equipment': ['PropertyPlantAndEquipmentNet'],
        'total_liabilities': ['Liabilities'],
        'current_liabilities': ['LiabilitiesCurrent'],
        'long_term_debt': ['LongTermDebtNoncurrent', 'LongTermDebt'],
        'shareholders_equity': ['StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],
        
        # Cash Flow
        'operating_cash_flow': ['NetCashProvidedByUsedInOperatingActivities'],
        'investing_cash_flow': ['NetCashProvidedByUsedInInvestingActivities'],
        'financing_cash_flow': ['NetCashProvidedByUsedInFinancingActivities'],
        'capital_expenditures': ['PaymentsToAcquirePropertyPlantAndEquipment'],
        
        # Share Information
        'shares_outstanding': ['CommonStockSharesOutstanding'],
        'weighted_average_shares': ['WeightedAverageNumberOfSharesOutstandingBasic', 'WeightedAverageNumberOfDilutedSharesOutstanding']
    }
    
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
    
    def get_company_profile(self, ticker: str) -> Optional[CompanyProfile]:
        """Get comprehensive company profile information"""
        try:
            cik = self._get_cik(ticker)
            url = self.SEC_SUBMISSIONS_URL.format(cik)
            response = self.http_client.get(url)
            data = response.json()
            
            return CompanyProfile(
                ticker=ticker,
                cik=cik,
                company_name=data.get('name', ''),
                sic_code=data.get('sic', ''),
                industry=data.get('sicDescription', ''),
                fiscal_year_end=data.get('fiscalYearEnd', ''),
                exchange=data.get('exchanges', [None])[0] if data.get('exchanges') else None,
                business_address={
                    'street1': data.get('addresses', {}).get('business', {}).get('street1', ''),
                    'city': data.get('addresses', {}).get('business', {}).get('city', ''),
                    'state': data.get('addresses', {}).get('business', {}).get('stateOrCountry', ''),
                    'zip': data.get('addresses', {}).get('business', {}).get('zipCode', '')
                }
            )
        except Exception:
            return None
    
    def get_comprehensive_financials(self, ticker: str, limit: int = 8) -> List[FinancialRecord]:
        """Get comprehensive financial data for multiple periods"""
        cik = self._get_cik(ticker)
        url = self.SEC_COMPANY_FACTS_URL.format(cik)
        
        try:
            response = self.http_client.get(url)
            facts = response.json()
            return self._extract_comprehensive_records(ticker, facts, limit)
        except (requests.RequestException, KeyError):
            return []
    
    def _get_cik(self, ticker: str) -> str:
        if ticker not in self.ticker_mapping:
            raise ValueError(f"Unknown ticker: {ticker}")
        return self.ticker_mapping[ticker]
    
    def _parse_filings(self, ticker: str, data: Dict[str, Any], form_types: List[str]) -> List[Filing]:
        filings = []
        recent = data["filings"]["recent"]
        
        for i, (form, date, accession) in enumerate(zip(
            recent["form"],
            recent["filingDate"],
            recent["accessionNumber"]
        )):
            if form in form_types:
                filing_url = self._build_filing_url(self._get_cik(ticker), accession)
                
                # Extract additional filing metadata
                period_report = recent.get("reportDate", [None] * len(recent["form"]))[i]
                doc_count = recent.get("documentCount", [None] * len(recent["form"]))[i]
                size_bytes = recent.get("size", [None] * len(recent["form"]))[i]
                primary_doc = recent.get("primaryDocument", [None] * len(recent["form"]))[i]
                
                # Check if it's an amendment
                is_amended = "/A" in form or "Amendment" in form
                
                filings.append(Filing(
                    ticker=ticker,
                    form_type=form,
                    filing_date=date,
                    accession_number=accession,
                    filing_url=filing_url,
                    period_of_report=period_report,
                    document_count=doc_count,
                    size_bytes=size_bytes,
                    is_amended=is_amended,
                    primary_document=primary_doc
                ))
        
        return filings
    
    def _build_filing_url(self, cik: str, accession: str) -> str:
        clean_accession = accession.replace('-', '')
        return f"{self.EDGAR_BASE_URL}/{int(cik)}/{clean_accession}/{accession}-index.htm"
    
    def _extract_comprehensive_records(self, ticker: str, facts: Dict[str, Any], limit: int) -> List[FinancialRecord]:
        """Extract comprehensive financial records with all available metrics"""
        if "facts" not in facts or "us-gaap" not in facts["facts"]:
            return []
        
        us_gaap_facts = facts["facts"]["us-gaap"]
        
        # Group data by period (end date and form type)
        period_data = {}
        
        # Process each metric type
        for field_name, metric_names in self.FINANCIAL_METRICS.items():
            for metric_name in metric_names:
                if metric_name in us_gaap_facts and "units" in us_gaap_facts[metric_name]:
                    units = us_gaap_facts[metric_name]["units"]
                    
                    # Look for USD values first, then shares for share-related metrics
                    unit_key = "USD"
                    if field_name in ['shares_outstanding', 'weighted_average_shares'] and "shares" in units:
                        unit_key = "shares"
                    
                    if unit_key in units:
                        for entry in units[unit_key]:
                            end_date = entry.get("end")
                            form_type = entry.get("form", "")
                            value = entry.get("val")
                            
                            if end_date and value is not None:
                                # Create period key
                                period_key = f"{end_date}_{form_type}"
                                
                                if period_key not in period_data:
                                    period_data[period_key] = {
                                        'ticker': ticker,
                                        'date': end_date,
                                        'form_type': form_type,
                                        'period': self._determine_period(end_date, form_type)
                                    }
                                
                                # Only update if we don't already have this metric or if this is more recent
                                if field_name not in period_data[period_key]:
                                    period_data[period_key][field_name] = value
        
        # Convert to FinancialRecord objects
        records = []
        for period_key, data in period_data.items():
            # Only include records that have at least revenue or total assets
            if data.get('revenue') or data.get('total_assets'):
                record = FinancialRecord(**data)
                records.append(record)
        
        # Sort by date (most recent first) and limit results
        records.sort(key=lambda x: x.date, reverse=True)
        return records[:limit]
    
    def _determine_period(self, end_date: str, form_type: str) -> str:
        """Determine the reporting period (Q1, Q2, Q3, Q4, FY)"""
        try:
            date_obj = datetime.fromisoformat(end_date)
            month = date_obj.month
            
            if form_type == "10-K":
                return "FY"
            elif form_type == "10-Q":
                if month in [3, 4]:
                    return "Q1"
                elif month in [6, 7]:
                    return "Q2"
                elif month in [9, 10]:
                    return "Q3"
                elif month in [12, 1]:
                    return "Q4"
            
            # Default determination based on month
            quarter_map = {
                1: "Q4", 2: "Q4", 3: "Q1",
                4: "Q1", 5: "Q1", 6: "Q2",
                7: "Q2", 8: "Q2", 9: "Q3",
                10: "Q3", 11: "Q3", 12: "Q4"
            }
            return quarter_map.get(month, "Unknown")
            
        except Exception:
            return "Unknown"