import pandas as pd
from typing import List, Optional, Any, Dict, Tuple
from datetime import datetime
from src.model.utils.models import FinancialRecord
from src.model.utils.logger_config import LoggerSetup


class SECDataCleaner:
    def __init__(self, strict_validation: bool = False):
        """
        Initialize SEC Data Cleaner with minimal required parameters.
        """
        self.logger = LoggerSetup.setup_logger(__name__)
        self.strict_validation = strict_validation
        self.logger.info(f"SECDataCleaner initialized with strict_validation: {strict_validation}")
    
    def clean_financial_records(self, records: List[FinancialRecord]) -> List[FinancialRecord]:
        """
        Clean a list of FinancialRecord objects.
        """
        self.logger.info(f"Starting to clean {len(records)} financial records")
        
        if not records:
            self.logger.warning("No records provided for cleaning")
            return records
        
        cleaned_records = []
        for i, record in enumerate(records):
            self.logger.debug(f"Cleaning record {i+1}/{len(records)} for {getattr(record, 'ticker', 'unknown')}")
            cleaned_record = self._clean_individual_record(record)
            if cleaned_record:
                cleaned_records.append(cleaned_record)
            else:
                self.logger.warning(f"Record {i+1} was filtered out during cleaning")
        
        self.logger.info(f"Individual cleaning complete: {len(cleaned_records)} records remain")
        
        cleaned_records = self._remove_duplicate_records(cleaned_records)
        self.logger.info(f"After duplicate removal: {len(cleaned_records)} records remain")
        
        if cleaned_records:
            ticker = cleaned_records[0].ticker
            self.logger.info(f"Starting data imputation for ticker {ticker}")
            cleaned_records = self.impute_missing_quarterly_data(cleaned_records, ticker)
        
        self.logger.info(f"Cleaning process complete: returning {len(cleaned_records)} records")
        return cleaned_records
    
    def impute_missing_quarterly_data(self, records: List[FinancialRecord], ticker: str) -> List[FinancialRecord]:
        """
        Impute missing quarterly data when only annual data is available.
        """
        self.logger.info(f"Starting quarterly data imputation for {ticker} with {len(records)} records")
        
        fiscal_years = self._group_records_by_fiscal_year(records)
        self.logger.debug(f"Grouped records into {len(fiscal_years)} fiscal years: {list(fiscal_years.keys())}")
        
        imputed_records = records.copy()
        
        for fiscal_year, year_records in fiscal_years.items():
            self.logger.debug(f"Processing fiscal year {fiscal_year} with {len(year_records)} records")
            self._impute_fiscal_year_data(year_records)
                                                        
        self.logger.info(f"Quarterly data imputation complete for {ticker}")
        return imputed_records
    
    def _group_records_by_fiscal_year(self, records: List[FinancialRecord]) -> Dict[str, List[FinancialRecord]]:
        """
        Group records by fiscal year based on their dates.
        """
        fiscal_years = {}
        for record in records:
            if record.date:
                fiscal_year = self._calculate_fiscal_year(record.date)
                
                if fiscal_year not in fiscal_years:
                    fiscal_years[fiscal_year] = []
                fiscal_years[fiscal_year].append(record)
        
        self.logger.debug(f"Records grouped by fiscal year: {[(fy, len(recs)) for fy, recs in fiscal_years.items()]}")
        return fiscal_years
    
    def _calculate_fiscal_year(self, date_str: str) -> str:
        """
        Calculate fiscal year from date string.
        """
        date_obj = datetime.fromisoformat(date_str)
        if date_obj.month >= 10:
            fiscal_year = str(date_obj.year + 1)
        else:
            fiscal_year = str(date_obj.year)
        
        self.logger.debug(f"Calculated fiscal year {fiscal_year} for date {date_str}")
        return fiscal_year
    
    def _impute_fiscal_year_data(self, year_records: List[FinancialRecord]) -> None:
        """
        Impute missing data for records within a single fiscal year.
        """
        annual_record, quarterly_records, incomplete_records = self._categorize_records(year_records)
        
        self.logger.debug(f"Categorized records - Annual: {1 if annual_record else 0}, "
                         f"Quarterly: {len(quarterly_records)}, Incomplete: {len(incomplete_records)}")
        
        if self._can_impute_data(annual_record, quarterly_records, incomplete_records):
            self.logger.info(f"Conditions met for imputation - proceeding with data imputation")
            self._perform_imputation(annual_record, quarterly_records, incomplete_records)
        else:
            self.logger.debug("Insufficient data for imputation - skipping")
    
    def _categorize_records(self, year_records: List[FinancialRecord]) -> Tuple[Optional[FinancialRecord], List[FinancialRecord], List[FinancialRecord]]:
        """
        Categorize records into annual, quarterly, and incomplete records.
        """
        annual_record = None
        quarterly_records = []
        incomplete_records = []
        
        for record in year_records:
            period_type = self._extract_period_type(record.period)
            
            if self._is_annual_record(record, period_type):
                annual_record = record
                self.logger.debug(f"Found annual record: {record.period} ({record.form_type})")
            elif self._is_quarterly_record(record, period_type):
                quarterly_records.append(record)
                if self._is_incomplete_record(record):
                    incomplete_records.append(record)
                    self.logger.debug(f"Found incomplete quarterly record: {record.period}")
        
        return annual_record, quarterly_records, incomplete_records
    
    def _is_annual_record(self, record: FinancialRecord, period_type: str) -> bool:
        """
        Check if record is an annual record.
        """
        is_annual = record.form_type == '10-K' and period_type in ['FY', 'Q3', 'Q4']
        if is_annual:
            self.logger.debug(f"Record identified as annual: {period_type} ({record.form_type})")
        return is_annual
    
    def _is_quarterly_record(self, record: FinancialRecord, period_type: str) -> bool:
        """
        Check if record is a quarterly record.
        """
        is_quarterly = record.form_type == '10-Q' and period_type in ['Q1', 'Q2', 'Q3', 'Q4']
        if is_quarterly:
            self.logger.debug(f"Record identified as quarterly: {period_type} ({record.form_type})")
        return is_quarterly
    
    def _is_incomplete_record(self, record: FinancialRecord) -> bool:
        """
        Check if record has missing key financial data.
        """
        is_incomplete = (record.revenue is None and 
                        record.net_income is None and 
                        record.operating_income is None)
        if is_incomplete:
            self.logger.debug(f"Record marked as incomplete: missing revenue, net_income, and operating_income")
        return is_incomplete
    
    def _can_impute_data(self, annual_record: Optional[FinancialRecord], 
                        quarterly_records: List[FinancialRecord], 
                        incomplete_records: List[FinancialRecord]) -> bool:
        """
        Check if we have sufficient data to perform imputation.
        """
        can_impute = (annual_record is not None and 
                     len(quarterly_records) >= 3 and 
                     len(incomplete_records) > 0)
        
        if can_impute:
            self.logger.debug("Imputation criteria met: have annual record, ≥3 quarterly records, and incomplete records")
        else:
            self.logger.debug(f"Imputation criteria not met - Annual: {annual_record is not None}, "
                             f"Quarterly: {len(quarterly_records)}, Incomplete: {len(incomplete_records)}")
        
        return can_impute
    
    def _perform_imputation(self, annual_record: FinancialRecord, 
                           quarterly_records: List[FinancialRecord], 
                           incomplete_records: List[FinancialRecord]) -> None:
        """
        Perform the actual imputation of missing quarterly data.
        """
        self.logger.info(f"Starting imputation for {len(incomplete_records)} incomplete records")
        
        for i, incomplete_record in enumerate(incomplete_records):
            self.logger.debug(f"Imputing record {i+1}/{len(incomplete_records)}: {incomplete_record.period}")
            complete_quarterly_records = self._get_complete_quarterly_records(quarterly_records, incomplete_record)
            self._impute_record_fields(incomplete_record, annual_record, complete_quarterly_records)
    
    def _get_complete_quarterly_records(self, quarterly_records: List[FinancialRecord], 
                                      incomplete_record: FinancialRecord) -> List[FinancialRecord]:
        """
        Get complete quarterly records excluding the incomplete one.
        """
        complete_records = [
            q for q in quarterly_records 
            if q != incomplete_record and q.revenue is not None
        ]
        complete_records.sort(key=lambda x: x.date)
        
        self.logger.debug(f"Found {len(complete_records)} complete quarterly records for imputation")
        return complete_records
    
    def _impute_record_fields(self, incomplete_record: FinancialRecord, 
                             annual_record: FinancialRecord, 
                             complete_quarterly_records: List[FinancialRecord]) -> None:
        """
        Impute missing fields for an incomplete record.
        """
        pure_quarterly_values = self._calculate_pure_quarterly_values(complete_quarterly_records)
        imputed_fields = 0
        
        for field in self._get_imputable_fields():
            if self._impute_single_field(incomplete_record, annual_record, field, pure_quarterly_values):
                imputed_fields += 1
        
        self.logger.debug(f"Imputed {imputed_fields} fields for record {incomplete_record.period}")
    
    def _get_imputable_fields(self) -> List[str]:
        """
        Get list of fields that can be imputed.
        """
        income_statement_fields = [
            'revenue', 'cost_of_revenue', 'gross_profit', 'operating_income', 
            'net_income', 'research_and_development', 'selling_general_admin'
        ]
        cash_flow_fields = [
            'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow',
            'capital_expenditures'
        ]
        return income_statement_fields + cash_flow_fields
    
    def _calculate_pure_quarterly_values(self, complete_quarterly_records: List[FinancialRecord]) -> Dict[str, List[float]]:
        """
        Calculate pure quarterly values from cumulative quarterly data.
        """
        pure_quarterly_values = {}
        
        self.logger.debug(f"Calculating pure quarterly values from {len(complete_quarterly_records)} complete records")
        
        for field in self._get_imputable_fields():
            pure_quarterly_values[field] = []
            for i, record in enumerate(complete_quarterly_records):
                current_value = getattr(record, field, 0) or 0
                if i == 0:
                    pure_value = current_value
                else:
                    previous_cumulative = getattr(complete_quarterly_records[i-1], field, 0) or 0
                    pure_value = current_value - previous_cumulative
                pure_quarterly_values[field].append(pure_value)
        
        return pure_quarterly_values
    
    def _impute_single_field(self, incomplete_record: FinancialRecord, 
                           annual_record: FinancialRecord, 
                           field: str, 
                           pure_quarterly_values: Dict[str, List[float]]) -> bool:
        """
        Impute a single field for an incomplete record.
        Returns True if field was imputed, False otherwise.
        """
        annual_value = getattr(annual_record, field, None)
        if annual_value is not None and field in pure_quarterly_values:
            pure_quarters_sum = sum(pure_quarterly_values[field])
            imputed_value = annual_value - pure_quarters_sum
            setattr(incomplete_record, field, imputed_value)
            self.logger.debug(f"Imputed {field}: {imputed_value} (annual: {annual_value}, quarters sum: {pure_quarters_sum})")
            return True
        return False
    
    def _extract_period_type(self, period: str) -> str:
        """
        Extract the period type from a period string that may include year.
        """
        if not period:
            return ""
        
        if ' ' in period:
            parts = period.split()
            if len(parts) >= 2:
                period_type = parts[-1]
                self.logger.debug(f"Extracted period type '{period_type}' from '{period}'")
                return period_type
        
        return period
    
    def _is_annual_period(self, period: str) -> bool:
        """
        Check if a period represents an annual/full-year period.
        """
        period_type = self._extract_period_type(period)
        return period_type in ['FY', 'Q4']
    
    def _is_quarterly_period(self, period: str) -> bool:
        """
        Check if a period represents a quarterly period.
        """
        period_type = self._extract_period_type(period)
        return period_type in ['Q1', 'Q2', 'Q3', 'Q4']
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean a pandas DataFrame of financial data.
        """
        self.logger.info(f"Starting DataFrame cleaning with {len(df) if not df.empty else 0} rows")
        
        if df.empty:
            self.logger.warning("Empty DataFrame provided for cleaning")
            return df
            
        original_rows = len(df)
        df = self._normalize_dates(df)
        df = self._remove_duplicate_rows(df)
        final_rows = len(df)
        
        self.logger.info(f"DataFrame cleaning complete - rows: {original_rows} → {final_rows}")
        return df
    
    def _clean_individual_record(self, record: FinancialRecord) -> Optional[FinancialRecord]:
        """
        Clean an individual financial record with enhanced validation.
        """
        try:
            ticker = getattr(record, 'ticker', 'unknown')
            self.logger.debug(f"Cleaning individual record for {ticker}")
            
            record_dict = self._get_record_dict(record)
            
            if not self._process_date_validation(record_dict):
                self.logger.warning(f"Record for {ticker} failed date validation")
                return None
            
            self._calculate_missing_metrics(record_dict)
            
            cleaned_record = self._create_financial_record(record_dict)
            self.logger.debug(f"Successfully cleaned record for {ticker}")
            return cleaned_record
                
        except Exception as e:
            self.logger.error(f"Error cleaning record for {getattr(record, 'ticker', 'unknown')}: {e}")
            return None
    
    def _get_record_dict(self, record: FinancialRecord) -> dict:
        """
        Get dictionary representation of a financial record.
        """
        if hasattr(record, 'to_dict'):
            return record.to_dict()
        else:
            return record.__dict__.copy()
    
    def _process_date_validation(self, record_dict: dict) -> bool:
        """
        Process date validation for a record dictionary.
        """
        date_val = record_dict.get('date')
        if not self._validate_date(date_val):
            ticker = record_dict.get('ticker', 'unknown')
            if self.strict_validation:
                self.logger.warning(f"Invalid date for {ticker}: {date_val} (strict validation enabled)")
                return False
            else:
                normalized_date = self._normalize_date(date_val)
                if normalized_date:
                    record_dict['date'] = normalized_date
                    self.logger.debug(f"Normalized date for {ticker}: {date_val} → {normalized_date}")
                else:
                    self.logger.warning(f"Could not normalize date for {ticker}: {date_val}")
                    return False
        return True
    
    def _create_financial_record(self, record_dict: dict) -> FinancialRecord:
        """
        Create a FinancialRecord from a dictionary.
        """
        if hasattr(FinancialRecord, 'from_dict'):
            return FinancialRecord.from_dict(record_dict)
        else:
            # Filter out any keys that aren't valid FinancialRecord fields
            valid_fields = {k: v for k, v in record_dict.items() 
                           if k in FinancialRecord.__dataclass_fields__}
            return FinancialRecord(**valid_fields)
    
    def _remove_duplicate_records(self, records: List[FinancialRecord]) -> List[FinancialRecord]:
        """
        Remove duplicate records based on ticker, date, and form_type.
        """
        seen = set()
        unique_records = []
        duplicates_removed = 0
        
        for record in records:
            key = (record.ticker, record.date, record.form_type)
            if key not in seen:
                seen.add(key)
                unique_records.append(record)
            else:
                duplicates_removed += 1
        
        if duplicates_removed > 0:
            self.logger.info(f"Removed {duplicates_removed} duplicate records")
        
        return unique_records
    
    def _calculate_missing_metrics(self, record_dict: dict) -> None:
        """
        Calculate any missing basic financial metrics.
        """
        calculated_metrics = 0
        
        if self._calculate_gross_profit(record_dict):
            calculated_metrics += 1
        if self._calculate_working_capital(record_dict):
            calculated_metrics += 1
        
        if calculated_metrics > 0:
            ticker = record_dict.get('ticker', 'unknown')
            self.logger.debug(f"Calculated {calculated_metrics} missing metrics for {ticker}")
    
    def _calculate_gross_profit(self, record_dict: dict) -> bool:
        """
        Calculate gross profit if missing.
        Returns True if calculated, False otherwise.
        """
        if (record_dict.get('gross_profit') is None and 
            record_dict.get('revenue') is not None and 
            record_dict.get('cost_of_revenue') is not None):
            record_dict['gross_profit'] = record_dict['revenue'] - record_dict['cost_of_revenue']
            self.logger.debug(f"Calculated gross profit: {record_dict['gross_profit']}")
            return True
        return False
    
    def _calculate_working_capital(self, record_dict: dict) -> bool:
        """
        Calculate working capital if missing.
        Returns True if calculated, False otherwise.
        """
        if (record_dict.get('working_capital') is None and 
            record_dict.get('current_assets') is not None and 
            record_dict.get('current_liabilities') is not None):
            record_dict['working_capital'] = record_dict['current_assets'] - record_dict['current_liabilities']
            self.logger.debug(f"Calculated working capital: {record_dict['working_capital']}")
            return True
        return False
    
    def _normalize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize dates in DataFrame.
        """
        if 'date' in df.columns:
            self.logger.debug("Normalizing dates in DataFrame")
            df['date'] = df['date'].apply(self._normalize_date)
        return df
    
    def _remove_duplicate_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate rows from DataFrame.
        """
        original_count = len(df)
        df = df.drop_duplicates()
        duplicates_removed = original_count - len(df)
        
        if duplicates_removed > 0:
            self.logger.info(f"Removed {duplicates_removed} duplicate rows from DataFrame")
        
        return df
    
    def _validate_date(self, date_val: Any) -> bool:
        """
        Validate if date is in acceptable format.
        """
        if date_val is None:
            return False
        
        try:
            if isinstance(date_val, str):
                return self._validate_string_date(date_val)
            elif isinstance(date_val, (datetime, pd.Timestamp)):
                return True
            return False
        except Exception:
            return False
    
    def _validate_string_date(self, date_str: str) -> bool:
        """
        Validate string date against multiple formats.
        """
        date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']
        for fmt in date_formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        return False
    
    def _normalize_date(self, date_val: Any) -> Optional[str]:
        """
        Normalize date to standard format.
        """
        if date_val is None:
            return None
        
        try:
            if isinstance(date_val, str):
                return self._normalize_string_date(date_val)
            elif isinstance(date_val, (datetime, pd.Timestamp)):
                return date_val.strftime('%Y-%m-%d')
        except Exception:
            pass
        
        return None
    
    def _normalize_string_date(self, date_str: str) -> Optional[str]:
        """
        Normalize string date to standard format.
        """
        date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                normalized = dt.strftime('%Y-%m-%d')
                self.logger.debug(f"Normalized date: {date_str} → {normalized}")
                return normalized
            except ValueError:
                continue
        self.logger.debug(f"Could not normalize date string: {date_str}")
        return None