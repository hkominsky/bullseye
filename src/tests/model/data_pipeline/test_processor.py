import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from dataclasses import replace
from src.model.data_pipeline.sec_data_processor import SECDataProcessor
from src.model.utils.models import FinancialRecord, GrowthMetrics


class TestSECDataProcessor:
    
    @pytest.fixture
    def processor(self):
        with patch('src.model.data_pipeline.sec_data_processor.LoggerSetup'):
            return SECDataProcessor()
    
    @pytest.fixture
    def sample_record(self):
        return FinancialRecord(
            ticker='AAPL',
            date='2024-01-01',
            period='Q1 2024',
            form_type='10-Q',
            revenue=100000000,
            cost_of_revenue=60000000,
            gross_profit=40000000,
            operating_income=25000000,
            net_income=20000000,
            total_assets=300000000,
            current_assets=150000000,
            cash_and_equivalents=50000000,
            accounts_receivable=20000000,
            inventory=10000000,
            current_liabilities=80000000,
            total_liabilities=120000000,
            long_term_debt=40000000,
            shareholders_equity=180000000,
            operating_cash_flow=30000000,
            capital_expenditures=5000000,
            shares_outstanding=1000000,
            weighted_average_shares=1000000
        )
    
    def test_init(self):
        with patch('src.model.data_pipeline.sec_data_processor.LoggerSetup'):
            processor = SECDataProcessor()
            assert processor.stock_price_cache == {}
    
    @patch('src.model.data_pipeline.sec_data_processor.yf.Ticker')
    def test_get_stock_price_for_date_exact_match(self, mock_yf, processor):
        mock_ticker = Mock()
        dates = pd.DatetimeIndex(['2024-01-01', '2024-01-02'])
        mock_ticker.history.return_value = pd.DataFrame({
            'Close': [150.0, 152.0]
        }, index=dates)
        mock_yf.return_value = mock_ticker
        
        price = processor.get_stock_price_for_date('AAPL', '2024-01-01')
        
        assert price == 150.0
    
    @patch('src.model.data_pipeline.sec_data_processor.yf.Ticker')
    def test_get_stock_price_for_date_fallback(self, mock_yf, processor):
        mock_ticker = Mock()
        dates = pd.DatetimeIndex(['2024-01-02', '2024-01-03'])
        mock_ticker.history.return_value = pd.DataFrame({
            'Close': [150.0, 152.0]
        }, index=dates)
        mock_yf.return_value = mock_ticker
        
        price = processor.get_stock_price_for_date('AAPL', '2024-01-01')
        
        assert price == 152.0
    
    @patch('src.model.data_pipeline.sec_data_processor.yf.Ticker')
    def test_get_stock_price_for_date_cached(self, mock_yf, processor):
        processor.stock_price_cache['AAPL_2024-01-01'] = 150.0
        
        price = processor.get_stock_price_for_date('AAPL', '2024-01-01')
        
        assert price == 150.0
        mock_yf.assert_not_called()
    
    @patch('src.model.data_pipeline.sec_data_processor.yf.Ticker')
    def test_get_stock_price_for_date_no_data(self, mock_yf, processor):
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_yf.return_value = mock_ticker
        
        price = processor.get_stock_price_for_date('AAPL', '2024-01-01')
        
        assert price is None
    
    @patch('src.model.data_pipeline.sec_data_processor.yf.Ticker')
    def test_get_stock_price_for_date_exception(self, mock_yf, processor):
        mock_yf.side_effect = Exception("API Error")
        
        price = processor.get_stock_price_for_date('AAPL', '2024-01-01')
        
        assert price is None
    
    def test_both_not_none_true(self, processor):
        data = {'key1': 10, 'key2': 20}
        assert processor._both_not_none(data, 'key1', 'key2') == True
    
    def test_both_not_none_one_none(self, processor):
        data = {'key1': 10, 'key2': None}
        assert processor._both_not_none(data, 'key1', 'key2') == False
    
    def test_both_not_none_both_none(self, processor):
        data = {'key1': None, 'key2': None}
        assert processor._both_not_none(data, 'key1', 'key2') == False
    
    def test_safe_divide_valid(self, processor):
        data = {'numerator': 100, 'denominator': 50}
        assert processor._safe_divide(data, 'numerator', 'denominator') == True
    
    def test_safe_divide_zero_denominator(self, processor):
        data = {'numerator': 100, 'denominator': 0}
        assert processor._safe_divide(data, 'numerator', 'denominator') == False
    
    def test_safe_divide_none_values(self, processor):
        data = {'numerator': None, 'denominator': 50}
        assert processor._safe_divide(data, 'numerator', 'denominator') == False
    
    def test_safe_divide_values_valid(self, processor):
        result = processor._safe_divide_values(100, 50)
        assert result == 2.0
    
    def test_safe_divide_values_zero_denominator(self, processor):
        result = processor._safe_divide_values(100, 0)
        assert result is None
    
    def test_safe_divide_values_none(self, processor):
        result = processor._safe_divide_values(None, 50)
        assert result is None
    
    def test_safe_ratio_valid(self, processor):
        result = processor._safe_ratio(100, 50)
        assert result == 2.0
    
    def test_safe_ratio_zero_denominator(self, processor):
        result = processor._safe_ratio(100, 0)
        assert result == 0
    
    def test_safe_ratio_none_values(self, processor):
        result = processor._safe_ratio(None, 50)
        assert result == 0
    
    def test_is_positive_true(self, processor):
        assert processor._is_positive(10) == True
    
    def test_is_positive_false(self, processor):
        assert processor._is_positive(-10) == False
        assert processor._is_positive(0) == False
        assert processor._is_positive(None) == False
    
    def test_is_above_threshold_true(self, processor):
        assert processor._is_above_threshold(10, 5) == True
    
    def test_is_above_threshold_false(self, processor):
        assert processor._is_above_threshold(3, 5) == False
        assert processor._is_above_threshold(None, 5) == False
    
    def test_is_below_threshold_true(self, processor):
        assert processor._is_below_threshold(3, 5) == True
    
    def test_is_below_threshold_false(self, processor):
        assert processor._is_below_threshold(10, 5) == False
        assert processor._is_below_threshold(None, 5) == False
    
    def test_calculate_derived_values_gross_profit(self, processor):
        data = {'revenue': 100000, 'cost_of_revenue': 60000}
        processor._calculate_derived_values(data)
        assert data['gross_profit'] == 40000
    
    def test_calculate_derived_values_working_capital(self, processor):
        data = {'current_assets': 150000, 'current_liabilities': 80000}
        processor._calculate_derived_values(data)
        assert data['working_capital'] == 70000
    
    def test_calculate_derived_values_free_cash_flow(self, processor):
        data = {'operating_cash_flow': 30000, 'capital_expenditures': 5000}
        processor._calculate_derived_values(data)
        assert data['free_cash_flow'] == 25000
    
    def test_calculate_margins_gross(self, processor):
        data = {'revenue': 100000, 'gross_profit': 40000}
        processor._calculate_margins(data)
        assert data['gross_margin'] == 40.0
    
    def test_calculate_margins_operating(self, processor):
        data = {'revenue': 100000, 'operating_income': 25000}
        processor._calculate_margins(data)
        assert data['operating_margin'] == 25.0
    
    def test_calculate_margins_net(self, processor):
        data = {'revenue': 100000, 'net_income': 20000}
        processor._calculate_margins(data)
        assert data['net_margin'] == 20.0
    
    def test_calculate_margins_zero_revenue(self, processor):
        data = {'revenue': 0, 'net_income': 20000}
        processor._calculate_margins(data)
        assert 'net_margin' not in data
    
    def test_calculate_ratios_current_ratio(self, processor):
        data = {'current_assets': 150000, 'current_liabilities': 80000, 'inventory': 10000}
        processor._calculate_ratios(data)
        assert data['current_ratio'] == 1.875
        assert data['quick_ratio'] == 1.75
    
    def test_calculate_ratios_debt_to_equity(self, processor):
        data = {'total_liabilities': 120000, 'shareholders_equity': 180000}
        processor._calculate_ratios(data)
        assert abs(data['debt_to_equity'] - 0.6667) < 0.001
    
    def test_calculate_ratios_roa(self, processor):
        data = {'net_income': 20000, 'total_assets': 300000}
        processor._calculate_ratios(data)
        assert abs(data['return_on_assets'] - 6.6667) < 0.001
    
    def test_calculate_ratios_roe(self, processor):
        data = {'net_income': 20000, 'shareholders_equity': 180000}
        processor._calculate_ratios(data)
        assert abs(data['return_on_equity'] - 11.1111) < 0.001
    
    def test_calculate_per_share_metrics_eps(self, processor):
        data = {'net_income': 20000000, 'weighted_average_shares': 1000000}
        processor._calculate_per_share_metrics_dict(data)
        assert data['earnings_per_share'] == 20.0
    
    def test_calculate_advanced_metrics_asset_turnover(self, processor):
        data = {'revenue': 100000, 'total_assets': 300000}
        processor._calculate_advanced_metrics_dict(data)
        assert abs(data['asset_turnover'] - 0.3333) < 0.001
    
    def test_calculate_advanced_metrics_inventory_turnover(self, processor):
        data = {'cost_of_revenue': 60000, 'inventory': 10000}
        processor._calculate_advanced_metrics_dict(data)
        assert data['inventory_turnover'] == 6.0
    
    def test_calculate_advanced_metrics_receivables_turnover(self, processor):
        data = {'revenue': 100000, 'accounts_receivable': 20000}
        processor._calculate_advanced_metrics_dict(data)
        assert data['receivables_turnover'] == 5.0
        assert data['days_sales_outstanding'] == 73.0
    
    def test_calculate_enterprise_value(self, processor):
        ev = processor._calculate_enterprise_value(1000000, 50000, 100000)
        assert ev == 950000
    
    def test_calculate_enterprise_value_no_market_cap(self, processor):
        ev = processor._calculate_enterprise_value(None, 50000, 100000)
        assert ev is None
    
    def test_calculate_ev_to_ebitda(self, processor):
        ratio = processor._calculate_ev_to_ebitda(1000000, 200000)
        assert ratio == 5.0
    
    def test_calculate_ev_to_ebitda_invalid(self, processor):
        ratio = processor._calculate_ev_to_ebitda(None, 200000)
        assert ratio is None
    
    def test_calculate_market_to_book_premium(self, processor):
        premium = processor._calculate_market_to_book_premium(1000000, 800000)
        assert premium == 25.0
    
    def test_calculate_market_to_book_premium_invalid(self, processor):
        premium = processor._calculate_market_to_book_premium(None, 800000)
        assert premium is None
    
    def test_calculate_altman_z_score(self, processor, sample_record):
        enhanced = replace(sample_record, working_capital=70000)
        z_score = processor._calculate_altman_z_score(enhanced)
        assert z_score is not None
        assert isinstance(z_score, float)
    
    def test_calculate_altman_z_score_no_assets(self, processor, sample_record):
        record = replace(sample_record, total_assets=None)
        z_score = processor._calculate_altman_z_score(record)
        assert z_score is None
    
    def test_calculate_piotroski_f_score(self, processor, sample_record):
        enhanced = replace(
            sample_record,
            net_income=20000000,
            operating_cash_flow=30000000,
            return_on_assets=10.0,
            current_ratio=2.0,
            debt_to_equity=0.3,
            asset_turnover=0.6,
            gross_margin=25.0
        )
        f_score = processor._calculate_piotroski_f_score(enhanced)
        assert f_score is not None
        assert 0 <= f_score <= 8
    
    def test_determine_trend_direction_increasing(self, processor):
        trend = processor._determine_trend_direction([10, 15, 20, 25])
        assert trend == "increasing"
    
    def test_determine_trend_direction_decreasing(self, processor):
        trend = processor._determine_trend_direction([25, 20, 15, 10])
        assert trend == "decreasing"
    
    def test_determine_trend_direction_stable(self, processor):
        trend = processor._determine_trend_direction([10, 15, 12, 18])
        assert trend == "stable"
    
    def test_determine_trend_direction_insufficient_data(self, processor):
        trend = processor._determine_trend_direction([10])
        assert trend == "stable"
    
    def test_calculate_period_growth_valid(self, processor):
        growth = processor._calculate_period_growth(110, 100)
        assert growth == 10.0
    
    def test_calculate_period_growth_negative(self, processor):
        growth = processor._calculate_period_growth(90, 100)
        assert growth == -10.0
    
    def test_calculate_period_growth_invalid(self, processor):
        growth = processor._calculate_period_growth(None, 100)
        assert growth is None
        growth = processor._calculate_period_growth(110, 0)
        assert growth is None
    
    def test_find_yoy_record_valid(self, processor):
        records = [FinancialRecord(ticker='AAPL', date=f'2024-0{i}-01', period=f'Q{i}') for i in range(1, 6)]
        yoy_record = processor._find_yoy_record(records, 4)
        assert yoy_record == records[0]
    
    def test_find_yoy_record_insufficient_data(self, processor):
        records = [FinancialRecord(ticker='AAPL', date=f'2024-0{i}-01', period=f'Q{i}') for i in range(1, 3)]
        yoy_record = processor._find_yoy_record(records, 1)
        assert yoy_record is None
    
    def test_extract_latest_financials(self, processor, sample_record):
        financials = processor._extract_latest_financials(sample_record)
        assert financials['revenue'] == 100000000
        assert financials['net_income'] == 20000000
        assert 'total_assets' in financials
    
    def test_extract_key_ratios(self, processor, sample_record):
        ratios = processor._extract_key_ratios(sample_record)
        assert 'gross_margin' in ratios
        assert 'current_ratio' in ratios
    
    def test_extract_market_metrics(self, processor, sample_record):
        metrics = processor._extract_market_metrics(sample_record)
        assert 'stock_price' in metrics
        assert 'market_cap' in metrics
    
    def test_create_financial_dataframe_empty(self, processor):
        df = processor.create_financial_dataframe({})
        assert df.empty
    
    def test_create_financial_dataframe_with_data(self, processor, sample_record):
        financial_data = {'AAPL': [sample_record]}
        with patch.object(processor, 'get_stock_price_for_date', return_value=150.0):
            df = processor.create_financial_dataframe(financial_data)
        
        assert not df.empty
        assert 'ticker' in df.columns
        assert len(df) == 1
    
    def test_create_split_dataframes_empty(self, processor):
        raw_df, metrics_df = processor.create_split_dataframes({})
        assert raw_df.empty
        assert metrics_df.empty
    
    def test_create_split_dataframes_with_data(self, processor, sample_record):
        financial_data = {'AAPL': [sample_record]}
        with patch.object(processor, 'get_stock_price_for_date', return_value=150.0):
            raw_df, metrics_df = processor.create_split_dataframes(financial_data)
        
        assert not raw_df.empty
        assert not metrics_df.empty
        assert 'ticker' in raw_df.columns
        assert 'ticker' in metrics_df.columns
    
    def test_calculate_growth_metrics_insufficient_data(self, processor):
        financial_data = {'AAPL': [FinancialRecord(ticker='AAPL', date='2024-01-01', period='Q1')]}
        growth_data = processor.calculate_growth_metrics(['AAPL'], financial_data)
        assert growth_data['AAPL'] == []
    
    def test_calculate_growth_metrics_with_data(self, processor):
        records = [
            FinancialRecord(ticker='AAPL', date='2024-01-01', period='Q1', revenue=100000, net_income=20000),
            FinancialRecord(ticker='AAPL', date='2024-04-01', period='Q2', revenue=110000, net_income=22000)
        ]
        financial_data = {'AAPL': records}
        growth_data = processor.calculate_growth_metrics(['AAPL'], financial_data)
        
        assert len(growth_data['AAPL']) == 1
        assert growth_data['AAPL'][0].ticker == 'AAPL'
    
    def test_calculate_qoq_growth(self, processor):
        current = FinancialRecord(ticker='AAPL', date='2024-04-01', period='Q2', revenue=110000, net_income=22000, operating_income=25000)
        previous = FinancialRecord(ticker='AAPL', date='2024-01-01', period='Q1', revenue=100000, net_income=20000, operating_income=23000)
        growth_metric = GrowthMetrics(ticker='AAPL', period='Q2')
        
        processor._calculate_qoq_growth(growth_metric, current, previous)
        
        assert growth_metric.revenue_growth_qoq == 10.0
        assert growth_metric.net_income_growth_qoq == 10.0
    
    def test_process_records_with_metrics(self, processor, sample_record):
        with patch.object(processor, 'get_stock_price_for_date', return_value=150.0):
            enhanced = processor.process_records_with_metrics([sample_record])
        
        assert len(enhanced) == 1
        assert enhanced[0].ticker == 'AAPL'
    
    def test_generate_financial_summary_no_data(self, processor):
        summary = processor.generate_financial_summary('AAPL', Mock(), [], [])
        assert 'error' in summary
    
    def test_generate_financial_summary_with_data(self, processor, sample_record):
        profile = Mock()
        profile.company_name = 'Apple Inc.'
        profile.industry = 'Technology'
        
        summary = processor.generate_financial_summary('AAPL', profile, [sample_record], [])
        
        assert 'company_info' in summary
        assert summary['company_info']['ticker'] == 'AAPL'
        assert 'latest_financials' in summary
        assert 'key_ratios' in summary