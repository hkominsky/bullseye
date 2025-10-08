import pytest
import pandas as pd
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from datetime import datetime
from stocks.routes import (
    get_ticker_info,
    has_valid_price,
    has_sufficient_data,
    create_stock_suggestion,
    get_popular_stocks,
    matches_search_query,
    search_stocks,
    validate_stock,
    get_current_price,
    get_previous_close,
    calculate_price_changes,
    format_chart_data,
    get_next_earnings_date,
    get_stock_info,
    get_user_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    get_user_reserve,
    add_to_reserve,
    remove_from_reserve,
    move_watchlist_to_reserve,
    move_reserve_to_watchlist
)
from config.schemas import CustomEmailRequest, StockSuggestion


class TestTickerHelpers:
    
    @patch('stocks.routes.yf.Ticker')
    def test_get_ticker_info_success(self, mock_yf):
        mock_ticker = Mock()
        mock_ticker.get_info.return_value = {'symbol': 'AAPL', 'longName': 'Apple Inc.'}
        mock_yf.return_value = mock_ticker
        
        result = get_ticker_info('AAPL')
        
        assert result['symbol'] == 'AAPL'
    
    @patch('stocks.routes.yf.Ticker')
    def test_get_ticker_info_no_symbol(self, mock_yf):
        mock_ticker = Mock()
        mock_ticker.get_info.return_value = {}
        mock_yf.return_value = mock_ticker
        
        result = get_ticker_info('INVALID')
        
        assert result is None
    
    @patch('stocks.routes.yf.Ticker')
    def test_get_ticker_info_exception(self, mock_yf):
        mock_yf.side_effect = Exception("API Error")
        
        result = get_ticker_info('AAPL')
        
        assert result is None
    
    def test_has_valid_price_regular_market(self):
        info = {'regularMarketPrice': 150.0}
        assert has_valid_price(info) == True
    
    def test_has_valid_price_current_price(self):
        info = {'currentPrice': 150.0}
        assert has_valid_price(info) == True
    
    def test_has_valid_price_previous_close(self):
        info = {'previousClose': 150.0}
        assert has_valid_price(info) == True
    
    def test_has_valid_price_none(self):
        info = {}
        assert has_valid_price(info) == False
    
    def test_has_sufficient_data_valid(self):
        info = {'regularMarketPrice': 150.0, 'marketCap': 2000000000}
        is_valid, error = has_sufficient_data(info)
        assert is_valid == True
        assert error is None
    
    def test_has_sufficient_data_no_price(self):
        info = {'marketCap': 2000000000}
        is_valid, error = has_sufficient_data(info)
        assert is_valid == False
        assert "no valid price data" in error
    
    def test_has_sufficient_data_no_market_cap(self):
        info = {'regularMarketPrice': 150.0}
        is_valid, error = has_sufficient_data(info)
        assert is_valid == False
        assert "insufficient fundamental data" in error
    
    def test_create_stock_suggestion(self):
        info = {
            'symbol': 'AAPL',
            'longName': 'Apple Inc.',
            'exchange': 'NASDAQ'
        }
        
        result = create_stock_suggestion('AAPL', info)
        
        assert result.symbol == 'AAPL'
        assert result.name == 'Apple Inc.'
        assert result.exchange == 'NASDAQ'
    
    def test_get_popular_stocks(self):
        stocks = get_popular_stocks()
        
        assert 'AAPL' in stocks
        assert 'MSFT' in stocks
        assert 'TSLA' in stocks
        assert len(stocks) > 10
    
    def test_matches_search_query_starts_with(self):
        assert matches_search_query('AAPL', 'AA') == True
    
    def test_matches_search_query_contains(self):
        assert matches_search_query('AAPL', 'PL') == True
    
    def test_matches_search_query_no_match(self):
        assert matches_search_query('AAPL', 'XYZ') == False


class TestSearchStocks:
    
    @pytest.fixture
    def mock_user(self):
        return Mock()
    
    @pytest.mark.asyncio
    async def test_search_stocks_empty_query(self, mock_user):
        result = await search_stocks('', 10, mock_user)
        
        assert result.suggestions == []
    
    @pytest.mark.asyncio
    async def test_search_stocks_success(self, mock_user):
        with patch('stocks.routes.get_ticker_info') as mock_get_info:
            mock_get_info.return_value = {
                'symbol': 'AAPL',
                'longName': 'Apple Inc.',
                'regularMarketPrice': 150.0
            }
            
            result = await search_stocks('AA', 10, mock_user)
            
            assert len(result.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_search_stocks_respects_limit(self, mock_user):
        with patch('stocks.routes.get_ticker_info') as mock_get_info:
            mock_get_info.return_value = {
                'symbol': 'AAPL',
                'longName': 'Apple Inc.',
                'regularMarketPrice': 150.0
            }
            
            result = await search_stocks('A', 3, mock_user)
            
            assert len(result.suggestions) <= 3
    
    @pytest.mark.asyncio
    async def test_search_stocks_exception(self, mock_user):
        with patch('stocks.routes.get_ticker_info', side_effect=Exception("Error")):
            with pytest.raises(HTTPException) as exc_info:
                await search_stocks('AA', 10, mock_user)
            
            assert exc_info.value.status_code == 500


class TestValidateStock:
    
    @pytest.fixture
    def mock_user(self):
        return Mock()
    
    @pytest.mark.asyncio
    async def test_validate_stock_valid(self, mock_user):
        with patch('stocks.routes.get_ticker_info') as mock_get_info:
            mock_get_info.return_value = {
                'symbol': 'AAPL',
                'longName': 'Apple Inc.',
                'regularMarketPrice': 150.0,
                'marketCap': 2000000000
            }
            
            result = await validate_stock('AAPL', mock_user)
            
            assert result.valid == True
            assert result.symbol == 'AAPL'
    
    @pytest.mark.asyncio
    async def test_validate_stock_not_found(self, mock_user):
        with patch('stocks.routes.get_ticker_info', return_value=None):
            result = await validate_stock('INVALID', mock_user)
            
            assert result.valid == False
            assert "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_validate_stock_no_price_data(self, mock_user):
        with patch('stocks.routes.get_ticker_info') as mock_get_info:
            mock_get_info.return_value = {'symbol': 'TEST'}
            
            result = await validate_stock('TEST', mock_user)
            
            assert result.valid == False
            assert "no valid price data" in result.error


class TestPriceCalculations:
    
    def test_get_current_price_regular_market(self):
        info = {'regularMarketPrice': 150.0}
        assert get_current_price(info) == 150.0
    
    def test_get_current_price_current_price(self):
        info = {'currentPrice': 152.0}
        assert get_current_price(info) == 152.0
    
    def test_get_previous_close(self):
        info = {'regularMarketPreviousClose': 148.0}
        assert get_previous_close(info) == 148.0
    
    def test_calculate_price_changes(self):
        change, percent = calculate_price_changes(150.0, 148.0)
        
        assert change == 2.0
        assert percent == pytest.approx(1.35, rel=0.01)
    
    def test_calculate_price_changes_no_data(self):
        change, percent = calculate_price_changes(None, 148.0)
        
        assert change is None
        assert percent is None
    
    def test_format_chart_data(self):
        dates = pd.date_range('2024-01-01', periods=3, freq='D')
        hist = pd.DataFrame({'Close': [100, 105, 110]}, index=dates)
        
        result = format_chart_data(hist)
        
        assert len(result) == 3
        assert result[0]['price'] == 100.0
        assert 'timestamp' in result[0]


class TestWatchlistEndpoints:
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def mock_user(self):
        user = Mock()
        user.email = "test@example.com"
        user.get_watchlist_tickers.return_value = ["AAPL", "MSFT"]
        user.set_watchlist_tickers = Mock()
        return user
    
    @pytest.mark.asyncio
    async def test_get_user_watchlist_success(self, mock_user, mock_db):
        result = await get_user_watchlist(mock_user, mock_db)
        
        assert result["tickers"] == ["AAPL", "MSFT"]
        mock_db.refresh.assert_called_once_with(mock_user)
    
    @pytest.mark.asyncio
    async def test_get_user_watchlist_exception(self, mock_user, mock_db):
        mock_db.refresh.side_effect = Exception("DB Error")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_user_watchlist(mock_user, mock_db)
        
        assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_add_to_watchlist_new_ticker(self, mock_user, mock_db):
        result = await add_to_watchlist('TSLA', mock_user, mock_db)
        
        assert "TSLA" in result["tickers"]
        mock_user.set_watchlist_tickers.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_to_watchlist_existing_ticker(self, mock_user, mock_db):
        result = await add_to_watchlist('AAPL', mock_user, mock_db)
        
        assert "AAPL" in result["tickers"]
    
    @pytest.mark.asyncio
    async def test_add_to_watchlist_lowercase_converted(self, mock_user, mock_db):
        await add_to_watchlist('tsla', mock_user, mock_db)
        
        call_args = mock_user.set_watchlist_tickers.call_args[0][0]
        assert "TSLA" in call_args
    
    @pytest.mark.asyncio
    async def test_remove_from_watchlist_success(self, mock_user, mock_db):
        result = await remove_from_watchlist('AAPL', mock_user, mock_db)
        
        mock_user.set_watchlist_tickers.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_from_watchlist_not_in_list(self, mock_user, mock_db):
        result = await remove_from_watchlist('TSLA', mock_user, mock_db)
        
        assert "tickers" in result


class TestReserveEndpoints:
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def mock_user(self):
        user = Mock()
        user.email = "test@example.com"
        user.get_reserve_tickers.return_value = ["NVDA", "AMD"]
        user.set_reserve_tickers = Mock()
        return user
    
    @pytest.mark.asyncio
    async def test_get_user_reserve_success(self, mock_user, mock_db):
        result = await get_user_reserve(mock_user, mock_db)
        
        assert result["tickers"] == ["NVDA", "AMD"]
    
    @pytest.mark.asyncio
    async def test_add_to_reserve_success(self, mock_user, mock_db):
        result = await add_to_reserve('INTC', mock_user, mock_db)
        
        mock_user.set_reserve_tickers.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_from_reserve_success(self, mock_user, mock_db):
        result = await remove_from_reserve('NVDA', mock_user, mock_db)
        
        mock_user.set_reserve_tickers.assert_called_once()
        mock_db.commit.assert_called_once()


class TestMoveOperations:
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def mock_user(self):
        user = Mock()
        user.get_watchlist_tickers.return_value = ["AAPL", "MSFT"]
        user.get_reserve_tickers.return_value = ["NVDA"]
        user.set_watchlist_tickers = Mock()
        user.set_reserve_tickers = Mock()
        return user
    
    @pytest.mark.asyncio
    async def test_move_watchlist_to_reserve(self, mock_user, mock_db):
        result = await move_watchlist_to_reserve('AAPL', mock_user, mock_db)
        
        assert "watchlist" in result
        assert "reserve" in result
        mock_user.set_watchlist_tickers.assert_called_once()
        mock_user.set_reserve_tickers.assert_called_once()
        mock_db.commit.