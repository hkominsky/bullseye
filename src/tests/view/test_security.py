import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from fastapi import HTTPException
from jose import jwt
from auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    get_current_user,
    SECRET_KEY,
    ALGORITHM
)


class TestPasswordFunctions:
    
    def test_get_password_hash(self):
        password = "test_password123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")
    
    def test_verify_password_correct(self):
        password = "test_password123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) == True
    
    def test_verify_password_incorrect(self):
        password = "test_password123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) == False
    
    def test_password_hash_uniqueness(self):
        password = "test_password123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
    
    def test_verify_password_empty_password(self):
        password = ""
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) == True
        assert verify_password("wrong", hashed) == False


class TestJWTFunctions:
    
    def test_create_access_token_default_expiry(self):
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "test@example.com"
        assert "exp" in payload
    
    def test_create_access_token_custom_expiry(self):
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=60)
        token = create_access_token(data, expires_delta)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_time = datetime.utcnow() + expires_delta
        
        assert abs((exp_time - expected_time).total_seconds()) < 5
    
    def test_create_access_token_with_additional_data(self):
        data = {"sub": "test@example.com", "role": "admin"}
        token = create_access_token(data)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "test@example.com"
        assert payload["role"] == "admin"
    
    def test_verify_token_valid(self):
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        email = verify_token(token)
        
        assert email == "test@example.com"
    
    def test_verify_token_no_sub(self):
        data = {"user": "test@example.com"}
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail
    
    def test_verify_token_invalid(self):
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid_token")
        
        assert exc_info.value.status_code == 401
    
    def test_verify_token_expired(self):
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta)
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        
        assert exc_info.value.status_code == 401


class TestGetCurrentUser:
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def mock_user(self):
        user = Mock()
        user.email = "test@example.com"
        user.id = 1
        return user
    
    @pytest.fixture
    def mock_token(self):
        token = Mock()
        data = {"sub": "test@example.com"}
        token.credentials = create_access_token(data)
        return token
    
    def test_get_current_user_success(self, mock_token, mock_db, mock_user):
        mock_db.query().filter().first.return_value = mock_user
        
        user = get_current_user(mock_token, mock_db)
        
        assert user == mock_user
    
    def test_get_current_user_no_user_in_db(self, mock_token, mock_db):
        mock_db.query().filter().first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_token, mock_db)
        
        assert exc_info.value.status_code == 401
    
    def test_get_current_user_invalid_token(self, mock_db):
        invalid_token = Mock()
        invalid_token.credentials = "invalid_token"
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(invalid_token, mock_db)
        
        assert exc_info.value.status_code == 401
    
    def test_get_current_user_no_email_in_token(self, mock_db):
        token_mock = Mock()
        data = {"user": "test@example.com"}
        token_mock.credentials = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token_mock, mock_db)
        
        assert exc_info.value.status_code == 401
    
    def test_get_current_user_expired_token(self, mock_db):
        token_mock = Mock()
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(seconds=-1)
        token_mock.credentials = create_access_token(data, expires_delta)
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token_mock, mock_db)
        
        assert exc_info.value.status_code == 401
    
    def test_get_current_user_www_authenticate_header(self, mock_db):
        invalid_token = Mock()
        invalid_token.credentials = "invalid_token"
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(invalid_token, mock_db)
        
        assert "WWW-Authenticate" in exc_info.value.headers
        assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"