import pandas as pd
from typing import List, Optional, Any, Dict, Tuple
from datetime import datetime
from src.model.utils.models import FinancialRecord


class SECDataCleaner:
    def __init__(self, strict_validation: bool = False):
        """
        Initialize SEC Data Cleaner with minimal required parameters.
        """
        self.strict_validation = strict_validation
    
    def clean_financial_records(self, records: List[FinancialRecord]) -> List[FinancialRecord]:
        """
        Clean a list of FinancialRecord objects.
        """
        if not records:
            return records
        
        cleaned_records = []
        for record in records:
            cleaned_record = self._clean_individual_record(record)
            if cleaned_record:
                cleaned_records.append(cleaned_record)
        
        cleaned_records = self._remove_duplicate_records(cleaned_records)
        
        if cleaned_records:
            ticker = cleaned_records[0].ticker
            cleaned_records = self.impute_missing_quarterly_data(cleaned_records, ticker)
        
        return cleaned_records
    
    def impute_missing_quarterly_data(self, records: List[FinancialRecord], ticker: str) -> List[FinancialRecord]:
        """
        Impute missing quarterly data when only annual data is available.
        """
        fiscal_years = self._group_records_by_fiscal_year(records)
        imputed_records = records.copy()
        
        for fiscal_year, year_records in fiscal_years.items():
            self._impute_fiscal_year_data(year_records)
                                                        
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
        
        return fiscal_years
    
    def _calculate_fiscal_year(self, date_str: str) -> str:
        """
        Calculate fiscal year from date string.
        """
        date_obj = datetime.fromisoformat(date_str)
        if date_obj.month >= 10:
            return str(date_obj.year + 1)
        else:
            return str(date_obj.year)
    
    def _impute_fiscal_year_data(self, year_records: List[FinancialRecord]) -> None:
        """
        Impute missing data for records within a single fiscal year.
        """
        annual_record, quarterly_records, incomplete_records = self._categorize_records(year_records)
        
        if self._can_impute_data(annual_record, quarterly_records, incomplete_records):
            self._perform_imputation(annual_record, quarterly_records, incomplete_records)
    
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
            elif self._is_quarterly_record(record, period_type):
                quarterly_records.append(record)
                if self._is_incomplete_record(record):
                    incomplete_records.append(record)
        
        return annual_record, quarterly_records, incomplete_records
    
    def _is_annual_record(self, record: FinancialRecord, period_type: str) -> bool:
        """
        Check if record is an annual record.
        """
        return record.form_type == '10-K' and period_type in ['FY', 'Q3', 'Q4']
    
    def _is_quarterly_record(self, record: FinancialRecord, period_type: str) -> bool:
        """
        Check if record is a quarterly record.
        """
        return record.form_type == '10-Q' and period_type in ['Q1', 'Q2', 'Q3', 'Q4']
    
    def _is_incomplete_record(self, record: FinancialRecord) -> bool:
        """
        Check if record has missing key financial data.
        """
        return (record.revenue is None and 
                record.net_income is None and 
                record.operating_income is None)
    
    def _can_impute_data(self, annual_record: Optional[FinancialRecord], 
                        quarterly_records: List[FinancialRecord], 
                        incomplete_records: List[FinancialRecord]) -> bool:
        """
        Check if we have sufficient data to perform imputation.
        """
        return (annual_record is not None and 
                len(quarterly_records) >= 3 and 
                len(incomplete_records) > 0)
    
    def _perform_imputation(self, annual_record: FinancialRecord, 
                           quarterly_records: List[FinancialRecord], 
                           incomplete_records: List[FinancialRecord]) -> None:
        """
        Perform the actual imputation of missing quarterly data.
        """
        for incomplete_record in incomplete_records:
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
        return complete_records
    
    def _impute_record_fields(self, incomplete_record: FinancialRecord, 
                             annual_record: FinancialRecord, 
                             complete_quarterly_records: List[FinancialRecord]) -> None:
        """
        Impute missing fields for an incomplete record.
        """
        pure_quarterly_values = self._calculate_pure_quarterly_values(complete_quarterly_records)
        
        for field in self._get_imputable_fields():
            self._impute_single_field(incomplete_record, annual_record, field, pure_quarterly_values)
    
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
                           pure_quarterly_values: Dict[str, List[float]]) -> None:
        """
        Impute a single field for an incomplete record.
        """
        annual_value = getattr(annual_record, field, None)
        if annual_value is not None and field in pure_quarterly_values:
            pure_quarters_sum = sum(pure_quarterly_values[field])
            imputed_value = annual_value - pure_quarters_sum
            setattr(incomplete_record, field, imputed_value)
    
    def _extract_period_type(self, period: str) -> str:
        """
        Extract the period type from a period string that may include year.
        """
        if not period:
            return ""
        
        if ' ' in period:
            parts = period.split()
            if len(parts) >= 2:
                return parts[-1]
        
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
        if df.empty:
            return df
            
        df = self._normalize_dates(df)
        df = self._remove_duplicate_rows(df)
        
        return df
    
    def _clean_individual_record(self, record: FinancialRecord) -> Optional[FinancialRecord]:
        """
        Clean an individual financial record with enhanced validation.
        """
        try:
            record_dict = self._get_record_dict(record)
            
            if not self._process_date_validation(record_dict):
                return None
            
            self._calculate_missing_metrics(record_dict)
            
            return self._create_financial_record(record_dict)
                
        except Exception as e:
            print(f"Error cleaning record for {record.ticker}: {e}")
            return None
    
    def _get_record_dict(self, record: FinancialRecord) -> dict:
        """
        Get dictionary representation of a financial record.
        """
        return record.to_dict() if hasattr(record, 'to_dict') else record.__dict__.copy()
    
    def _process_date_validation(self, record_dict: dict) -> bool:
        """
        Process date validation for a record dictionary.
        """
        if not self._validate_date(record_dict.get('date')):
            if self.strict_validation:
                print(f"Invalid date for {record_dict.get('ticker')}: {record_dict.get('date')}")
                return False
            else:
                record_dict['date'] = self._normalize_date(record_dict.get('date'))
        return True
    
    def _create_financial_record(self, record_dict: dict) -> FinancialRecord:
        """
        Create a FinancialRecord from a dictionary.
        """
        if hasattr(FinancialRecord, 'from_dict'):
            return FinancialRecord.from_dict(record_dict)
        else:
            return FinancialRecord(**record_dict)
    
    def _remove_duplicate_records(self, records: List[FinancialRecord]) -> List[FinancialRecord]:
        """
        Remove duplicate records based on ticker, date, and form_type.
        """
        seen = set()
        unique_records = []
        
        for record in records:
            key = (record.ticker, record.date, record.form_type)
            if key not in seen:
                seen.add(key)
                unique_records.append(record)
        
        return unique_records
    
    def _calculate_missing_metrics(self, record_dict: dict) -> None:
        """
        Calculate any missing basic financial metrics.
        """
        self._calculate_gross_profit(record_dict)
        self._calculate_working_capital(record_dict)
    
    def _calculate_gross_profit(self, record_dict: dict) -> None:
        """
        Calculate gross profit if missing.
        """
        if (record_dict.get('gross_profit') is None and 
            record_dict.get('revenue') is not None and 
            record_dict.get('cost_of_revenue') is not None):
            record_dict['gross_profit'] = record_dict['revenue'] - record_dict['cost_of_revenue']
    
    def _calculate_working_capital(self, record_dict: dict) -> None:
        """
        Calculate working capital if missing.
        """
        if (record_dict.get('working_capital') is None and 
            record_dict.get('current_assets') is not None and 
            record_dict.get('current_liabilities') is not None):
            record_dict['working_capital'] = record_dict['current_assets'] - record_dict['current_liabilities']
    
    def _normalize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize dates in DataFrame.
        """
        if 'date' in df.columns:
            df['date'] = df['date'].apply(self._normalize_date)
        return df
    
    def _remove_duplicate_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate rows from DataFrame.
        """
        return df.drop_duplicates()
    
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
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        return None