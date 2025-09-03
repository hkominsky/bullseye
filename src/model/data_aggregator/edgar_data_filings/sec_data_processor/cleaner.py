import pandas as pd
from typing import List, Optional, Any
from datetime import datetime
from src.model.utils.models import FinancialRecord


class SECDataCleaner:
    def __init__(self, strict_validation: bool = False):
        """
        Initialize SEC Data Cleaner with minimal required parameters.
        
        Args:
            strict_validation (bool): If True, raises warnings for data issues instead of silent fixes.
        """
        self.strict_validation = strict_validation
    
    def clean_financial_records(self, records: List[FinancialRecord]) -> List[FinancialRecord]:
        """
        Clean a list of FinancialRecord objects.
        
        Args:
            records (List[FinancialRecord]): List of financial records to clean.
        
        Returns:
            List[FinancialRecord]: Cleaned financial records.
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
        
        Args:
            records (List[FinancialRecord]): Financial records for a ticker.
            ticker (str): Stock ticker symbol.
        
        Returns:
            List[FinancialRecord]: Financial records with imputed quarterly data.
        """
        fiscal_years = {}
        for record in records:
            if record.date:
                date_obj = datetime.fromisoformat(record.date)
                if date_obj.month >= 10:
                    fiscal_year = str(date_obj.year + 1)
                else:
                    fiscal_year = str(date_obj.year)
                
                if fiscal_year not in fiscal_years:
                    fiscal_years[fiscal_year] = []
                fiscal_years[fiscal_year].append(record)
        
        imputed_records = records.copy()
        
        for fiscal_year, year_records in fiscal_years.items():
            annual_record = None
            quarterly_records = []
            incomplete_records = []
            
            for record in year_records:
                period_type = self._extract_period_type(record.period)
                
                # Check for annual records
                if (record.form_type == '10-K' and 
                    period_type in ['FY', 'Q3', 'Q4']):
                    annual_record = record
                # Check for quarterly records
                elif (record.form_type == '10-Q' and 
                      period_type in ['Q1', 'Q2', 'Q3', 'Q4']):
                    quarterly_records.append(record)
                    if (record.revenue is None and 
                        record.net_income is None and 
                        record.operating_income is None):
                        incomplete_records.append(record)
            
            if annual_record and len(quarterly_records) >= 3 and len(incomplete_records) > 0:
                for incomplete_record in incomplete_records:
                    complete_quarterly_records = [
                        q for q in quarterly_records 
                        if q != incomplete_record and q.revenue is not None
                    ]
                    complete_quarterly_records.sort(key=lambda x: x.date)
                                        
                    pure_quarterly_values = {}
                    income_statement_fields = [
                        'revenue', 'cost_of_revenue', 'gross_profit', 'operating_income', 
                        'net_income', 'research_and_development', 'selling_general_admin'
                    ]
                    cash_flow_fields = [
                        'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow',
                        'capital_expenditures'
                    ]
                    
                    for field in income_statement_fields + cash_flow_fields:
                        pure_quarterly_values[field] = []
                        for i, record in enumerate(complete_quarterly_records):
                            current_value = getattr(record, field, 0) or 0
                            if i == 0:
                                pure_value = current_value
                            else:
                                previous_cumulative = getattr(complete_quarterly_records[i-1], field, 0) or 0
                                pure_value = current_value - previous_cumulative
                            pure_quarterly_values[field].append(pure_value)
                    
                    for field in income_statement_fields + cash_flow_fields:
                        annual_value = getattr(annual_record, field, None)
                        if annual_value is not None and field in pure_quarterly_values:
                            pure_quarters_sum = sum(pure_quarterly_values[field])
                            imputed_value = annual_value - pure_quarters_sum
                            setattr(incomplete_record, field, imputed_value)
                                                        
        return imputed_records
    
    def _extract_period_type(self, period: str) -> str:
        """
        Extract the period type from a period string that may include year.
        
        Args:
            period (str): Period string (e.g., "2024 Q1", "Q1", "2024 FY", "FY").
        
        Returns:
            str: Period type (Q1, Q2, Q3, Q4, FY, or original if no match).
        """
        if not period:
            return ""
        
        # Handle year-prefixed periods (e.g., "2024 Q1", "2024 FY")
        if ' ' in period:
            parts = period.split()
            if len(parts) >= 2:
                # Return the last part which should be the period type
                return parts[-1]
        
        # Handle direct period strings (e.g., "Q1", "FY")
        return period
    
    def _is_annual_period(self, period: str) -> bool:
        """
        Check if a period represents an annual/full-year period.
        
        Args:
            period (str): Period string.
        
        Returns:
            bool: True if annual period, False otherwise.
        """
        period_type = self._extract_period_type(period)
        return period_type in ['FY', 'Q4']  # Some companies use Q4 for annual
    
    def _is_quarterly_period(self, period: str) -> bool:
        """
        Check if a period represents a quarterly period.
        
        Args:
            period (str): Period string.
        
        Returns:
            bool: True if quarterly period, False otherwise.
        """
        period_type = self._extract_period_type(period)
        return period_type in ['Q1', 'Q2', 'Q3', 'Q4']
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean a pandas DataFrame of financial data.
        
        Args:
            df (pd.DataFrame): Financial data DataFrame.
        
        Returns:
            pd.DataFrame: Cleaned DataFrame.
        """
        if df.empty:
            return df
            
        df = self._normalize_dates(df)
        df = self._remove_duplicate_rows(df)
        
        return df
    
    def _clean_individual_record(self, record: FinancialRecord) -> Optional[FinancialRecord]:
        """
        Clean an individual financial record with enhanced validation.
        
        Args:
            record (FinancialRecord): Financial record to clean.
        
        Returns:
            Optional[FinancialRecord]: Cleaned record or None if invalid.
        """
        try:
            record_dict = record.to_dict() if hasattr(record, 'to_dict') else record.__dict__.copy()
            
            if not self._validate_date(record_dict.get('date')):
                if self.strict_validation:
                    print(f"Invalid date for {record_dict.get('ticker')}: {record_dict.get('date')}")
                    return None
                else:
                    record_dict['date'] = self._normalize_date(record_dict.get('date'))
            
            self._calculate_missing_metrics(record_dict)
            
            if hasattr(FinancialRecord, 'from_dict'):
                return FinancialRecord.from_dict(record_dict)
            else:
                return FinancialRecord(**record_dict)
                
        except Exception as e:
            print(f"Error cleaning record for {record.ticker}: {e}")
            return None
    
    def _remove_duplicate_records(self, records: List[FinancialRecord]) -> List[FinancialRecord]:
        """
        Remove duplicate records based on ticker, date, and form_type.
        
        Args:
            records (List[FinancialRecord]): List of financial records.
        
        Returns:
            List[FinancialRecord]: Deduplicated records.
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
        
        Args:
            record_dict (dict): Financial record data.
        """
        if (record_dict.get('gross_profit') is None and 
            record_dict.get('revenue') is not None and 
            record_dict.get('cost_of_revenue') is not None):
            record_dict['gross_profit'] = record_dict['revenue'] - record_dict['cost_of_revenue']
        
        if (record_dict.get('working_capital') is None and 
            record_dict.get('current_assets') is not None and 
            record_dict.get('current_liabilities') is not None):
            record_dict['working_capital'] = record_dict['current_assets'] - record_dict['current_liabilities']
    
    def _normalize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize dates in DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame containing financial records.
        
        Returns:
            pd.DataFrame: DataFrame with normalized dates.
        """
        if 'date' in df.columns:
            df['date'] = df['date'].apply(self._normalize_date)
        return df
    
    def _remove_duplicate_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate rows from DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame containing financial records.
        
        Returns:
            pd.DataFrame: DataFrame without duplicate rows.
        """
        return df.drop_duplicates()
    
    def _validate_date(self, date_val: Any) -> bool:
        """
        Validate if date is in acceptable format.
        
        Args:
            date_val (Any): Date value to validate.
        
        Returns:
            bool: True if valid, False otherwise.
        """
        if date_val is None:
            return False
        
        try:
            if isinstance(date_val, str):
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        datetime.strptime(date_val, fmt)
                        return True
                    except ValueError:
                        continue
                return False
            elif isinstance(date_val, (datetime, pd.Timestamp)):
                return True
            return False
        except Exception:
            return False
    
    def _normalize_date(self, date_val: Any) -> Optional[str]:
        """
        Normalize date to standard format.
        
        Args:
            date_val (Any): Date value to normalize.
        
        Returns:
            Optional[str]: Normalized date in YYYY-MM-DD format or None if invalid.
        """
        if date_val is None:
            return None
        
        try:
            if isinstance(date_val, str):
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        dt = datetime.strptime(date_val, fmt)
                        return dt.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            elif isinstance(date_val, (datetime, pd.Timestamp)):
                return date_val.strftime('%Y-%m-%d')
        except Exception:
            pass
        
        return None