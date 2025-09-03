from typing import List, Dict, Any
from datetime import datetime
import requests

from src.model.utils.http_client import HttpClient
from src.model.utils.models import FinancialRecord


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

        Args:
            http_client (HttpClient): Client to fetch SEC data.
            ticker_mapping (Dict[str, str]): Mapping of ticker symbols to CIK identifiers.
        """
        self.http_client = http_client
        self.ticker_mapping = ticker_mapping

    def extract_raw_financial_data(self, ticker: str, limit: int = 8) -> List[FinancialRecord]:
        """
        Extract raw SEC financial data for a given ticker.

        Args:
            ticker (str): Stock ticker symbol.
            limit (int, optional): Number of periods to return. Defaults to 8.

        Returns:
            List[FinancialRecord]: List of financial records sorted by date (most recent first).
        """
        cik = self._get_cik(ticker)
        url = self.SEC_COMPANY_FACTS_URL.format(cik)

        try:
            response = self.http_client.get(url)
            response.raise_for_status()
            facts = response.json()
            return self._parse_facts_to_records(ticker, facts, limit)

        except requests.RequestException as e:
            print(f"HTTP error retrieving financial data for {ticker}: {e}")
        except (KeyError, ValueError) as e:
            print(f"Data parsing error for {ticker}: {e}")
        except Exception as e:
            print(f"Unexpected error retrieving financial data for {ticker}: {e}")

        return []

    def _get_cik(self, ticker: str) -> str:
        """
        Get the CIK for a given ticker.

        Args:
            ticker (str): Stock ticker symbol.

        Returns:
            str: The CIK identifier.
        """
        if ticker not in self.ticker_mapping:
            raise ValueError(
                f"Unknown ticker: {ticker}. Available tickers: {list(self.ticker_mapping.keys())[:10]}..."
            )
        return self.ticker_mapping[ticker]

    def _parse_facts_to_records(self, ticker: str, facts: Dict[str, Any], limit: int) -> List[FinancialRecord]:
        """
        Convert SEC facts JSON into a list of FinancialRecord objects.

        Args:
            ticker (str): Stock ticker symbol.
            facts (Dict[str, Any]): Raw SEC facts JSON.
            limit (int): Number of records to return.

        Returns:
            List[FinancialRecord]: Parsed financial records.
        """
        if "facts" not in facts or "us-gaap" not in facts["facts"]:
            print(f"No US-GAAP data found for {ticker}")
            return []

        us_gaap_facts = facts["facts"]["us-gaap"]
        period_data: Dict[str, Dict[str, Any]] = {}

        for field_name, metric_names in self.FINANCIAL_METRICS.items():
            self._collect_metric_data(ticker, us_gaap_facts, field_name, metric_names, period_data)

        records: List[FinancialRecord] = []
        for data in period_data.values():
            if self._has_sufficient_data(data):
                try:
                    record = self._build_financial_record(data)
                    records.append(record)
                except Exception as e:
                    print(f"Error creating FinancialRecord for {ticker}: {e}")

        records.sort(key=lambda x: x.date, reverse=True)
        return records[:limit]

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

        Args:
            ticker (str): Stock ticker symbol.
            us_gaap_facts (Dict[str, Any]): GAAP fact data from SEC.
            field_name (str): Logical financial metric name.
            metric_names (List[str]): Possible SEC field names for the metric.
            period_data (Dict[str, Dict[str, Any]]): Dictionary of collected period data.
        """
        for metric_name in metric_names:
            if metric_name not in us_gaap_facts or "units" not in us_gaap_facts[metric_name]:
                continue

            units = us_gaap_facts[metric_name]["units"]
            unit_key = self._determine_unit_key(field_name, units)

            if unit_key not in units:
                continue

            for entry in units[unit_key]:
                if not self._validate_entry(entry):
                    continue
                self._update_period_data(ticker, field_name, entry, period_data)

    def _update_period_data(
        self, ticker: str, field_name: str, entry: Dict[str, Any], period_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Insert or update a financial metric entry in the period_data dictionary.

        Args:
            ticker (str): Stock ticker symbol.
            field_name (str): Logical financial metric name.
            entry (Dict[str, Any]): SEC entry containing financial data.
            period_data (Dict[str, Dict[str, Any]]): Dictionary of collected period data.
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

        if (field_name not in period_data[period_key] or
                self._should_update_metric(period_data[period_key], entry)):
            period_data[period_key][field_name] = value

    def _build_financial_record(self, data: Dict[str, Any]) -> FinancialRecord:
        """
        Build a FinancialRecord from raw period data.

        Args:
            data (Dict[str, Any]): Dictionary of financial fields.

        Returns:
            FinancialRecord: Dataclass instance of financial record.
        """
        valid_fields = {k: v for k, v in data.items() if k in FinancialRecord.__dataclass_fields__}
        return FinancialRecord(**valid_fields)

    def _determine_unit_key(self, field_name: str, units: Dict) -> str:
        """
        Determine which unit key to use for a given metric.

        Args:
            field_name (str): Logical financial metric name.
            units (Dict): Units dictionary from SEC data.

        Returns:
            str: The chosen unit key.
        """
        share_fields = ['shares_outstanding', 'weighted_average_shares', 'shares_issued']

        if field_name in share_fields:
            if "shares" in units:
                return "shares"
            elif "pure" in units:
                return "pure"

        if "USD" in units:
            return "USD"
        elif "pure" in units and field_name in ['current_ratio', 'debt_to_equity', 'asset_turnover']:
            return "pure"

        return next(iter(units), "USD")

    def _validate_entry(self, entry: Dict[str, Any]) -> bool:
        """
        Validate an SEC data entry for required fields and reasonable values.

        Args:
            entry (Dict[str, Any]): A single SEC entry.

        Returns:
            bool: True if entry is valid, False otherwise.
        """
        if not entry.get('end') or entry.get('val') is None:
            return False

        val = entry['val']
        if not isinstance(val, (int, float)) or abs(val) > 1e15:
            return False

        try:
            datetime.fromisoformat(entry['end'])
        except (ValueError, TypeError):
            return False

        return True

    def _should_update_metric(self, existing_data: Dict, new_entry: Dict) -> bool:
        """
        Decide whether a new entry should replace an existing metric.

        Args:
            existing_data (Dict): The current metric data.
            new_entry (Dict): A new SEC entry.

        Returns:
            bool: True if new entry should replace, False otherwise.
        """
        new_form = new_entry.get('form', '')
        existing_form = existing_data.get('form_type', '')

        if '10-K' in new_form and '10-Q' in existing_form:
            return True
        if '10-Q' in new_form and '10-K' in existing_form:
            return False

        return False

    def _has_sufficient_data(self, data: Dict) -> bool:
        """
        Check if a record has enough data to be useful.

        Args:
            data (Dict): Financial data for a period.

        Returns:
            bool: True if sufficient, False otherwise.
        """
        return data.get('revenue') is not None or data.get('total_assets') is not None

    def _determine_period(self, end_date: str, form_type: str, frame: str = "") -> str:
        """
        Determine reporting period (quarter or FY) from form type, frame, and end date.

        Args:
            end_date (str): Period end date in ISO format.
            form_type (str): SEC form type (e.g., "10-K", "10-Q").
            frame (str, optional): Frame label provided by SEC.

        Returns:
            str: Reporting period with year (e.g., "2024 Q1", "2024 Q2", "2024 FY", "Unknown").
        """
        try:
            date_obj = datetime.fromisoformat(end_date)
            year = date_obj.year
            
            # Try to extract period from frame first
            frame_period = self._extract_period_from_frame(frame)
            if frame_period:
                return f"{year} {frame_period}"
            
            # Fall back to form type and date-based logic
            period = self._determine_period_from_form_and_date(form_type, date_obj.month)
            return f"{year} {period}" if period != "Unknown" else "Unknown"
            
        except Exception:
            return "Unknown"

    def _extract_period_from_frame(self, frame: str) -> str:
        """
        Extract period information from SEC frame string.
        
        Args:
            frame (str): Frame label from SEC data.
            
        Returns:
            str: Period string (Q1, Q2, Q3, Q4, FY) or empty string if not found.
        """
        if not frame:
            return ""
        
        frame_upper = frame.upper()
        
        for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
            if quarter in frame_upper:
                return quarter
        
        if 'CY' in frame_upper and 'Q' not in frame_upper:
            return "FY"
        
        return ""

    def _determine_period_from_form_and_date(self, form_type: str, month: int) -> str:
        """
        Determine period based on SEC form type and month.
        
        Args:
            form_type (str): SEC form type (e.g., "10-K", "10-Q").
            month (int): Month number (1-12).
            
        Returns:
            str: Period string (Q1, Q2, Q3, Q4, FY, Unknown).
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
        
        Args:
            month (int): Month number (1-12).
            
        Returns:
            str: Quarter string (Q1, Q2, Q3, Q4, Unknown).
        """
        month_to_quarter = {
            1: "Q4", 2: "Q4", 3: "Q1", 4: "Q1", 5: "Q1", 6: "Q2",
            7: "Q2", 8: "Q2", 9: "Q3", 10: "Q3", 11: "Q3", 12: "Q4"
        }
        return month_to_quarter.get(month, "Unknown")

    def _get_quarter_from_month(self, month: int) -> str:
        """
        Map month to standard calendar quarter.
        
        Args:
            month (int): Month number (1-12).
            
        Returns:
            str: Quarter string (Q1, Q2, Q3, Q4).
        """
        if month in [1, 2, 3]:
            return "Q1"
        elif month in [4, 5, 6]:
            return "Q2"
        elif month in [7, 8, 9]:
            return "Q3"
        else:  # month in [10, 11, 12]
            return "Q4"