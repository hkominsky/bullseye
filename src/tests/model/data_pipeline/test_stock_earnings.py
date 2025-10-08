import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from src.model.data_pipeline.earnings_fetcher import EarningsFetcher


class TestEarningsFetcher:
    """Test suite for EarningsFetcher class"""
    
    @pytest.fixture
    def fetcher(self):
        """Create a fresh EarningsFetcher instance for each test"""
        with patch('src.model.data_pipeline.earnings_fetcher.load_dotenv'):
            return EarningsFetcher()
    
    @pytest.fixture
    def mock_yf_ticker(self):
        """Create a mock yfinance Ticker object"""
        mock_ticker = Mock()
        mock_ticker.info = {}
        mock_ticker.earnings_history = pd.DataFrame()
        mock_ticker.calendar = {}
        return mock_ticker
    
    def test_safe_float_with_valid_number(self, fetcher):
        """Test _safe_float with a valid number"""
        assert fetcher._safe_float(3.14) == 3.14
        assert fetcher._safe_float(42) == 42.0
        assert fetcher._safe_float("5.5") == 5.5
    
    def test_safe_float_with_none(self, fetcher):
        """Test _safe_float with None"""
        assert fetcher._safe_float(None) is None
    
    def test_safe_float_with_nan(self, fetcher):
        """Test _safe_float with NaN"""
        assert fetcher._safe_float(pd.NA) is None
        assert fetcher._safe_float(float('nan')) is None
    
    def test_calculate_surprise_percentage_positive(self, fetcher):
        """Test surprise percentage calculation with positive surprise"""
        result = fetcher._calculate_surprise_percentage(1.10, 1.00)
        assert result == 10.0
    
    def test_calculate_surprise_percentage_negative(self, fetcher):
        """Test surprise percentage calculation with negative surprise"""
        result = fetcher._calculate_surprise_percentage(0.90, 1.00)
        assert result == -10.0
    
    def test_calculate_surprise_percentage_zero_estimate(self, fetcher):
        """Test surprise percentage with zero estimate"""
        result = fetcher._calculate_surprise_percentage(1.00, 0)
        assert result is None
    
    def test_calculate_surprise_percentage_none_values(self, fetcher):
        """Test surprise percentage with None values"""
        assert fetcher._calculate_surprise_percentage(None, 1.00) is None
        assert fetcher._calculate_surprise_percentage(1.00, None) is None
    
    def test_calculate_return_percentage_positive(self, fetcher):
        """Test return percentage with price increase"""
        result = fetcher._calculate_return_percentage(100, 110)
        assert result == 10.0
    
    def test_calculate_return_percentage_negative(self, fetcher):
        """Test return percentage with price decrease"""
        result = fetcher._calculate_return_percentage(100, 90)
        assert result == -10.0
    
    def test_calculate_return_percentage_no_change(self, fetcher):
        """Test return percentage with no price change"""
        result = fetcher._calculate_return_percentage(100, 100)
        assert result == 0.0
    
    def test_get_earnings_date_index_exact_match(self, fetcher):
        """Test finding earnings date index with exact match"""
        dates = pd.DatetimeIndex(['2024-01-01', '2024-01-02', '2024-01-03'])
        history = pd.DataFrame({'Close': [100, 101, 102]}, index=dates)
        earnings_date = pd.Timestamp('2024-01-02')
        
        result = fetcher._get_earnings_date_index(history, earnings_date)
        assert result == 1
    
    def test_get_earnings_date_index_after_date(self, fetcher):
        """Test finding earnings date index when earnings is after all dates"""
        dates = pd.DatetimeIndex(['2024-01-01', '2024-01-02', '2024-01-03'])
        history = pd.DataFrame({'Close': [100, 101, 102]}, index=dates)
        earnings_date = pd.Timestamp('2024-01-04')
        
        result = fetcher._get_earnings_date_index(history, earnings_date)
        assert result is None
    
    def test_get_earnings_date_index_before_all_dates(self, fetcher):
        """Test finding earnings date index when earnings is before all dates"""
        dates = pd.DatetimeIndex(['2024-01-02', '2024-01-03', '2024-01-04'])
        history = pd.DataFrame({'Close': [100, 101, 102]}, index=dates)
        earnings_date = pd.Timestamp('2024-01-01')
        
        result = fetcher._get_earnings_date_index(history, earnings_date)
        assert result == 0
    
    def test_get_one_day_return_success(self, fetcher):
        """Test one day return calculation with sufficient data"""
        history = pd.DataFrame({'Close': [100, 105, 103, 108]})
        
        result = fetcher._get_one_day_return(history, 0, 100)
        assert result == 5.0
    
    def test_get_one_day_return_insufficient_data(self, fetcher):
        """Test one day return when index is at end of data"""
        history = pd.DataFrame({'Close': [100, 105]})
        
        result = fetcher._get_one_day_return(history, 1, 105)
        assert result is None
    
    def test_get_five_day_return_success(self, fetcher):
        """Test five day return calculation with sufficient data"""
        history = pd.DataFrame({'Close': [100, 101, 102, 103, 104, 110, 112]})
        
        result = fetcher._get_five_day_return(history, 0, 100)
        assert result == 10.0
    
    def test_get_five_day_return_uses_last_available(self, fetcher):
        """Test five day return uses last available price if insufficient data"""
        history = pd.DataFrame({'Close': [100, 101, 102]})
        
        result = fetcher._get_five_day_return(history, 0, 100)
        assert result == 2.0
    
    def test_get_five_day_return_insufficient_data(self, fetcher):
        """Test five day return with no data after earnings"""
        history = pd.DataFrame({'Close': [100]})
        
        result = fetcher._get_five_day_return(history, 0, 100)
        assert result is None
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_calculate_post_earnings_returns_success(self, mock_yf, fetcher):
        """Test successful calculation of post-earnings returns"""
        mock_stock = Mock()
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        mock_stock.history.return_value = pd.DataFrame({
            'Close': [100, 102, 105, 103, 106, 110, 108, 107, 109, 112]
        }, index=dates)
        
        earnings_date = pd.Timestamp('2024-01-01')
        one_day, five_day = fetcher._calculate_post_earnings_returns(mock_stock, earnings_date)
        
        assert one_day == 2.0
        assert five_day == 10.0
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_calculate_post_earnings_returns_empty_history(self, mock_yf, fetcher):
        """Test post-earnings returns with empty history"""
        mock_stock = Mock()
        mock_stock.history.return_value = pd.DataFrame()
        
        earnings_date = pd.Timestamp('2024-01-01')
        one_day, five_day = fetcher._calculate_post_earnings_returns(mock_stock, earnings_date)
        
        assert one_day is None
        assert five_day is None
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_calculate_post_earnings_returns_exception(self, mock_yf, fetcher):
        """Test post-earnings returns handles exceptions"""
        mock_stock = Mock()
        mock_stock.history.side_effect = Exception("API Error")
        
        earnings_date = pd.Timestamp('2024-01-01')
        one_day, five_day = fetcher._calculate_post_earnings_returns(mock_stock, earnings_date)
        
        assert one_day is None
        assert five_day is None
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_build_earnings_record_complete(self, mock_yf, fetcher):
        """Test building complete earnings record"""
        mock_stock = Mock()
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        mock_stock.history.return_value = pd.DataFrame({
            'Close': [100, 102, 105, 103, 106, 110, 108, 107, 109, 112]
        }, index=dates)
        
        row = pd.Series({'epsActual': 1.50, 'epsEstimate': 1.40})
        index = pd.Timestamp('2024-01-01')
        
        record = fetcher._build_earnings_record(index, row, mock_stock)
        
        assert record['fiscalDateEnding'] == '2024-01-01'
        assert record['reportedEPS'] == 1.50
        assert record['estimatedEPS'] == 1.40
        assert record['surprisePercentage'] is not None
        assert 'oneDayReturn' in record
        assert 'fiveDayReturn' in record
    
    def test_create_empty_dataframe(self, fetcher):
        """Test creation of empty DataFrame with correct columns"""
        df = fetcher._create_empty_dataframe()
        
        expected_columns = [
            'fiscalDateEnding', 'reportedEPS', 'estimatedEPS', 'surprisePercentage',
            'oneDayReturn', 'fiveDayReturn'
        ]
        assert list(df.columns) == expected_columns
        assert len(df) == 0
    
    def test_ensure_dataframe_columns_missing_columns(self, fetcher):
        """Test ensuring DataFrame has all required columns"""
        df = pd.DataFrame({
            'fiscalDateEnding': ['2024-01-01'],
            'reportedEPS': [1.5]
        })
        
        result = fetcher._ensure_dataframe_columns(df)
        
        expected_columns = [
            'fiscalDateEnding', 'reportedEPS', 'estimatedEPS', 'surprisePercentage',
            'oneDayReturn', 'fiveDayReturn'
        ]
        assert list(result.columns) == expected_columns
        assert pd.isna(result['estimatedEPS'].iloc[0])
    
    def test_ensure_dataframe_columns_all_present(self, fetcher):
        """Test ensuring columns when all are already present"""
        df = pd.DataFrame({
            'fiscalDateEnding': ['2024-01-01'],
            'reportedEPS': [1.5],
            'estimatedEPS': [1.4],
            'surprisePercentage': [7.14],
            'oneDayReturn': [2.0],
            'fiveDayReturn': [5.0]
        })
        
        result = fetcher._ensure_dataframe_columns(df)
        
        assert len(result.columns) == 6
        assert result['reportedEPS'].iloc[0] == 1.5
    
    def test_extract_earnings_date_from_dict_list(self, fetcher):
        """Test extracting earnings date from dict with list value"""
        calendar = {'Earnings Date': [pd.Timestamp('2024-06-15')]}
        
        result = fetcher._extract_earnings_date_from_dict(calendar)
        
        assert result == pd.Timestamp('2024-06-15')
    
    def test_extract_earnings_date_from_dict_single(self, fetcher):
        """Test extracting earnings date from dict with single value"""
        calendar = {'Date': pd.Timestamp('2024-06-15')}
        
        result = fetcher._extract_earnings_date_from_dict(calendar)
        
        assert result == pd.Timestamp('2024-06-15')
    
    def test_extract_earnings_date_from_dict_none(self, fetcher):
        """Test extracting earnings date when not in dict"""
        calendar = {'Other': 'value'}
        
        result = fetcher._extract_earnings_date_from_dict(calendar)
        
        assert result is None
    
    def test_extract_eps_estimate_from_dict_list(self, fetcher):
        """Test extracting EPS estimate from dict with list value"""
        calendar = {'Earnings Average': [1.50]}
        
        result = fetcher._extract_eps_estimate_from_dict(calendar)
        
        assert result == 1.50
    
    def test_extract_eps_estimate_from_dict_single(self, fetcher):
        """Test extracting EPS estimate from dict with single value"""
        calendar = {'EPS Estimate': 1.50}
        
        result = fetcher._extract_eps_estimate_from_dict(calendar)
        
        assert result == 1.50
    
    def test_extract_earnings_date_from_dataframe(self, fetcher):
        """Test extracting earnings date from DataFrame"""
        calendar = pd.DataFrame({'Earnings Date': [pd.Timestamp('2024-06-15')]})
        
        result = fetcher._extract_earnings_date_from_dataframe(calendar)
        
        assert result == pd.Timestamp('2024-06-15')
    
    def test_extract_eps_estimate_from_dataframe(self, fetcher):
        """Test extracting EPS estimate from DataFrame"""
        calendar = pd.DataFrame({'Earnings Average': [1.50]})
        
        result = fetcher._extract_eps_estimate_from_dataframe(calendar)
        
        assert result == 1.50
    
    def test_parse_calendar_data_dict(self, fetcher):
        """Test parsing calendar data in dict format"""
        calendar = {
            'Earnings Date': [pd.Timestamp('2024-06-15')],
            'Earnings Average': [1.50]
        }
        
        date, eps = fetcher._parse_calendar_data(calendar)
        
        assert date == pd.Timestamp('2024-06-15')
        assert eps == 1.50
    
    def test_parse_calendar_data_dataframe(self, fetcher):
        """Test parsing calendar data in DataFrame format"""
        calendar = pd.DataFrame({
            'Earnings Date': [pd.Timestamp('2024-06-15')],
            'EPS Estimate': [1.50]
        })
        
        date, eps = fetcher._parse_calendar_data(calendar)
        
        assert date == pd.Timestamp('2024-06-15')
        assert eps == 1.50
    
    def test_format_earnings_date_valid(self, fetcher):
        """Test formatting valid earnings date"""
        date = pd.Timestamp('2024-06-15')
        
        result = fetcher._format_earnings_date(date)
        
        assert result == '2024-06-15'
    
    def test_format_earnings_date_none(self, fetcher):
        """Test formatting None earnings date"""
        result = fetcher._format_earnings_date(None)
        
        assert result is None
    
    def test_get_forward_pe_from_info_direct(self, fetcher):
        """Test getting forward P/E from info dict"""
        info = {'forwardPE': 25.5}
        
        result = fetcher._get_forward_pe_from_info(info)
        
        assert result == 25.5
    
    def test_get_forward_pe_from_info_alternative(self, fetcher):
        """Test getting forward P/E from alternative keys"""
        info = {'trailingPE': 28.3}
        
        result = fetcher._get_forward_pe_from_info(info)
        
        assert result == 28.3
    
    def test_get_forward_pe_from_info_none(self, fetcher):
        """Test getting forward P/E when not available"""
        info = {}
        
        result = fetcher._get_forward_pe_from_info(info)
        
        assert result is None
    
    def test_get_peg_ratio_from_info_direct(self, fetcher):
        """Test getting PEG ratio from info dict"""
        info = {'pegRatio': 1.5}
        
        result = fetcher._get_peg_ratio_from_info(info)
        
        assert result == 1.5
    
    def test_get_peg_ratio_from_info_trailing(self, fetcher):
        """Test getting PEG ratio from trailing key"""
        info = {'trailingPegRatio': 1.8}
        
        result = fetcher._get_peg_ratio_from_info(info)
        
        assert result == 1.8
    
    def test_get_peg_ratio_from_info_none(self, fetcher):
        """Test getting PEG ratio when not available"""
        info = {}
        
        result = fetcher._get_peg_ratio_from_info(info)
        
        assert result is None
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_fetch_historical_success(self, mock_yf, fetcher):
        """Test successful fetch of historical earnings"""
        mock_stock = Mock()
        
        dates = pd.DatetimeIndex(['2024-01-01', '2023-10-01'])
        mock_stock.earnings_history = pd.DataFrame({
            'epsActual': [1.50, 1.40],
            'epsEstimate': [1.45, 1.38]
        }, index=dates)
        
        history_dates = pd.date_range('2024-01-01', periods=10, freq='D')
        mock_stock.history.return_value = pd.DataFrame({
            'Close': [100, 102, 105, 103, 106, 110, 108, 107, 109, 112]
        }, index=history_dates)
        
        mock_yf.return_value = mock_stock
        
        result = fetcher.fetch_historical('AAPL')
        
        assert 'quarterlyEarnings' in result
        assert len(result['quarterlyEarnings']) == 2
        assert result['quarterlyEarnings'][0]['fiscalDateEnding'] == '2024-01-01'
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_fetch_historical_no_data(self, mock_yf, fetcher):
        """Test fetch historical with no earnings data"""
        mock_stock = Mock()
        mock_stock.earnings_history = None
        mock_yf.return_value = mock_stock
        
        result = fetcher.fetch_historical('AAPL')
        
        assert result == {"quarterlyEarnings": []}
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_fetch_historical_exception(self, mock_yf, fetcher):
        """Test fetch historical handles exceptions"""
        mock_yf.side_effect = Exception("API Error")
        
        result = fetcher.fetch_historical('AAPL')
        
        assert result == {"quarterlyEarnings": []}
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_fetch_earnings_success(self, mock_yf, fetcher):
        """Test successful fetch of earnings DataFrame"""
        mock_stock = Mock()
        
        dates = pd.DatetimeIndex(['2024-01-01', '2023-10-01', '2023-07-01', '2023-04-01', '2023-01-01'])
        mock_stock.earnings_history = pd.DataFrame({
            'epsActual': [1.50, 1.40, 1.35, 1.30, 1.25],
            'epsEstimate': [1.45, 1.38, 1.33, 1.28, 1.23]
        }, index=dates)
        
        history_dates = pd.date_range('2024-01-01', periods=10, freq='D')
        mock_stock.history.return_value = pd.DataFrame({
            'Close': [100, 102, 105, 103, 106, 110, 108, 107, 109, 112]
        }, index=history_dates)
        
        mock_yf.return_value = mock_stock
        
        result = fetcher.fetch_earnings('AAPL', rows=4)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4
        assert 'fiscalDateEnding' in result.columns
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_fetch_earnings_no_data(self, mock_yf, fetcher):
        """Test fetch earnings with no data returns empty DataFrame"""
        mock_stock = Mock()
        mock_stock.earnings_history = None
        mock_yf.return_value = mock_stock
        
        result = fetcher.fetch_earnings('AAPL')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_fetch_earnings_custom_rows(self, mock_yf, fetcher):
        """Test fetch earnings with custom row count"""
        mock_stock = Mock()
        
        dates = pd.DatetimeIndex(['2024-01-01', '2023-10-01'])
        mock_stock.earnings_history = pd.DataFrame({
            'epsActual': [1.50, 1.40],
            'epsEstimate': [1.45, 1.38]
        }, index=dates)
        
        history_dates = pd.date_range('2024-01-01', periods=10, freq='D')
        mock_stock.history.return_value = pd.DataFrame({
            'Close': [100, 102, 105, 103, 106, 110, 108, 107, 109, 112]
        }, index=history_dates)
        
        mock_yf.return_value = mock_stock
        
        result = fetcher.fetch_earnings('AAPL', rows=1)
        
        assert len(result) == 1
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_fetch_next_earnings_success(self, mock_yf, fetcher):
        """Test successful fetch of next earnings date"""
        mock_stock = Mock()
        mock_stock.calendar = {
            'Earnings Date': [pd.Timestamp('2024-06-15')],
            'Earnings Average': [1.50]
        }
        mock_stock.info = {
            'forwardPE': 25.5,
            'pegRatio': 1.8
        }
        mock_yf.return_value = mock_stock
        
        result = fetcher.fetch_next_earnings('AAPL')
        
        assert result['nextEarningsDate'] == '2024-06-15'
        assert result['estimatedEPS'] == 1.50
        assert result['forwardPE'] == 25.5
        assert result['pegRatio'] == 1.8
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_fetch_next_earnings_no_calendar(self, mock_yf, fetcher):
        """Test fetch next earnings with no calendar data"""
        mock_stock = Mock()
        mock_stock.calendar = None
        mock_stock.info = {}
        mock_yf.return_value = mock_stock
        
        result = fetcher.fetch_next_earnings('AAPL')
        
        assert result['nextEarningsDate'] is None
        assert result['estimatedEPS'] is None
        assert result['forwardPE'] is None
        assert result['pegRatio'] is None
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_fetch_next_earnings_exception(self, mock_yf, fetcher):
        """Test fetch next earnings handles exceptions"""
        mock_yf.side_effect = Exception("API Error")
        
        result = fetcher.fetch_next_earnings('AAPL')
        
        assert result['nextEarningsDate'] is None
        assert result['estimatedEPS'] is None
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_fetch_valuation_metrics_success(self, mock_yf, fetcher):
        """Test successful fetch of valuation metrics"""
        mock_stock = Mock()
        mock_stock.info = {
            'forwardPE': 25.5,
            'pegRatio': 1.8
        }
        mock_yf.return_value = mock_stock
        
        result = fetcher.fetch_valuation_metrics('AAPL')
        
        assert result['forwardPE'] == 25.5
        assert result['pegRatio'] == 1.8
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_fetch_valuation_metrics_missing_data(self, mock_yf, fetcher):
        """Test fetch valuation metrics with missing data"""
        mock_stock = Mock()
        mock_stock.info = {}
        mock_yf.return_value = mock_stock
        
        result = fetcher.fetch_valuation_metrics('AAPL')
        
        assert result['forwardPE'] is None
        assert result['pegRatio'] is None
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_fetch_valuation_metrics_exception(self, mock_yf, fetcher):
        """Test fetch valuation metrics handles exceptions"""
        mock_yf.side_effect = Exception("API Error")
        
        result = fetcher.fetch_valuation_metrics('AAPL')
        
        assert result['forwardPE'] is None
        assert result['pegRatio'] is None
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_get_stock_ticker_uppercase(self, mock_yf, fetcher):
        """Test that ticker symbol is converted to uppercase"""
        fetcher._get_stock_ticker('aapl')
        
        mock_yf.assert_called_once_with('AAPL')
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_get_stock_ticker_already_uppercase(self, mock_yf, fetcher):
        """Test ticker symbol that's already uppercase"""
        fetcher._get_stock_ticker('MSFT')
        
        mock_yf.assert_called_once_with('MSFT')
    
    @patch('src.model.data_pipeline.earnings_fetcher.yf.Ticker')
    def test_process_earnings_history_sorts_descending(self, mock_yf, fetcher):
        """Test that earnings history is sorted in descending order by date"""
        mock_stock = Mock()
        
        dates = pd.DatetimeIndex(['2023-01-01', '2024-01-01', '2023-07-01'])
        earnings_history = pd.DataFrame({
            'epsActual': [1.25, 1.50, 1.35],
            'epsEstimate': [1.23, 1.45, 1.33]
        }, index=dates)
        
        history_dates = pd.date_range('2024-01-01', periods=10, freq='D')
        mock_stock.history.return_value = pd.DataFrame({
            'Close': [100, 102, 105, 103, 106, 110, 108, 107, 109, 112]
        }, index=history_dates)
        
        mock_yf.return_value = mock_stock
        
        result = fetcher._process_earnings_history(earnings_history, 'AAPL')
        
        assert result[0]['fiscalDateEnding'] == '2024-01-01'
        assert result[1]['fiscalDateEnding'] == '2023-07-01'
        assert result[2]['fiscalDateEnding'] == '2023-01-01'