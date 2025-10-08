import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from sqlalchemy.orm import Session
from config.database import User, get_db


class TestUserModel:
    
    @pytest.fixture
    def user(self):
        return User(
            id=1,
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_pass",
            watchlist_tickers="AAPL,MSFT,GOOGL",
            reserve_tickers="TSLA,AMZN"
        )
    
    def test_user_creation(self):
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_pass"
        )
        
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.hashed_password == "hashed_pass"
    
    def test_get_watchlist_tickers_with_data(self, user):
        tickers = user.get_watchlist_tickers()
        
        assert tickers == ["AAPL", "MSFT", "GOOGL"]
    
    def test_get_watchlist_tickers_empty(self):
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_pass",
            watchlist_tickers=None
        )
        
        tickers = user.get_watchlist_tickers()
        
        assert tickers == []
    
    def test_get_watchlist_tickers_empty_string(self):
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_pass",
            watchlist_tickers=""
        )
        
        tickers = user.get_watchlist_tickers()
        
        assert tickers == []
    
    def test_get_watchlist_tickers_strips_whitespace(self):
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_pass",
            watchlist_tickers=" AAPL , MSFT , GOOGL "
        )
        
        tickers = user.get_watchlist_tickers()
        
        assert tickers == ["AAPL", "MSFT", "GOOGL"]
    
    def test_get_watchlist_tickers_ignores_empty_entries(self):
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_pass",
            watchlist_tickers="AAPL,,MSFT,,"
        )
        
        tickers = user.get_watchlist_tickers()
        
        assert tickers == ["AAPL", "MSFT"]
    
    def test_get_reserve_tickers_with_data(self, user):
        tickers = user.get_reserve_tickers()
        
        assert tickers == ["TSLA", "AMZN"]
    
    def test_get_reserve_tickers_empty(self):
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_pass",
            reserve_tickers=None
        )
        
        tickers = user.get_reserve_tickers()
        
        assert tickers == []
    
    def test_set_watchlist_tickers(self):
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_pass"
        )
        
        user.set_watchlist_tickers(["AAPL", "MSFT", "GOOGL"])
        
        assert user.watchlist_tickers == "AAPL,MSFT,GOOGL"
    
    def test_set_watchlist_tickers_empty_list(self):
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_pass"
        )
        
        user.set_watchlist_tickers([])
        
        assert user.watchlist_tickers is None
    
    def test_set_reserve_tickers(self):
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_pass"
        )
        
        user.set_reserve_tickers(["TSLA", "AMZN"])
        
        assert user.reserve_tickers == "TSLA,AMZN"
    
    def test_set_reserve_tickers_empty_list(self):
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_pass"
        )
        
        user.set_reserve_tickers([])
        
        assert user.reserve_tickers is None
    
    def test_user_oauth_fields(self):
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="",
            oauth_provider="google",
            oauth_provider_id="123456"
        )
        
        assert user.oauth_provider == "google"
        assert user.oauth_provider_id == "123456"
    
    def test_user_reset_token_fields(self):
        expiry = datetime.utcnow()
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_pass",
            reset_token="token_hash",
            reset_token_expiry=expiry
        )
        
        assert user.reset_token == "token_hash"
        assert user.reset_token_expiry == expiry
    
    def test_user_timestamps(self):
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_pass"
        )
        
        assert hasattr(user, 'created_at')
        assert hasattr(user, 'updated_at')


class TestGetDb:
    
    def test_get_db_yields_session(self):
        with patch('config.database.SessionLocal') as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session
            
            db_generator = get_db()
            db = next(db_generator)
            
            assert db == mock_session
    
    def test_get_db_closes_session(self):
        with patch('config.database.SessionLocal') as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session
            
            db_generator = get_db()
            next(db_generator)
            
            try:
                next(db_generator)
            except StopIteration:
                pass
            
            mock_session.close.assert_called_once()
    
    def test_get_db_closes_on_exception(self):
        with patch('config.database.SessionLocal') as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session
            
            db_generator = get_db()
            next(db_generator)
            
            try:
                db_generator.throw(Exception("Test error"))
            except Exception:
                pass
            
            mock_session.close.assert_called_once()


class TestDatabaseConfiguration:
    
    def test_database_url_format(self):
        with patch('config.database.config') as mock_config:
            mock_config.side_effect = lambda key, default=None, cast=None: {
                'DB_HOST': 'localhost',
                'DB_PORT': '5432',
                'DB_NAME': 'testdb',
                'DB_USER': 'testuser',
                'DB_PASSWORD': 'testpass'
            }.get(key, default)
            
            from config.database import DATABASE_URL
            
            assert 'postgresql://' in DATABASE_URL
            assert 'testuser:testpass' in DATABASE_URL
            assert 'localhost:5432' in DATABASE_URL
            assert 'testdb' in DATABASE_URL