import pytest
import pandas as pd
from datetime import date, datetime
from src.model.data_pipeline.database.data_validator import DataValidator


class TestDataValidator:
    
    @pytest.fixture
    def validator(self):
        with patch('src.model.data_pipeline.database.data_validator.LoggerSetup'):
            return DataValidator()
    
    def test_safe_decimal_valid_float(self):
        assert DataValidator.safe_decimal(3.14) == 3.14
        assert DataValidator.safe_decimal(10) == 10.0
        assert DataValidator.safe_decimal("5.5") == 5.5
    
    def test_safe_decimal_none(self):
        assert DataValidator.safe_decimal(None) is None
        assert DataValidator.safe_decimal(pd.NA) is None
        assert DataValidator.safe_decimal(float('nan')) is None
    
    def test_safe_decimal_invalid(self):
        assert DataValidator.safe_decimal("invalid") is None
        assert DataValidator.safe_decimal([1, 2, 3]) is None
    
    def test_safe_date_valid(self):
        result = DataValidator.safe_date("2024-01-01")
        assert result == date(2024, 1, 1)
        
        result = DataValidator.safe_date(datetime(2024, 1, 1))
        assert result == date(2024, 1, 1)
        
        result = DataValidator.safe_date(date(2024, 1, 1))
        assert result == date(2024, 1, 1)
    
    def test_safe_date_none(self):
        assert DataValidator.safe_date(None) is None
        assert DataValidator.safe_date(pd.NA) is None
    
    def test_safe_date_invalid(self):
        assert DataValidator.safe_date("invalid") is None
        assert DataValidator.safe_date(12345) is None
    
    def test_safe_bigint_valid(self):
        assert DataValidator.safe_bigint(100) == 100
        assert DataValidator.safe_bigint(3.7) == 3
        assert DataValidator.safe_bigint("42") == 42
    
    def test_safe_bigint_none(self):
        assert DataValidator.safe_bigint(None) is None
        assert DataValidator.safe_bigint(pd.NA) is None
    
    def test_safe_bigint_invalid(self):
        assert DataValidator.safe_bigint("invalid") is None
        assert DataValidator.safe_bigint([1, 2]) is None
    
    def test_safe_string_valid(self):
        assert DataValidator.safe_string("test") == "test"
        assert DataValidator.safe_string(123) == "123"
        assert DataValidator.safe_string(3.14) == "3.14"
    
    def test_safe_string_with_max_length(self):
        assert DataValidator.safe_string("hello world", 5) == "hello"
        assert DataValidator.safe_string("short", 10) == "short"
    
    def test_safe_string_none(self):
        assert DataValidator.safe_string(None) is None
        assert DataValidator.safe_string(pd.NA) is None
    
    def test_clean_dataframe_empty(self, validator):
        df = pd.DataFrame()
        result = validator.clean_dataframe(df)
        assert result.empty
    
    def test_clean_dataframe_removes_inf(self, validator):
        df = pd.DataFrame({'a': [1, float('inf'), 2], 'b': [3, float('-inf'), 5]})
        result = validator.clean_dataframe(df)
        assert pd.isna(result['a'].iloc[1])
        assert pd.isna(result['b'].iloc[1])
    
    def test_clean_dataframe_numeric_columns(self, validator):
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4.5, 5.5, 6.5]})
        result = validator.clean_dataframe(df)
        assert result['a'].iloc[0] == 1.0
        assert result['b'].iloc[0] == 4.5
    
    def test_clean_dataframe_date_columns(self, validator):
        df = pd.DataFrame({'date': ['2024-01-01', '2024-01-02'], 'value': [1, 2]})
        result = validator.clean_dataframe(df)
        assert isinstance(result['date'].iloc[0], date)
    
    def test_validate_ticker_data_package_all_valid(self, validator):
        is_valid, msg = validator.validate_ticker_data_package(
            corporate_sentiment=0.5,
            retail_sentiment=0.3,
            ticker_news_df=pd.DataFrame({'headline': ['test']}),
            sector_performance_data={'key': 'value'},
            earnings_df=pd.DataFrame({'eps': [1.5]}),
            raw_df=pd.DataFrame({'revenue': [100000]}),
            metrics_df=pd.DataFrame({'margin': [25.0]})
        )
        assert is_valid == True
        assert msg == ""
    
    def test_validate_ticker_data_package_empty_raw_df(self, validator):
        is_valid, msg = validator.validate_ticker_data_package(
            corporate_sentiment=0.5,
            retail_sentiment=0.3,
            ticker_news_df=pd.DataFrame({'headline': ['test']}),
            sector_performance_data={'key': 'value'},
            earnings_df=pd.DataFrame({'eps': [1.5]}),
            raw_df=pd.DataFrame(),
            metrics_df=pd.DataFrame({'margin': [25.0]})
        )
        assert is_valid == False
        assert "Raw financial data" in msg
    
    def test_validate_ticker_data_package_empty_metrics_df(self, validator):
        is_valid, msg = validator.validate_ticker_data_package(
            corporate_sentiment=0.5,
            retail_sentiment=0.3,
            ticker_news_df=pd.DataFrame({'headline': ['test']}),
            sector_performance_data={'key': 'value'},
            earnings_df=pd.DataFrame({'eps': [1.5]}),
            raw_df=pd.DataFrame({'revenue': [100000]}),
            metrics_df=pd.DataFrame()
        )
        assert is_valid == False
        assert "Metrics data" in msg
    
    def test_validate_ticker_data_package_invalid_sentiment(self, validator):
        is_valid, msg = validator.validate_ticker_data_package(
            corporate_sentiment=None,
            retail_sentiment=0.3,
            ticker_news_df=pd.DataFrame({'headline': ['test']}),
            sector_performance_data={'key': 'value'},
            earnings_df=pd.DataFrame({'eps': [1.5]}),
            raw_df=pd.DataFrame({'revenue': [100000]}),
            metrics_df=pd.DataFrame({'margin': [25.0]})
        )
        assert is_valid == False
        assert "Corporate sentiment" in msg
    
    def test_validate_ticker_data_package_invalid_sector_data(self, validator):
        is_valid, msg = validator.validate_ticker_data_package(
            corporate_sentiment=0.5,
            retail_sentiment=0.3,
            ticker_news_df=pd.DataFrame({'headline': ['test']}),
            sector_performance_data=None,
            earnings_df=pd.DataFrame({'eps': [1.5]}),
            raw_df=pd.DataFrame({'revenue': [100000]}),
            metrics_df=pd.DataFrame({'margin': [25.0]})
        )
        assert is_valid == False
        assert "Sector performance data" in msg
    
    def test_prepare_raw_financial_data_empty(self, validator):
        df = pd.DataFrame()
        result = validator.prepare_raw_financial_data('AAPL', df)
        assert result == []
    
    def test_prepare_raw_financial_data_valid(self, validator):
        df = pd.DataFrame({
            'date': ['2024-01-01'],
            'period': ['Q1 2024'],
            'form_type': ['10-Q'],
            'revenue': [100000],
            'cost_of_revenue': [60000],
            'gross_profit': [40000],
            'operating_income': [25000],
            'net_income': [20000],
            'total_assets': [300000],
            'current_assets': [150000],
            'cash_and_equivalents': [50000],
            'total_liabilities': [120000],
            'current_liabilities': [80000],
            'shareholders_equity': [180000]
        })
        
        result = validator.prepare_raw_financial_data('AAPL', df)
        
        assert len(result) == 1
        assert result[0][0] == 'AAPL'
        assert result[0][4] == 100000
    
    def test_prepare_metrics_data_empty(self, validator):
        df = pd.DataFrame()
        result = validator.prepare_metrics_data('AAPL', df)
        assert result == []
    
    def test_prepare_metrics_data_valid(self, validator):
        df = pd.DataFrame({
            'period': ['Q1 2024'],
            'working_capital': [70000],
            'asset_turnover': [0.33],
            'altman_z_score': [3.5],
            'piotroski_f_score': [7],
            'gross_margin': [40.0],
            'operating_margin': [25.0],
            'net_margin': [20.0],
            'current_ratio': [1.875],
            'quick_ratio': [1.75],
            'debt_to_equity': [0.67],
            'return_on_assets': [6.67],
            'return_on_equity': [11.11],
            'free_cash_flow': [25000],
            'earnings_per_share': [20.0],
            'book_value_per_share': [180.0],
            'revenue_per_share': [100.0],
            'cash_per_share': [50.0],
            'fcf_per_share': [25.0],
            'stock_price': [150.0],
            'market_cap': [150000000],
            'enterprise_value': [145000000],
            'price_to_earnings': [7.5],
            'price_to_book': [0.83],
            'price_to_sales': [1.5],
            'ev_to_revenue': [1.45],
            'ev_to_ebitda': [5.8],
            'price_to_fcf': [6.0],
            'market_to_book_premium': [25.0]
        })
        
        result = validator.prepare_metrics_data('AAPL', df)
        
        assert len(result) == 1
        assert result[0][0] == 'AAPL'
        assert result[0][1] == 'Q1 2024'
    
    def test_prepare_news_articles_data_empty(self, validator):
        df = pd.DataFrame()
        result = validator.prepare_news_articles_data('AAPL', df)
        assert result == []
    
    def test_prepare_news_articles_data_valid(self, validator):
        df = pd.DataFrame({
            'headline': ['Test Headline', 'Another Headline'],
            'summary': ['Test summary', 'Another summary'],
            'url': ['http://test1.com', 'http://test2.com'],
            'published_at': ['2024-01-01', '2024-01-02']
        })
        
        result = validator.prepare_news_articles_data('AAPL', df)
        
        assert len(result) == 2
        assert result[0][0] == 'AAPL'
        assert result[0][1] == 'Test Headline'
    
    def test_prepare_news_articles_data_truncates_long_headline(self, validator):
        df = pd.DataFrame({
            'headline': ['x' * 2000],
            'summary': ['summary'],
            'url': ['http://test.com'],
            'published_at': ['2024-01-01']
        })
        
        result = validator.prepare_news_articles_data('AAPL', df)
        
        assert len(result[0][1]) == 1000
    
    def test_prepare_earnings_data_empty(self, validator):
        df = pd.DataFrame()
        result = validator.prepare_earnings_data('AAPL', df)
        assert result == []
    
    def test_prepare_earnings_data_valid(self, validator):
        df = pd.DataFrame({
            'fiscalDateEnding': ['2024-01-01', '2024-04-01'],
            'reportedEPS': [1.5, 1.6],
            'estimatedEPS': [1.4, 1.5],
            'surprisePercentage': [7.14, 6.67],
            'oneDayReturn': [2.5, 3.0],
            'fiveDayReturn': [5.0, 6.0]
        })
        
        result = validator.prepare_earnings_data('AAPL', df)
        
        assert len(result) == 2
        assert result[0][0] == 'AAPL'
        assert result[0][2] == 1.5
    
    def test_prepare_raw_financial_data_handles_none(self, validator):
        df = pd.DataFrame({
            'date': ['2024-01-01'],
            'period': [None],
            'form_type': ['10-Q'],
            'revenue': [None],
            'cost_of_revenue': [60000]
        })
        
        result = validator.prepare_raw_financial_data('AAPL', df)
        
        assert result[0][2] is None
        assert result[0][4] is None
    
    def test_prepare_metrics_data_handles_none(self, validator):
        df = pd.DataFrame({
            'period': ['Q1 2024'],
            'working_capital': [None],
            'asset_turnover': [0.33]
        })
        
        result = validator.prepare_metrics_data('AAPL', df)
        
        assert result[0][2] is None
        assert result[0][3] == 0.33