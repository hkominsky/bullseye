import pytest
from unittest.mock import Mock, patch
from datetime import timedelta
from fastapi import HTTPException
from auth.routes import signup, login, get_current_user_info
from config.schemas import UserCreate, UserLogin


class TestSignup:
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def valid_user_data(self):
        return UserCreate(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="password123",
            confirm_password="password123"
        )
    
    def test_signup_success(self, valid_user_data, mock_db):
        mock_db.query().filter().first.return_value = None
        mock_user = Mock()
        mock_user.email = "test@example.com"
        
        with patch('auth.routes.get_password_hash', return_value="hashed_pass"):
            with patch('auth.routes.User', return_value=mock_user):
                with patch('auth.routes.create_access_token', return_value="jwt_token"):
                    response = signup(valid_user_data, mock_db)
        
        assert response["access_token"] == "jwt_token"
        assert response["token_type"] == "bearer"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_signup_passwords_do_not_match(self, mock_db):
        user_data = UserCreate(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="password123",
            confirm_password="different_password"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            signup(user_data, mock_db)
        
        assert exc_info.value.status_code == 400
        assert "Passwords do not match" in exc_info.value.detail
    
    def test_signup_email_already_exists(self, valid_user_data, mock_db):
        existing_user = Mock()
        mock_db.query().filter().first.return_value = existing_user
        
        with pytest.raises(HTTPException) as exc_info:
            signup(valid_user_data, mock_db)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in exc_info.value.detail
    
    def test_signup_creates_user_with_correct_data(self, valid_user_data, mock_db):
        mock_db.query().filter().first.return_value = None
        
        with patch('auth.routes.get_password_hash', return_value="hashed_pass"):
            with patch('auth.routes.User') as mock_user_class:
                with patch('auth.routes.create_access_token', return_value="jwt_token"):
                    signup(valid_user_data, mock_db)
                    
                    call_kwargs = mock_user_class.call_args[1]
                    assert call_kwargs['email'] == "test@example.com"
                    assert call_kwargs['first_name'] == "Test"
                    assert call_kwargs['last_name'] == "User"
                    assert call_kwargs['hashed_password'] == "hashed_pass"
    
    def test_signup_token_expires_in_30_minutes(self, valid_user_data, mock_db):
        mock_db.query().filter().first.return_value = None
        mock_user = Mock()
        mock_user.email = "test@example.com"
        
        with patch('auth.routes.get_password_hash', return_value="hashed_pass"):
            with patch('auth.routes.User', return_value=mock_user):
                with patch('auth.routes.create_access_token') as mock_create_token:
                    signup(valid_user_data, mock_db)
                    
                    call_kwargs = mock_create_token.call_args[1]
                    assert call_kwargs['expires_delta'] == timedelta(minutes=30)


class TestLogin:
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def mock_user(self):
        user = Mock()
        user.email = "test@example.com"
        user.hashed_password = "hashed_pass"
        return user
    
    @pytest.fixture
    def valid_credentials(self):
        return UserLogin(
            email="test@example.com",
            password="password123"
        )
    
    def test_login_success(self, valid_credentials, mock_db, mock_user):
        mock_db.query().filter().first.return_value = mock_user
        
        with patch('auth.routes.verify_password', return_value=True):
            with patch('auth.routes.create_access_token', return_value="jwt_token"):
                response = login(valid_credentials, mock_db)
        
        assert response["access_token"] == "jwt_token"
        assert response["token_type"] == "bearer"
        assert response["user"] == mock_user
    
    def test_login_user_not_found(self, valid_credentials, mock_db):
        mock_db.query().filter().first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            login(valid_credentials, mock_db)
        
        assert exc_info.value.status_code == 401
        assert "Incorrect email or password" in exc_info.value.detail
    
    def test_login_incorrect_password(self, valid_credentials, mock_db, mock_user):
        mock_db.query().filter().first.return_value = mock_user
        
        with patch('auth.routes.verify_password', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                login(valid_credentials, mock_db)
        
        assert exc_info.value.status_code == 401
        assert "Incorrect email or password" in exc_info.value.detail
    
    def test_login_token_expires_in_30_minutes(self, valid_credentials, mock_db, mock_user):
        mock_db.query().filter().first.return_value = mock_user
        
        with patch('auth.routes.verify_password', return_value=True):
            with patch('auth.routes.create_access_token') as mock_create_token:
                mock_create_token.return_value = "jwt_token"
                login(valid_credentials, mock_db)
                
                call_kwargs = mock_create_token.call_args[1]
                assert call_kwargs['expires_delta'] == timedelta(minutes=30)


class TestGetCurrentUserInfo:
    
    @pytest.fixture
    def mock_user(self):
        user = Mock()
        user.id = 1
        user.email = "test@example.com"
        user.first_name = "Test"
        user.last_name = "User"
        return user
    
    def test_get_current_user_info_success(self, mock_user):
        result = get_current_user_info(mock_user)
        
        assert result == mock_user
    
    def test_get_current_user_info_returns_user_response(self, mock_user):
        result = get_current_user_info(mock_user)
        
        assert hasattr(result, 'email')
        assert result.email == "test@example.com"


class TestRouterConfiguration:
    
    def test_router_prefix(self):
        from auth.routes import router
        assert router.prefix == "/auth"
    
    def test_router_tags(self):
        from auth.routes import router
        assert "authentication" in router.tags
    
    def test_router_includes_oauth(self):
        from auth.routes import router
        # OAuth router should be included
        assert any('oauth' in str(route.path).lower() or 'google' in str(route.path).lower() 
                  for route in router.routes)
    
    def test_router_includes_password_reset(self):
        from auth.routes import router
        # Password reset router should be included
        assert any('reset' in str(route.path).lower() for route in router.routes)