import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from src.model.data_pipeline.sector_performance import SectorPerformance, SECTOR_ETF_MAP


class TestSectorPerformance:
    
    @pytest.fixture
    def mock_yf_ticker(self):
        with patch('src.model.data_pipeline.sector_performance.yf.Ticker') as mock:
            yield mock
    
    @pytest.fixture
    def mock_yf_download(self):
        with patch('src.model.data_pipeline.sector_performance.yf.download') as mock:
            yield mock
    
    def test_init_success(self, mock_yf_ticker):
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'sector': 'Technology'}
        mock_yf_ticker.return_value = mock_ticker_instance
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            sp = SectorPerformance('AAPL')
        
        assert sp.ticker == 'AAPL'
        assert sp.sector == 'Technology'
        assert sp.sector_etf == 'XLK'
    
    def test_init_no_sector(self, mock_yf_ticker):
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {}
        mock_yf_ticker.return_value = mock_ticker_instance
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            with pytest.raises(ValueError, match="Could not find sector"):
                SectorPerformance('INVALID')
    
    def test_init_unmapped_sector(self, mock_yf_ticker):
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'sector': 'Unknown Sector'}
        mock_yf_ticker.return_value = mock_ticker_instance
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            with pytest.raises(ValueError, match="No ETF mapping found"):
                SectorPerformance('TEST')
    
    def test_get_sector_success(self, mock_yf_ticker):
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'sector': 'Healthcare'}
        mock_yf_ticker.return_value = mock_ticker_instance
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            sp = SectorPerformance('JNJ')
        
        assert sp._get_sector('JNJ') == 'Healthcare'
    
    def test_get_sector_error(self, mock_yf_ticker):
        mock_yf_ticker.side_effect = Exception("API Error")
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            with pytest.raises(Exception):
                sp = SectorPerformance('AAPL')
    
    def test_get_sector_etf_technology(self):
        with patch('src.model.data_pipeline.sector_performance.yf.Ticker') as mock_yf:
            mock_ticker = Mock()
            mock_ticker.info = {'sector': 'Technology'}
            mock_yf.return_value = mock_ticker
            
            with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
                sp = SectorPerformance('AAPL')
                assert sp._get_sector_etf() == 'XLK'
    
    def test_get_sector_etf_healthcare(self):
        with patch('src.model.data_pipeline.sector_performance.yf.Ticker') as mock_yf:
            mock_ticker = Mock()
            mock_ticker.info = {'sector': 'Healthcare'}
            mock_yf.return_value = mock_ticker
            
            with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
                sp = SectorPerformance('JNJ')
                assert sp._get_sector_etf() == 'XLV'
    
    def test_get_sector_etf_invalid_sector(self):
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            sp_mock = Mock(spec=SectorPerformance)
            sp_mock.sector = 'Invalid Sector'
            sp_mock._get_sector_etf = SectorPerformance._get_sector_etf.__get__(sp_mock)
            
            with pytest.raises(ValueError, match="No ETF mapping found"):
                sp_mock._get_sector_etf()
    
    def test_get_price_data_success(self, mock_yf_ticker, mock_yf_download):
        dates = pd.date_range('2023-01-01', periods=250, freq='D')
        prices = pd.Series(range(100, 350), index=dates)
        mock_yf_download.return_value = pd.DataFrame({'Close': prices})
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'sector': 'Technology'}
        mock_yf_ticker.return_value = mock_ticker_instance
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            sp = SectorPerformance('AAPL')
            result = sp._get_price_data('AAPL', datetime(2023, 1, 1), datetime(2023, 12, 31))
        
        assert len(result) == 250
        assert result.iloc[0] == 100
    
    def test_get_price_data_no_close_column(self, mock_yf_ticker, mock_yf_download):
        mock_yf_download.return_value = pd.DataFrame({'Open': [100, 101, 102]})
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'sector': 'Technology'}
        mock_yf_ticker.return_value = mock_ticker_instance
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            sp = SectorPerformance('AAPL')
            
            with pytest.raises(ValueError, match="No Close column found"):
                sp._get_price_data('AAPL', datetime(2023, 1, 1), datetime(2023, 12, 31))
    
    def test_get_price_data_exception(self, mock_yf_ticker, mock_yf_download):
        mock_yf_download.side_effect = Exception("Download failed")
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'sector': 'Technology'}
        mock_yf_ticker.return_value = mock_ticker_instance
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            sp = SectorPerformance('AAPL')
            
            with pytest.raises(Exception):
                sp._get_price_data('AAPL', datetime(2023, 1, 1), datetime(2023, 12, 31))
    
    def test_calculate_performance_positive_return(self, mock_yf_ticker):
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'sector': 'Technology'}
        mock_yf_ticker.return_value = mock_ticker_instance
        
        dates = pd.date_range('2023-01-01', periods=250, freq='D')
        prices = pd.Series([100.0] + list(range(101, 350)), index=dates)
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            sp = SectorPerformance('AAPL')
            performance = sp._calculate_performance(prices, 'AAPL')
        
        assert performance == pytest.approx(249.0, rel=0.01)
    
    def test_calculate_performance_negative_return(self, mock_yf_ticker):
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'sector': 'Technology'}
        mock_yf_ticker.return_value = mock_ticker_instance
        
        dates = pd.date_range('2023-01-01', periods=250, freq='D')
        prices = pd.Series([200.0, 150.0] + [100.0] * 248, index=dates)
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            sp = SectorPerformance('AAPL')
            performance = sp._calculate_performance(prices, 'AAPL')
        
        assert performance == pytest.approx(-50.0, rel=0.01)
    
    def test_calculate_performance_no_change(self, mock_yf_ticker):
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'sector': 'Technology'}
        mock_yf_ticker.return_value = mock_ticker_instance
        
        dates = pd.date_range('2023-01-01', periods=250, freq='D')
        prices = pd.Series([100.0] * 250, index=dates)
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            sp = SectorPerformance('AAPL')
            performance = sp._calculate_performance(prices, 'AAPL')
        
        assert performance == pytest.approx(0.0, rel=0.01)
    
    def test_calculate_performance_insufficient_data(self, mock_yf_ticker):
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'sector': 'Technology'}
        mock_yf_ticker.return_value = mock_ticker_instance
        
        prices = pd.Series([100.0])
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            sp = SectorPerformance('AAPL')
            
            with pytest.raises(ValueError, match="Insufficient historical data"):
                sp._calculate_performance(prices, 'AAPL')
    
    def test_calculate_performance_empty_series(self, mock_yf_ticker):
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'sector': 'Technology'}
        mock_yf_ticker.return_value = mock_ticker_instance
        
        prices = pd.Series([], dtype=float)
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            sp = SectorPerformance('AAPL')
            
            with pytest.raises(ValueError, match="Insufficient historical data"):
                sp._calculate_performance(prices, 'AAPL')
    
    def test_get_sector_performance_success(self, mock_yf_ticker, mock_yf_download):
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'sector': 'Technology'}
        mock_yf_ticker.return_value = mock_ticker_instance
        
        dates = pd.date_range('2023-01-01', periods=250, freq='D')
        ticker_prices = pd.Series([100.0] + list(range(101, 350)), index=dates)
        etf_prices = pd.Series([50.0] + list(range(51, 300)), index=dates)
        
        mock_yf_download.side_effect = [
            pd.DataFrame({'Close': ticker_prices}),
            pd.DataFrame({'Close': etf_prices})
        ]
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            sp = SectorPerformance('AAPL')
            result = sp.get_sector_performance()
        
        assert result['ticker'] == 'AAPL'
        assert result['sector'] == 'Technology'
        assert result['sector_etf'] == 'XLK'
        assert 'ticker_1y_performance_pct' in result
        assert 'sector_1y_performance_pct' in result
        assert isinstance(result['ticker_1y_performance_pct'], (int, float))
        assert isinstance(result['sector_1y_performance_pct'], (int, float))
    
    def test_get_sector_performance_exception(self, mock_yf_ticker, mock_yf_download):
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'sector': 'Technology'}
        mock_yf_ticker.return_value = mock_ticker_instance
        
        mock_yf_download.side_effect = Exception("Download failed")
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            sp = SectorPerformance('AAPL')
            
            with pytest.raises(Exception):
                sp.get_sector_performance()
    
    def test_sector_etf_map_completeness(self):
        expected_sectors = [
            "Technology", "Financial Services", "Healthcare", "Energy",
            "Industrials", "Consumer Cyclical", "Consumer Defensive",
            "Utilities", "Real Estate", "Basic Materials", "Communication Services"
        ]
        
        for sector in expected_sectors:
            assert sector in SECTOR_ETF_MAP
            assert isinstance(SECTOR_ETF_MAP[sector], str)
            assert len(SECTOR_ETF_MAP[sector]) > 0
    
    def test_sector_etf_map_values(self):
        expected_mappings = {
            "Technology": "XLK",
            "Financial Services": "XLF",
            "Healthcare": "XLV",
            "Energy": "XLE",
            "Industrials": "XLI",
            "Consumer Cyclical": "XLY",
            "Consumer Defensive": "XLP",
            "Utilities": "XLU",
            "Real Estate": "XLRE",
            "Basic Materials": "XLB",
            "Communication Services": "XLC"
        }
        
        assert SECTOR_ETF_MAP == expected_mappings
    
    def test_get_sector_performance_rounds_results(self, mock_yf_ticker, mock_yf_download):
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'sector': 'Technology'}
        mock_yf_ticker.return_value = mock_ticker_instance
        
        dates = pd.date_range('2023-01-01', periods=250, freq='D')
        ticker_prices = pd.Series([100.0, 115.5555], index=dates[:2])
        etf_prices = pd.Series([50.0, 53.3333], index=dates[:2])
        
        mock_yf_download.side_effect = [
            pd.DataFrame({'Close': ticker_prices}),
            pd.DataFrame({'Close': etf_prices})
        ]
        
        with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
            sp = SectorPerformance('AAPL')
            result = sp.get_sector_performance()
        
        assert result['ticker_1y_performance_pct'] == round(15.5555, 2)
        assert result['sector_1y_performance_pct'] == round(6.6666, 2)
    
    def test_multiple_sectors(self, mock_yf_ticker, mock_yf_download):
        sectors_to_test = [
            ('AAPL', 'Technology', 'XLK'),
            ('JPM', 'Financial Services', 'XLF'),
            ('JNJ', 'Healthcare', 'XLV'),
            ('XOM', 'Energy', 'XLE')
        ]
        
        for ticker, sector, expected_etf in sectors_to_test:
            mock_ticker_instance = Mock()
            mock_ticker_instance.info = {'sector': sector}
            mock_yf_ticker.return_value = mock_ticker_instance
            
            with patch('src.model.data_pipeline.sector_performance.LoggerSetup'):
                sp = SectorPerformance(ticker)
                assert sp.sector == sector
                assert sp.sector_etf == expected_etf