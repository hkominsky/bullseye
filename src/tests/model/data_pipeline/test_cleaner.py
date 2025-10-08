import pytest
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime
from src.model.data_pipeline.sec_data_cleaner import SECDataCleaner
from src.model.utils.models import FinancialRecord


class TestSECDataCleaner:
    
    @pytest.fixture
    def cleaner(self):
        with patch('src.model.data_pipeline.sec_data_cleaner.LoggerSetup'):
            return SECDataCleaner(strict_validation=False)
    
    @pytest.fixture
    def strict_cleaner(self):
        with patch('src.model.data_pipeline.sec_data_cleaner.LoggerSetup'):
            return SECDataCleaner(strict_validation=True)
    
    @pytest.fixture
    def sample_record(self):
        return FinancialRecord(
            ticker='AAPL',
            date='2024-01-01',
            period='Q1 2024',
            form_type='10-Q',
            revenue=100000,
            net_income=20000,
            operating_income=25000,
            cost_of_revenue=60000,
            gross_profit=40000,
            current_assets=50000,
            current_liabilities=30000,
            working_capital=20000
        )
    
    def test_init_default_strict_validation(self):
        with patch('src.model.data_pipeline.sec_data_cleaner.LoggerSetup'):
            cleaner = SECDataCleaner()
            assert cleaner.strict_validation == False
    
    def test_init_with_strict_validation(self):
        with patch('src.model.data_pipeline.sec_data_cleaner.LoggerSetup'):
            cleaner = SECDataCleaner(strict_validation=True)
            assert cleaner.strict_validation == True
    
    def test_safe_float_valid_number(self, cleaner):
        assert cleaner._safe_float(3.14) == 3.14
        assert cleaner._safe_float(42) == 42.0
    
    def test_safe_float_none(self, cleaner):
        assert cleaner._safe_float(None) is None
    
    def test_safe_float_nan(self, cleaner):
        assert cleaner._safe_float(pd.NA) is None
        assert cleaner._safe_float(float('nan')) is None
    
    def test_extract_period_type_with_year(self, cleaner):
        assert cleaner._extract_period_type('2024 Q1') == 'Q1'
        assert cleaner._extract_period_type('2023 FY') == 'FY'
    
    def test_extract_period_type_without_year(self, cleaner):
        assert cleaner._extract_period_type('Q2') == 'Q2'
        assert cleaner._extract_period_type('FY') == 'FY'
    
    def test_extract_period_type_empty(self, cleaner):
        assert cleaner._extract_period_type('') == ''
        assert cleaner._extract_period_type(None) == ''
    
    def test_is_annual_period_fy(self, cleaner):
        assert cleaner._is_annual_period('FY') == True
        assert cleaner._is_annual_period('2024 FY') == True
    
    def test_is_annual_period_q4(self, cleaner):
        assert cleaner._is_annual_period('Q4') == True
        assert cleaner._is_annual_period('2024 Q4') == True
    
    def test_is_annual_period_quarterly(self, cleaner):
        assert cleaner._is_annual_period('Q1') == False
        assert cleaner._is_annual_period('Q2') == False
        assert cleaner._is_annual_period('Q3') == False
    
    def test_is_quarterly_period_valid(self, cleaner):
        assert cleaner._is_quarterly_period('Q1') == True
        assert cleaner._is_quarterly_period('Q2') == True
        assert cleaner._is_quarterly_period('Q3') == True
        assert cleaner._is_quarterly_period('Q4') == True
        assert cleaner._is_quarterly_period('2024 Q1') == True
    
    def test_is_quarterly_period_invalid(self, cleaner):
        assert cleaner._is_quarterly_period('FY') == False
        assert cleaner._is_quarterly_period('') == False
    
    def test_calculate_fiscal_year_before_october(self, cleaner):
        assert cleaner._calculate_fiscal_year('2024-05-15') == '2024'
        assert cleaner._calculate_fiscal_year('2024-01-01') == '2024'
        assert cleaner._calculate_fiscal_year('2024-09-30') == '2024'
    
    def test_calculate_fiscal_year_october_or_after(self, cleaner):
        assert cleaner._calculate_fiscal_year('2024-10-01') == '2025'
        assert cleaner._calculate_fiscal_year('2024-11-15') == '2025'
        assert cleaner._calculate_fiscal_year('2024-12-31') == '2025'
    
    def test_validate_date_valid_formats(self, cleaner):
        assert cleaner._validate_date('2024-01-01') == True
        assert cleaner._validate_date('2024/01/01') == True
        assert cleaner._validate_date('01/01/2024') == True
        assert cleaner._validate_date('2024-01-01 12:00:00') == True
    
    def test_validate_date_datetime_objects(self, cleaner):
        assert cleaner._validate_date(datetime(2024, 1, 1)) == True
        assert cleaner._validate_date(pd.Timestamp('2024-01-01')) == True
    
    def test_validate_date_invalid(self, cleaner):
        assert cleaner._validate_date(None) == False
        assert cleaner._validate_date('invalid-date') == False
        assert cleaner._validate_date(12345) == False
    
    def test_normalize_date_string_formats(self, cleaner):
        assert cleaner._normalize_date('2024-01-01') == '2024-01-01'
        assert cleaner._normalize_date('2024/01/15') == '2024-01-15'
        assert cleaner._normalize_date('03/20/2024') == '2024-03-20'
    
    def test_normalize_date_datetime_objects(self, cleaner):
        assert cleaner._normalize_date(datetime(2024, 1, 1)) == '2024-01-01'
        assert cleaner._normalize_date(pd.Timestamp('2024-06-15')) == '2024-06-15'
    
    def test_normalize_date_invalid(self, cleaner):
        assert cleaner._normalize_date(None) is None
        assert cleaner._normalize_date('invalid') is None
        assert cleaner._normalize_date(12345) is None
    
    def test_calculate_gross_profit_success(self, cleaner):
        record_dict = {'revenue': 100000, 'cost_of_revenue': 60000, 'gross_profit': None}
        result = cleaner._calculate_gross_profit(record_dict)
        assert result == True
        assert record_dict['gross_profit'] == 40000
    
    def test_calculate_gross_profit_already_exists(self, cleaner):
        record_dict = {'revenue': 100000, 'cost_of_revenue': 60000, 'gross_profit': 40000}
        result = cleaner._calculate_gross_profit(record_dict)
        assert result == False
        assert record_dict['gross_profit'] == 40000
    
    def test_calculate_gross_profit_missing_data(self, cleaner):
        record_dict = {'revenue': None, 'cost_of_revenue': 60000, 'gross_profit': None}
        result = cleaner._calculate_gross_profit(record_dict)
        assert result == False
    
    def test_calculate_working_capital_success(self, cleaner):
        record_dict = {'current_assets': 50000, 'current_liabilities': 30000, 'working_capital': None}
        result = cleaner._calculate_working_capital(record_dict)
        assert result == True
        assert record_dict['working_capital'] == 20000
    
    def test_calculate_working_capital_already_exists(self, cleaner):
        record_dict = {'current_assets': 50000, 'current_liabilities': 30000, 'working_capital': 20000}
        result = cleaner._calculate_working_capital(record_dict)
        assert result == False
    
    def test_calculate_working_capital_missing_data(self, cleaner):
        record_dict = {'current_assets': None, 'current_liabilities': 30000, 'working_capital': None}
        result = cleaner._calculate_working_capital(record_dict)
        assert result == False
    
    def test_is_annual_record_10k_fy(self, cleaner):
        record = FinancialRecord(ticker='AAPL', date='2024-01-01', period='FY', form_type='10-K')
        assert cleaner._is_annual_record(record, 'FY') == True
    
    def test_is_annual_record_10k_q4(self, cleaner):
        record = FinancialRecord(ticker='AAPL', date='2024-01-01', period='Q4', form_type='10-K')
        assert cleaner._is_annual_record(record, 'Q4') == True
    
    def test_is_annual_record_10q(self, cleaner):
        record = FinancialRecord(ticker='AAPL', date='2024-01-01', period='FY', form_type='10-Q')
        assert cleaner._is_annual_record(record, 'FY') == False
    
    def test_is_quarterly_record_10q(self, cleaner):
        record = FinancialRecord(ticker='AAPL', date='2024-01-01', period='Q1', form_type='10-Q')
        assert cleaner._is_quarterly_record(record, 'Q1') == True
    
    def test_is_quarterly_record_10k(self, cleaner):
        record = FinancialRecord(ticker='AAPL', date='2024-01-01', period='Q1', form_type='10-K')
        assert cleaner._is_quarterly_record(record, 'Q1') == False
    
    def test_is_incomplete_record_all_none(self, cleaner):
        record = FinancialRecord(
            ticker='AAPL', date='2024-01-01', period='Q1', form_type='10-Q',
            revenue=None, net_income=None, operating_income=None
        )
        assert cleaner._is_incomplete_record(record) == True
    
    def test_is_incomplete_record_has_revenue(self, cleaner):
        record = FinancialRecord(
            ticker='AAPL', date='2024-01-01', period='Q1', form_type='10-Q',
            revenue=100000, net_income=None, operating_income=None
        )
        assert cleaner._is_incomplete_record(record) == False
    
    def test_is_incomplete_record_has_net_income(self, cleaner):
        record = FinancialRecord(
            ticker='AAPL', date='2024-01-01', period='Q1', form_type='10-Q',
            revenue=None, net_income=20000, operating_income=None
        )
        assert cleaner._is_incomplete_record(record) == False
    
    def test_group_records_by_fiscal_year(self, cleaner):
        records = [
            FinancialRecord(ticker='AAPL', date='2024-01-01', period='Q1', form_type='10-Q'),
            FinancialRecord(ticker='AAPL', date='2024-05-01', period='Q2', form_type='10-Q'),
            FinancialRecord(ticker='AAPL', date='2023-11-01', period='Q4', form_type='10-K'),
        ]
        
        fiscal_years = cleaner._group_records_by_fiscal_year(records)
        
        assert '2024' in fiscal_years
        assert len(fiscal_years['2024']) == 3
    
    def test_group_records_by_fiscal_year_multiple_years(self, cleaner):
        records = [
            FinancialRecord(ticker='AAPL', date='2024-01-01', period='Q1', form_type='10-Q'),
            FinancialRecord(ticker='AAPL', date='2023-01-01', period='Q1', form_type='10-Q'),
        ]
        
        fiscal_years = cleaner._group_records_by_fiscal_year(records)
        
        assert '2024' in fiscal_years
        assert '2023' in fiscal_years
        assert len(fiscal_years['2024']) == 1
        assert len(fiscal_years['2023']) == 1
    
    def test_categorize_records_with_annual(self, cleaner):
        records = [
            FinancialRecord(ticker='AAPL', date='2024-01-01', period='FY', form_type='10-K', revenue=400000),
            FinancialRecord(ticker='AAPL', date='2024-03-01', period='Q1', form_type='10-Q', revenue=100000),
            FinancialRecord(ticker='AAPL', date='2024-06-01', period='Q2', form_type='10-Q', revenue=100000),
        ]
        
        annual, quarterly, incomplete = cleaner._categorize_records(records)
        
        assert annual is not None
        assert annual.form_type == '10-K'
        assert len(quarterly) == 2
    
    def test_categorize_records_with_incomplete(self, cleaner):
        records = [
            FinancialRecord(ticker='AAPL', date='2024-01-01', period='Q1', form_type='10-Q', revenue=None, net_income=None, operating_income=None),
            FinancialRecord(ticker='AAPL', date='2024-03-01', period='Q2', form_type='10-Q', revenue=100000),
        ]
        
        annual, quarterly, incomplete = cleaner._categorize_records(records)
        
        assert len(incomplete) == 1
        assert incomplete[0].revenue is None
    
    def test_can_impute_data_sufficient_data(self, cleaner):
        annual = FinancialRecord(ticker='AAPL', date='2024-01-01', period='FY', form_type='10-K', revenue=400000)
        quarterly = [
            FinancialRecord(ticker='AAPL', date='2024-03-01', period='Q1', form_type='10-Q', revenue=100000),
            FinancialRecord(ticker='AAPL', date='2024-06-01', period='Q2', form_type='10-Q', revenue=100000),
            FinancialRecord(ticker='AAPL', date='2024-09-01', period='Q3', form_type='10-Q', revenue=100000),
        ]
        incomplete = [FinancialRecord(ticker='AAPL', date='2024-12-01', period='Q4', form_type='10-Q', revenue=None)]
        
        assert cleaner._can_impute_data(annual, quarterly, incomplete) == True
    
    def test_can_impute_data_no_annual(self, cleaner):
        quarterly = [
            FinancialRecord(ticker='AAPL', date='2024-03-01', period='Q1', form_type='10-Q', revenue=100000),
            FinancialRecord(ticker='AAPL', date='2024-06-01', period='Q2', form_type='10-Q', revenue=100000),
            FinancialRecord(ticker='AAPL', date='2024-09-01', period='Q3', form_type='10-Q', revenue=100000),
        ]
        incomplete = [FinancialRecord(ticker='AAPL', date='2024-12-01', period='Q4', form_type='10-Q', revenue=None)]
        
        assert cleaner._can_impute_data(None, quarterly, incomplete) == False
    
    def test_can_impute_data_insufficient_quarterly(self, cleaner):
        annual = FinancialRecord(ticker='AAPL', date='2024-01-01', period='FY', form_type='10-K', revenue=400000)
        quarterly = [
            FinancialRecord(ticker='AAPL', date='2024-03-01', period='Q1', form_type='10-Q', revenue=100000),
            FinancialRecord(ticker='AAPL', date='2024-06-01', period='Q2', form_type='10-Q', revenue=100000),
        ]
        incomplete = [FinancialRecord(ticker='AAPL', date='2024-12-01', period='Q4', form_type='10-Q', revenue=None)]
        
        assert cleaner._can_impute_data(annual, quarterly, incomplete) == False
    
    def test_can_impute_data_no_incomplete(self, cleaner):
        annual = FinancialRecord(ticker='AAPL', date='2024-01-01', period='FY', form_type='10-K', revenue=400000)
        quarterly = [
            FinancialRecord(ticker='AAPL', date='2024-03-01', period='Q1', form_type='10-Q', revenue=100000),
            FinancialRecord(ticker='AAPL', date='2024-06-01', period='Q2', form_type='10-Q', revenue=100000),
            FinancialRecord(ticker='AAPL', date='2024-09-01', period='Q3', form_type='10-Q', revenue=100000),
        ]
        
        assert cleaner._can_impute_data(annual, quarterly, []) == False
    
    def test_get_complete_quarterly_records(self, cleaner):
        incomplete = FinancialRecord(ticker='AAPL', date='2024-12-01', period='Q4', form_type='10-Q', revenue=None)
        quarterly = [
            FinancialRecord(ticker='AAPL', date='2024-03-01', period='Q1', form_type='10-Q', revenue=100000),
            incomplete,
            FinancialRecord(ticker='AAPL', date='2024-06-01', period='Q2', form_type='10-Q', revenue=100000),
            FinancialRecord(ticker='AAPL', date='2024-09-01', period='Q3', form_type='10-Q', revenue=100000),
        ]
        
        complete = cleaner._get_complete_quarterly_records(quarterly, incomplete)
        
        assert len(complete) == 3
        assert incomplete not in complete
        assert complete[0].date == '2024-03-01'
    
    def test_calculate_pure_quarterly_values_first_quarter(self, cleaner):
        records = [
            FinancialRecord(ticker='AAPL', date='2024-03-01', period='Q1', form_type='10-Q', revenue=100000, net_income=20000),
        ]
        
        pure_values = cleaner._calculate_pure_quarterly_values(records)
        
        assert pure_values['revenue'][0] == 100000
        assert pure_values['net_income'][0] == 20000
    
    def test_calculate_pure_quarterly_values_cumulative(self, cleaner):
        records = [
            FinancialRecord(ticker='AAPL', date='2024-03-01', period='Q1', form_type='10-Q', revenue=100000, net_income=20000),
            FinancialRecord(ticker='AAPL', date='2024-06-01', period='Q2', form_type='10-Q', revenue=210000, net_income=45000),
        ]
        
        pure_values = cleaner._calculate_pure_quarterly_values(records)
        
        assert pure_values['revenue'][0] == 100000
        assert pure_values['revenue'][1] == 110000
        assert pure_values['net_income'][0] == 20000
        assert pure_values['net_income'][1] == 25000
    
    def test_impute_single_field_success(self, cleaner):
        incomplete = FinancialRecord(ticker='AAPL', date='2024-12-01', period='Q4', form_type='10-Q', revenue=None)
        annual = FinancialRecord(ticker='AAPL', date='2024-01-01', period='FY', form_type='10-K', revenue=400000)
        pure_values = {'revenue': [100000, 110000, 90000]}
        
        result = cleaner._impute_single_field(incomplete, annual, 'revenue', pure_values)
        
        assert result == True
        assert incomplete.revenue == 100000
    
    def test_impute_single_field_no_annual_value(self, cleaner):
        incomplete = FinancialRecord(ticker='AAPL', date='2024-12-01', period='Q4', form_type='10-Q', revenue=None)
        annual = FinancialRecord(ticker='AAPL', date='2024-01-01', period='FY', form_type='10-K', revenue=None)
        pure_values = {'revenue': [100000, 110000, 90000]}
        
        result = cleaner._impute_single_field(incomplete, annual, 'revenue', pure_values)
        
        assert result == False
        assert incomplete.revenue is None
    
    def test_get_imputable_fields(self, cleaner):
        fields = cleaner._get_imputable_fields()
        
        assert 'revenue' in fields
        assert 'net_income' in fields
        assert 'operating_income' in fields
        assert 'operating_cash_flow' in fields
        assert 'capital_expenditures' in fields
    
    def test_remove_duplicate_records(self, cleaner):
        records = [
            FinancialRecord(ticker='AAPL', date='2024-01-01', period='Q1', form_type='10-Q', revenue=100000),
            FinancialRecord(ticker='AAPL', date='2024-01-01', period='Q1', form_type='10-Q', revenue=100000),
            FinancialRecord(ticker='AAPL', date='2024-03-01', period='Q2', form_type='10-Q', revenue=110000),
        ]
        
        unique = cleaner._remove_duplicate_records(records)
        
        assert len(unique) == 2
    
    def test_remove_duplicate_records_no_duplicates(self, cleaner):
        records = [
            FinancialRecord(ticker='AAPL', date='2024-01-01', period='Q1', form_type='10-Q', revenue=100000),
            FinancialRecord(ticker='AAPL', date='2024-03-01', period='Q2', form_type='10-Q', revenue=110000),
        ]
        
        unique = cleaner._remove_duplicate_records(records)
        
        assert len(unique) == 2
    
    def test_clean_financial_records_empty_list(self, cleaner):
        result = cleaner.clean_financial_records([])
        assert result == []
    
    def test_clean_financial_records_single_record(self, cleaner, sample_record):
        result = cleaner.clean_financial_records([sample_record])
        assert len(result) == 1
    
    def test_clean_dataframe_empty(self, cleaner):
        df = pd.DataFrame()
        result = cleaner.clean_dataframe(df)
        assert result.empty
    
    def test_clean_dataframe_with_dates(self, cleaner):
        df = pd.DataFrame({
            'ticker': ['AAPL', 'AAPL'],
            'date': ['2024-01-01', '2024/03/15'],
            'revenue': [100000, 110000]
        })
        
        result = cleaner.clean_dataframe(df)
        
        assert result['date'].iloc[0] == '2024-01-01'
        assert result['date'].iloc[1] == '2024-03-15'
    
    def test_clean_dataframe_removes_duplicates(self, cleaner):
        df = pd.DataFrame({
            'ticker': ['AAPL', 'AAPL', 'AAPL'],
            'date': ['2024-01-01', '2024-01-01', '2024-03-15'],
            'revenue': [100000, 100000, 110000]
        })
        
        result = cleaner.clean_dataframe(df)
        
        assert len(result) == 2
    
    def test_process_date_validation_valid_date(self, cleaner):
        record_dict = {'ticker': 'AAPL', 'date': '2024-01-01'}
        result = cleaner._process_date_validation(record_dict)
        assert result == True
    
    def test_process_date_validation_invalid_date_strict(self, strict_cleaner):
        record_dict = {'ticker': 'AAPL', 'date': 'invalid'}
        result = strict_cleaner._process_date_validation(record_dict)
        assert result == False
    
    def test_process_date_validation_invalid_date_non_strict(self, cleaner):
        record_dict = {'ticker': 'AAPL', 'date': '01/15/2024'}
        result = cleaner._process_date_validation(record_dict)
        assert result == True
        assert record_dict['date'] == '2024-01-15'
    
    def test_impute_missing_quarterly_data_no_records(self, cleaner):
        result = cleaner.impute_missing_quarterly_data([], 'AAPL')
        assert result == []
    
    def test_impute_missing_quarterly_data_with_records(self, cleaner):
        records = [
            FinancialRecord(ticker='AAPL', date='2024-01-01', period='FY', form_type='10-K', revenue=400000),
            FinancialRecord(ticker='AAPL', date='2024-03-01', period='Q1', form_type='10-Q', revenue=100000),
            FinancialRecord(ticker='AAPL', date='2024-06-01', period='Q2', form_type='10-Q', revenue=210000),
            FinancialRecord(ticker='AAPL', date='2024-09-01', period='Q3', form_type='10-Q', revenue=300000),
            FinancialRecord(ticker='AAPL', date='2024-12-01', period='Q4', form_type='10-Q', revenue=None, net_income=None, operating_income=None),
        ]
        
        result = cleaner.impute_missing_quarterly_data(records, 'AAPL')
        
        assert len(result) == 5
        assert result[4].revenue == 100000