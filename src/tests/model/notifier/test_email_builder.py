import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from src.model.notifier.email_builder import EmailBuilder


class TestEmailBuilder:
    
    @pytest.fixture
    def builder(self):
        with patch('src.model.notifier.email_builder.LoggerSetup'):
            return EmailBuilder()
    
    @pytest.fixture
    def sample_stock_data(self):
        dates = pd.date_range(start='2024-01-01', periods=252, freq='D')
        return pd.DataFrame({
            'Close': np.linspace(100, 120, 252),
            'Volume': np.random.randint(1000000, 5000000, 252)
        }, index=dates)
    
    @pytest.fixture
    def sample_earnings_df(self):
        return pd.DataFrame({
            'fiscalDateEnding': ['2024-01-01', '2024-04-01'],
            'reportedEPS': [1.5, 1.6],
            'estimatedEPS': [1.4, 1.5],
            'surprisePercentage': [7.14, 6.67],
            'oneDayReturn': [2.5, 3.0],
            'fiveDayReturn': [5.0, 6.0]
        })
    
    def test_init(self):
        with patch('src.model.notifier.email_builder.LoggerSetup'):
            builder = EmailBuilder()
            assert len(builder.raw_df_mappings) > 0
            assert len(builder.metrics_df_mappings) > 0
            assert builder.news_limit == 5
            assert builder.news_summary_chars == 220
    
    @patch('src.model.notifier.email_builder.yf.Ticker')
    def test_fetch_stock_data_success(self, mock_yf, builder, sample_stock_data):
        mock_ticker = Mock()
        mock_ticker.history.return_value = sample_stock_data
        mock_yf.return_value = mock_ticker
        
        result = builder.fetch_stock_data('AAPL')
        
        assert not result.empty
        assert len(result) == 252
    
    @patch('src.model.notifier.email_builder.yf.Ticker')
    def test_fetch_stock_data_empty(self, mock_yf, builder):
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_yf.return_value = mock_ticker
        
        result = builder.fetch_stock_data('AAPL')
        
        assert result.empty
    
    @patch('src.model.notifier.email_builder.yf.Ticker')
    def test_fetch_stock_data_exception(self, mock_yf, builder):
        mock_yf.side_effect = Exception("API Error")
        
        result = builder.fetch_stock_data('AAPL')
        
        assert result.empty
    
    def test_get_stock_performance_data_success(self, builder, sample_stock_data):
        result = builder.get_stock_performance_data(sample_stock_data)
        
        assert result['current_price'] is not None
        assert result['year_ago_price'] is not None
        assert result['price_change_pct'] is not None
    
    def test_get_stock_performance_data_empty(self, builder):
        result = builder.get_stock_performance_data(pd.DataFrame())
        
        assert result['current_price'] is None
        assert result['year_ago_price'] is None
    
    def test_format_numeric_value_large_numbers(self, builder):
        assert builder._format_numeric_value(1500000000000) == "1.5T"
        assert builder._format_numeric_value(2500000000) == "2.5B"
        assert builder._format_numeric_value(3500000) == "3.5M"
        assert builder._format_numeric_value(4500) == "4.5K"
    
    def test_format_numeric_value_small_numbers(self, builder):
        assert builder._format_numeric_value(100) == "100"
        assert builder._format_numeric_value(3.14) == "3.14"
    
    def test_format_numeric_value_none_nan(self, builder):
        assert pd.isna(builder._format_numeric_value(None))
        assert pd.isna(builder._format_numeric_value(np.nan))
    
    def test_format_dataframe(self, builder):
        df = pd.DataFrame({
            'revenue': [1000000, 2000000],
            'name': ['Test1', 'Test2']
        })
        
        result = builder.format_dataframe(df)
        
        assert result['revenue'].iloc[0] == '1M'
    
    def test_format_column_headers(self, builder):
        df = pd.DataFrame({'snake_case_column': [1, 2]})
        
        result = builder.format_column_headers(df)
        
        assert 'Snake Case Column' in result.columns
    
    def test_format_raw_df(self, builder):
        df = pd.DataFrame({
            'date': ['2024-01-01'],
            'form_type': ['10-Q'],
            'cost_of_revenue': [60000]
        })
        
        result = builder.format_raw_df(df)
        
        assert 'date' not in result.columns
        assert 'form_type' not in result.columns
        assert 'COGS' in result.columns
    
    def test_format_metrics_df(self, builder):
        df = pd.DataFrame({'working_capital': [70000]})
        
        result = builder.format_metrics_df(df)
        
        assert 'WC' in result.columns
    
    def test_rename_columns(self, builder):
        df = pd.DataFrame({'old_name': [1, 2]})
        mapping = {'old_name': 'New Name'}
        
        result = builder.rename_columns(df, mapping)
        
        assert 'New Name' in result.columns
    
    def test_get_performance_class(self, builder):
        assert builder.get_performance_class(10.0) == "performance-positive"
        assert builder.get_performance_class(-10.0) == "performance-negative"
        assert builder.get_performance_class(0.0) == "performance-neutral"
    
    def test_create_introduction_html(self, builder):
        result = builder._create_introduction_html('AAPL')
        
        assert 'AAPL' in result
        assert 'intro-section' in result
    
    def test_create_stock_header(self, builder):
        performance = {
            'current_price': 150.0,
            'price_change_pct': 10.5
        }
        
        result = builder._create_stock_header('AAPL', performance)
        
        assert 'AAPL' in result
        assert '$150.00' in result
        assert '+10.50%' in result
    
    def test_create_stock_header_missing_data(self, builder):
        performance = {'current_price': None, 'price_change_pct': None}
        
        result = builder._create_stock_header('AAPL', performance)
        
        assert result == 'AAPL'
    
    def test_create_chart_html(self, builder):
        result = builder._create_chart_html('chart_id', 'AAPL')
        
        assert 'cid:chart_id' in result
        assert 'AAPL' in result
    
    def test_create_chart_html_no_content_id(self, builder):
        result = builder._create_chart_html(None, 'AAPL')
        
        assert result == ""
    
    @patch('src.model.notifier.email_builder.pio.to_image')
    def test_create_chart_attachment_success(self, mock_to_image, builder, sample_stock_data):
        mock_to_image.return_value = b'fake_image_data'
        
        img_bytes, content_id = builder.create_chart_attachment('AAPL', sample_stock_data)
        
        assert img_bytes == b'fake_image_data'
        assert content_id == 'stock_chart_aapl'
    
    def test_create_chart_attachment_empty_data(self, builder):
        img_bytes, content_id = builder.create_chart_attachment('AAPL', pd.DataFrame())
        
        assert img_bytes is None
        assert content_id is None
    
    def test_format_sentiment_analysis(self, builder):
        result = builder._format_sentiment_analysis(0.65, -0.45)
        
        assert 'Corporate Sentiment' in result
        assert 'Retail Sentiment' in result
        assert 'performance-positive' in result
        assert 'performance-negative' in result
    
    def test_get_sentiment_details_positive(self, builder):
        value, css_class = builder._get_sentiment_details(0.5)
        
        assert '+0.50' in value
        assert css_class == "performance-positive"
    
    def test_get_sentiment_details_negative(self, builder):
        value, css_class = builder._get_sentiment_details(-0.5)
        
        assert '-0.50' in value
        assert css_class == "performance-negative"
    
    def test_get_sentiment_details_neutral(self, builder):
        value, css_class = builder._get_sentiment_details(0.02)
        
        assert css_class == "performance-neutral"
    
    def test_format_sector_performance(self, builder):
        sector_data = {
            'sector': 'Technology',
            'sector_etf': 'XLK',
            'ticker_1y_performance_pct': 25.5,
            'sector_1y_performance_pct': 15.3
        }
        
        result = builder._format_sector_performance('AAPL', sector_data)
        
        assert 'Technology' in result
        assert 'XLK' in result
        assert '+25.50%' in result
    
    def test_format_sector_performance_no_data(self, builder):
        result = builder._format_sector_performance('AAPL', {'sector': 'Unknown'})
        
        assert 'not available' in result
    
    def test_format_earnings_analysis(self, builder, sample_earnings_df):
        earnings_estimate = {
            'nextEarningsDate': '2024-07-01',
            'estimatedEPS': 1.7,
            'forwardPE': 25.5,
            'pegRatio': 1.8
        }
        
        result = builder._format_earnings_analysis(sample_earnings_df, earnings_estimate)
        
        assert 'Historical Quarterly Earnings' in result
        assert 'Next Earnings Estimate' in result
    
    def test_format_earnings_analysis_no_data(self, builder):
        result = builder._format_earnings_analysis(pd.DataFrame(), {})
        
        assert 'No historical earnings data available' in result
    
    def test_prepare_earnings_display_df(self, builder, sample_earnings_df):
        result = builder._prepare_earnings_display_df(sample_earnings_df)
        
        assert 'Fiscal Date' in result.columns
        assert 'Reported EPS' in result.columns
    
    def test_format_earnings_date(self, builder):
        assert builder._format_earnings_date('2024-07-01') == '2024-07-01'
        assert builder._format_earnings_date(None) == 'N/A'
    
    def test_format_earnings_value(self, builder):
        assert builder._format_earnings_value(1.5) == '1.50'
        assert builder._format_earnings_value(None) == 'N/A'
    
    def test_build_news_html_success(self, builder):
        news_df = pd.DataFrame({
            'headline': ['Test Headline 1', 'Test Headline 2'],
            'summary': ['Summary 1', 'Summary 2'],
            'url': ['http://url1.com', 'http://url2.com'],
            'published_at': [datetime.now(), datetime.now()]
        })
        
        result = builder._build_news_html(news_df)
        
        assert 'Test Headline 1' in result
        assert 'news-list' in result
    
    def test_build_news_html_empty(self, builder):
        result = builder._build_news_html(pd.DataFrame())
        
        assert result == ""
    
    def test_format_single_news_item(self, builder):
        result = builder._format_single_news_item(
            'Test Headline', 
            'Test Summary', 
            'http://test.com'
        )
        
        assert 'Test Headline' in result
        assert 'Test Summary' in result
        assert 'http://test.com' in result
    
    def test_format_single_news_item_long_summary(self, builder):
        long_summary = 'a' * 300
        
        result = builder._format_single_news_item('Headline', long_summary, 'http://test.com')
        
        assert '…' in result
        assert len(result) < len(long_summary)
    
    def test_build_html_content(self, builder, sample_earnings_df):
        raw_df = pd.DataFrame({'revenue': [100000], 'period': ['Q1 2024']})
        metrics_df = pd.DataFrame({'gross_margin': [40.0], 'period': ['Q1 2024']})
        news_df = pd.DataFrame({'headline': ['Test'], 'summary': ['Summary'], 'url': ['http://test.com']})
        sector_data = {'sector': 'Technology', 'sector_etf': 'XLK', 'ticker_1y_performance_pct': 25.5, 'sector_1y_performance_pct': 15.3}
        earnings_estimate = {'nextEarningsDate': '2024-07-01', 'estimatedEPS': 1.7}
        
        with patch.object(builder, 'fetch_stock_data', return_value=pd.DataFrame()):
            with patch.object(builder, 'get_stock_performance_data', return_value=builder._empty_performance_dict()):
                with patch.object(builder, 'create_chart_attachment', return_value=(None, None)):
                    html, chart_data = builder.build_html_content(
                        raw_df, metrics_df, 'AAPL', 0.5, 0.3, news_df, 
                        sector_data, sample_earnings_df, earnings_estimate
                    )
        
        assert 'AAPL' in html
        assert 'Sentiment Analysis' in html
        assert 'Company Financials' in html
    
    def test_get_css_styles(self, builder):
        styles = builder._get_css_styles()
        
        assert 'body' in styles
        assert 'section-header' in styles
        assert 'performance-positive' in styles