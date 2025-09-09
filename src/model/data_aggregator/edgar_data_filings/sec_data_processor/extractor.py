from typing import List, Dict, Any
from datetime import datetime
import requests

from src.model.utils.http_client import HttpClient
from src.model.utils.models import FinancialRecord
from src.model.utils.logger_config import LoggerSetup


class SECDataExtractor:
    """
    Extracts raw financial data from the SEC Company Facts API.
    """

    SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{}.json"

    FINANCIAL_METRICS = {
        'revenue': [
            'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax',
            'SalesRevenueNet', 'RevenueFromContractWithCustomerIncludingAssessedTax',
            'TotalRevenues', 'SalesRevenueGross'
        ],
        'cost_of_revenue': ['CostOfRevenue', 'CostOfGoodsAndServicesSold', 'CostOfSales', 'CostOfGoodsSold'],
        'gross_profit': ['GrossProfit'],
        'operating_income': [
            'OperatingIncomeLoss',
            'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest'
        ],
        'net_income': [
            'NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic',
            'NetIncomeLossAttributableToParent'
        ],
        'research_and_development': ['ResearchAndDevelopmentExpense'],
        'selling_general_admin': ['SellingGeneralAndAdministrativeExpense'],
        'ebitda': ['EarningsBeforeInterestTaxesDepreciationAmortization'],
        'total_assets': ['Assets'],
        'current_assets': ['AssetsCurrent'],
        'cash_and_equivalents': [
            'CashAndCashEquivalentsAtCarryingValue', 'Cash',
            'CashCashEquivalentsAndShortTermInvestments'
        ],
        'accounts_receivable': ['AccountsReceivableNetCurrent', 'AccountsReceivableNet', 'ReceivablesNetCurrent'],
        'inventory': ['InventoryNet', 'InventoryFinishedGoodsNetOfReserves'],
        'property_plant_equipment': ['PropertyPlantAndEquipmentNet'],
        'intangible_assets': ['IntangibleAssetsNetExcludingGoodwill', 'FiniteLivedIntangibleAssetsNet'],
        'goodwill': ['Goodwill'],
        'total_liabilities': ['Liabilities'],
        'current_liabilities': ['LiabilitiesCurrent'],
        'accounts_payable': ['AccountsPayableCurrent'],
        'short_term_debt': ['ShortTermBorrowings', 'CommercialPaper'],
        'long_term_debt': ['LongTermDebtNoncurrent', 'LongTermDebt', 'LongTermDebtAndCapitalLeaseObligations'],
        'total_debt': ['DebtCurrent', 'DebtNoncurrent'],
        'shareholders_equity': [
            'StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'
        ],
        'retained_earnings': ['RetainedEarningsAccumulatedDeficit'],
        'operating_cash_flow': ['NetCashProvidedByUsedInOperatingActivities'],
        'investing_cash_flow': ['NetCashProvidedByUsedInInvestingActivities'],
        'financing_cash_flow': ['NetCashProvidedByUsedInFinancingActivities'],
        'capital_expenditures': [
            'PaymentsToAcquirePropertyPlantAndEquipment', 'CapitalExpendituresIncurredButNotYetPaid'
        ],
        'dividends_paid': ['PaymentsOfDividends', 'PaymentsOfDividendsCommonStock'],
        'share_repurchases': ['PaymentsForRepurchaseOfCommonStock'],
        'shares_outstanding': [
            'CommonStockSharesOutstanding', 'WeightedAverageNumberOfSharesOutstandingBasic',
            'CommonStockSharesIssued', 'SharesOutstanding'
        ],
        'weighted_average_shares': [
            'WeightedAverageNumberOfSharesOutstandingBasic',
            'WeightedAverageNumberOfDilutedSharesOutstanding',
            'CommonStockSharesOutstanding'
        ],
        'shares_issued': ['CommonStockSharesIssued'],
        'depreciation_amortization': ['DepreciationDepletionAndAmortization', 'Depreciation'],
        'stock_based_compensation': ['ShareBasedCompensation'],
        'provision_for_credit_losses': ['ProvisionForLoanAndLeaseLosses'],
        'restructuring_costs': ['RestructuringCharges'],
        'impairment_charges': ['AssetImpairmentCharges'],
        'domestic_revenue': ['RevenueDomestic'],
        'foreign_revenue': ['RevenueForeign'],
        'working_capital': ['WorkingCapital'],
        'book_value_per_share': ['BookValuePerShare'],
        'tangible_book_value': ['TangibleBookValue']
    }

    def __init__(self, http_client: HttpClient, ticker_mapping: Dict[str, str]):
        """
        Initialize the extractor with HTTP client and ticker-to-CIK mapping.
        """
        self.logger = LoggerSetup.setup_logger(__name__)
        self.http_client = http_client
        self.ticker_mapping = ticker_mapping
        self.logger.info(f"SECDataExtractor initialized with {len(ticker_mapping)} ticker mappings")

    def extract_raw_financial_data(self, ticker: str, limit: int = 8) -> List[FinancialRecord]:
        """
        Extract raw SEC financial data for a given ticker.
        """
        self.logger.info(f"Extracting financial data for {ticker} with limit {limit}")
        
        try:
            cik = self._get_cik(ticker)
            url = self.SEC_COMPANY_FACTS_URL.format(cik)
            self.logger.debug(f"Fetching data from SEC API for {ticker} (CIK: {cik})")

            response = self.http_client.get(url)
            response.raise_for_status()
            facts = response.json()
            
            records = self._parse_facts_to_records(ticker, facts, limit)
            self.logger.info(f"Successfully extracted {len(records)} financial records for {ticker}")
            return records

        except requests.RequestException as e:
            self.logger.error(f"HTTP error retrieving financial data for {ticker}: {e}")
        except (KeyError, ValueError) as e:
            self.logger.error(f"Data parsing error for {ticker}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving financial data for {ticker}: {e}")

        return []

    def _get_cik(self, ticker: str) -> str:
        """
        Get the CIK for a given ticker.
        """
        if ticker not in self.ticker_mapping:
            available_tickers = list(self.ticker_mapping.keys())[:10]
            self.logger.error(f"Unknown ticker: {ticker}. Available tickers sample: {available_tickers}")
            raise ValueError(
                f"Unknown ticker: {ticker}. Available tickers: {available_tickers}..."
            )
        
        cik = self.ticker_mapping[ticker]
        self.logger.debug(f"Found CIK {cik} for ticker {ticker}")
        return cik

    def _parse_facts_to_records(self, ticker: str, facts: Dict[str, Any], limit: int) -> List[FinancialRecord]:
        """
        Convert SEC facts JSON into a list of FinancialRecord objects.
        """
        self.logger.debug(f"Parsing SEC facts to records for {ticker}")
        
        if "facts" not in facts or "us-gaap" not in facts["facts"]:
            self.logger.warning(f"No US-GAAP data found for {ticker}")
            return []

        us_gaap_facts = facts["facts"]["us-gaap"]
        period_data: Dict[str, Dict[str, Any]] = {}

        for field_name, metric_names in self.FINANCIAL_METRICS.items():
            self._collect_metric_data(ticker, us_gaap_facts, field_name, metric_names, period_data)

        self.logger.debug(f"Collected data for {len(period_data)} periods for {ticker}")

        records: List[FinancialRecord] = []
        for period_key, data in period_data.items():
            if self._has_sufficient_data(data):
                try:
                    record = self._build_financial_record(data)
                    records.append(record)
                except Exception as e:
                    self.logger.error(f"Error creating FinancialRecord for {ticker} period {period_key}: {e}")

        records.sort(key=lambda x: x.date, reverse=True)
        final_records = records[:limit]
        self.logger.debug(f"Built {len(final_records)} financial records for {ticker}")
        return final_records

    def _collect_metric_data(
        self,
        ticker: str,
        us_gaap_facts: Dict[str, Any],
        field_name: str,
        metric_names: List[str],
        period_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Collect metric values for a field across reporting periods.
        """
        for metric_name in metric_names:
            if metric_name not in us_gaap_facts or "units" not in us_gaap_facts[metric_name]:
                continue

            units = us_gaap_facts[metric_name]["units"]
            unit_key = self._determine_unit_key(field_name, units)

            if unit_key not in units:
                continue

            entries_count = len(units[unit_key])
            self.logger.debug(f"Processing {entries_count} entries for {field_name} ({metric_name}) for {ticker}")

            for entry in units[unit_key]:
                if not self._validate_entry(entry):
                    continue
                self._update_period_data(ticker, field_name, entry, period_data)

    def _update_period_data(
        self, ticker: str, field_name: str, entry: Dict[str, Any], period_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Insert or update a financial metric entry in the period_data dictionary.
        """
        end_date = entry.get("end")
        form_type = entry.get("form", "")
        value = entry.get("val")
        frame = entry.get("frame", "")

        if not end_date or value is None:
            return

        period_key = f"{end_date}_{form_type}"
        if period_key not in period_data:
            period_data[period_key] = {
                'ticker': ticker,
                'date': end_date,
                'form_type': form_type,
                'period': self._determine_period(end_date, form_type, frame)
            }
            self.logger.debug(f"Created new period {period_key} for {ticker}")

        if (field_name not in period_data[period_key] or
                self._should_update_metric(period_data[period_key], entry)):
            period_data[period_key][field_name] = value
            self.logger.debug(f"Updated {field_name} for {ticker} period {period_key}: {value}")

    def _build_financial_record(self, data: Dict[str, Any]) -> FinancialRecord:
        """
        Build a FinancialRecord from raw period data.
        """
        ticker = data.get('ticker', 'Unknown')
        period = data.get('period', 'Unknown')
        self.logger.debug(f"Building FinancialRecord for {ticker} period {period}")
        
        valid_fields = {k: v for k, v in data.items() if k in FinancialRecord.__dataclass_fields__}
        record = FinancialRecord(**valid_fields)
        
        self.logger.debug(f"Built FinancialRecord for {ticker} with {len(valid_fields)} fields")
        return record

    def _determine_unit_key(self, field_name: str, units: Dict) -> str:
        """
        Determine which unit key to use for a given metric.
        """
        share_fields = ['shares_outstanding', 'weighted_average_shares', 'shares_issued']

        if field_name in share_fields:
            if "shares" in units:
                self.logger.debug(f"Using 'shares' unit for {field_name}")
                return "shares"
            elif "pure" in units:
                self.logger.debug(f"Using 'pure' unit for {field_name}")
                return "pure"

        if "USD" in units:
            self.logger.debug(f"Using 'USD' unit for {field_name}")
            return "USD"
        elif "pure" in units and field_name in ['current_ratio', 'debt_to_equity', 'asset_turnover']:
            self.logger.debug(f"Using 'pure' unit for ratio field {field_name}")
            return "pure"

        default_unit = next(iter(units), "USD")
        self.logger.debug(f"Using default unit '{default_unit}' for {field_name}")
        return default_unit

    def _validate_entry(self, entry: Dict[str, Any]) -> bool:
        """
        Validate an SEC data entry for required fields and reasonable values.
        """
        if not entry.get('end') or entry.get('val') is None:
            return False

        val = entry['val']
        if not isinstance(val, (int, float)) or abs(val) > 1e15:
            self.logger.debug(f"Invalid value rejected: {val}")
            return False

        try:
            datetime.fromisoformat(entry['end'])
        except (ValueError, TypeError):
            self.logger.debug(f"Invalid date rejected: {entry.get('end')}")
            return False

        return True

    def _should_update_metric(self, existing_data: Dict, new_entry: Dict) -> bool:
        """
        Decide whether a new entry should replace an existing metric.
        """
        new_form = new_entry.get('form', '')
        existing_form = existing_data.get('form_type', '')

        if '10-K' in new_form and '10-Q' in existing_form:
            self.logger.debug(f"Updating metric: 10-K supersedes 10-Q")
            return True
        if '10-Q' in new_form and '10-K' in existing_form:
            self.logger.debug(f"Keeping existing metric: 10-K takes precedence over 10-Q")
            return False

        return False

    def _has_sufficient_data(self, data: Dict) -> bool:
        """
        Check if a record has enough data to be useful.
        """
        has_revenue = data.get('revenue') is not None
        has_assets = data.get('total_assets') is not None
        
        sufficient = has_revenue or has_assets
        if not sufficient:
            self.logger.debug(f"Insufficient data for record - no revenue or total assets")
        
        return sufficient

    def _determine_period(self, end_date: str, form_type: str, frame: str = "") -> str:
        """
        Determine reporting period (quarter or FY) from form type, frame, and end date.
        """
        try:
            date_obj = datetime.fromisoformat(end_date)
            year = date_obj.year
            
            frame_period = self._extract_period_from_frame(frame)
            if frame_period:
                period = f"{year} {frame_period}"
                self.logger.debug(f"Determined period from frame: {period}")
                return period
            
            period_type = self._determine_period_from_form_and_date(form_type, date_obj.month)
            period = f"{year} {period_type}" if period_type != "Unknown" else "Unknown"
            self.logger.debug(f"Determined period from form/date: {period}")
            return period
            
        except Exception as e:
            self.logger.warning(f"Error determining period for {end_date}: {e}")
            return "Unknown"

    def _extract_period_from_frame(self, frame: str) -> str:
        """
        Extract period information from SEC frame string.
        """
        if not frame:
            return ""
        
        frame_upper = frame.upper()
        
        for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
            if quarter in frame_upper:
                self.logger.debug(f"Extracted quarter {quarter} from frame: {frame}")
                return quarter
        
        if 'CY' in frame_upper and 'Q' not in frame_upper:
            self.logger.debug(f"Extracted FY from frame: {frame}")
            return "FY"
        
        return ""

    def _determine_period_from_form_and_date(self, form_type: str, month: int) -> str:
        """
        Determine period based on SEC form type and month.
        """
        if form_type == "10-K":
            return "FY"
        elif form_type == "10-Q":
            return self._get_quarter_from_10q_month(month)
        else:
            return self._get_quarter_from_month(month)

    def _get_quarter_from_10q_month(self, month: int) -> str:
        """
        Map month to quarter for 10-Q filings (which have specific timing rules).
        """
        month_to_quarter = {
            1: "Q4", 2: "Q4", 3: "Q1", 4: "Q1", 5: "Q1", 6: "Q2",
            7: "Q2", 8: "Q2", 9: "Q3", 10: "Q3", 11: "Q3", 12: "Q4"
        }
        quarter = month_to_quarter.get(month, "Unknown")
        self.logger.debug(f"Mapped 10-Q month {month} to quarter {quarter}")
        return quarter

    def _get_quarter_from_month(self, month: int) -> str:
        """
        Map month to standard calendar quarter.
        """
        if month in [1, 2, 3]:
            return "Q1"
        elif month in [4, 5, 6]:
            return "Q2"
        elif month in [7, 8, 9]:
            return "Q3"
        else: 
            return "Q4"