import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from datetime import timedelta
from auth.oauth import (
    get_or_create_oauth_user,
    exchange_code_for_token,
    fetch_user_data,
    create_jwt_and_redirect,
    handle_oauth_error,
    google_auth,
    google_callback,
    github_auth,
    github_callback,
    get_github_primary_email,
    parse_github_name
)
from config.types import OAuthUserInfo


class TestOAuthHelpers:
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def mock_user(self):
        user = Mock()
        user.email = "test@example.com"
        user.first_name = "Test"
        user.last_name = "User"
        user.oauth_provider = None
        user.oauth_provider_id = None
        return user
    
    @pytest.fixture
    def oauth_user_info(self):
        return OAuthUserInfo(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            provider="google",
            provider_id="123456"
        )
    
    def test_get_or_create_oauth_user_creates_new(self, mock_db, oauth_user_info):
        mock_db.query().filter().first.return_value = None
        
        with patch('auth.oauth.User') as mock_user_class:
            mock_user = Mock()
            mock_user_class.return_value = mock_user
            
            result = get_or_create_oauth_user(oauth_user_info, mock_db)
            
            mock_db.add.assert_called_once_with(mock_user)
            mock_db.commit.assert_called()
            assert result == mock_user
    
    def test_get_or_create_oauth_user_returns_existing(self, mock_db, mock_user, oauth_user_info):
        mock_user.oauth_provider = "google"
        mock_db.query().filter().first.return_value = mock_user
        
        result = get_or_create_oauth_user(oauth_user_info, mock_db)
        
        assert result == mock_user
        mock_db.add.assert_not_called()
    
    def test_get_or_create_oauth_user_updates_existing_without_provider(self, mock_db, mock_user, oauth_user_info):
        mock_db.query().filter().first.return_value = mock_user
        
        result = get_or_create_oauth_user(oauth_user_info, mock_db)
        
        assert result.oauth_provider == "google"
        assert result.oauth_provider_id == "123456"
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self):
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test_token"}
        mock_client.post.return_value = mock_response
        
        token = await exchange_code_for_token(
            mock_client, "http://token.url", {"code": "test_code"}
        )
        
        assert token == "test_token"
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_failure(self):
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_client.post.return_value = mock_response
        
        with pytest.raises(HTTPException) as exc_info:
            await exchange_code_for_token(
                mock_client, "http://token.url", {"code": "test_code"}
            )
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_fetch_user_data_success(self):
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"email": "test@example.com"}
        mock_client.get.return_value = mock_response
        
        data = await fetch_user_data(
            mock_client, "http://user.url", "test_token"
        )
        
        assert data["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_fetch_user_data_failure(self):
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_client.get.return_value = mock_response
        
        with pytest.raises(HTTPException) as exc_info:
            await fetch_user_data(
                mock_client, "http://user.url", "test_token"
            )
        
        assert exc_info.value.status_code == 400
    
    def test_create_jwt_and_redirect(self, mock_user):
        with patch('auth.oauth.create_access_token') as mock_create_token:
            mock_create_token.return_value = "jwt_token"
            
            response = create_jwt_and_redirect(mock_user, "google")
            
            assert isinstance(response, RedirectResponse)
            assert "jwt_token" in response.headers["location"]
            assert "provider=google" in response.headers["location"]
    
    def test_handle_oauth_error(self):
        error = Exception("Test error")
        
        response = handle_oauth_error(error, "google")
        
        assert isinstance(response, RedirectResponse)
        assert "error=oauth_failed" in response.headers["location"]
    
    def test_google_auth(self):
        response = google_auth()
        
        assert isinstance(response, RedirectResponse)
        assert "accounts.google.com" in response.headers["location"]
        assert "client_id" in response.headers["location"]
    
    def test_github_auth(self):
        response = github_auth()
        
        assert isinstance(response, RedirectResponse)
        assert "github.com" in response.headers["location"]
        assert "client_id" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_get_github_primary_email_success(self):
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"email": "test@example.com", "primary": True},
            {"email": "other@example.com", "primary": False}
        ]
        mock_client.get.return_value = mock_response
        
        email = await get_github_primary_email(mock_client, "test_token")
        
        assert email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_github_primary_email_no_primary(self):
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"email": "test@example.com", "primary": False}
        ]
        mock_client.get.return_value = mock_response
        
        with pytest.raises(HTTPException) as exc_info:
            await get_github_primary_email(mock_client, "test_token")
        
        assert "No email found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_github_primary_email_failure(self):
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_client.get.return_value = mock_response
        
        with pytest.raises(HTTPException):
            await get_github_primary_email(mock_client, "test_token")
    
    def test_parse_github_name_full_name(self):
        first, last = parse_github_name("John Doe")
        
        assert first == "John"
        assert last == "Doe"
    
    def test_parse_github_name_single_name(self):
        first, last = parse_github_name("John")
        
        assert first == "John"
        assert last == ""
    
    def test_parse_github_name_empty(self):
        first, last = parse_github_name("")
        
        assert first == ""
        assert last == ""
    
    def test_parse_github_name_multiple_spaces(self):
        first, last = parse_github_name("John Michael Doe")
        
        assert first == "John"
        assert last == "Michael Doe"
    
    @pytest.mark.asyncio
    async def test_google_callback_success(self, mock_db, mock_user):
        mock_db.query().filter().first.return_value = None
        
        with patch('auth.oauth.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_token_response = Mock()
            mock_token_response.status_code = 200
            mock_token_response.json.return_value = {"access_token": "test_token"}
            
            mock_user_response = Mock()
            mock_user_response.status_code = 200
            mock_user_response.json.return_value = {
                "email": "test@example.com",
                "given_name": "Test",
                "family_name": "User",
                "id": "123456"
            }
            
            mock_client.post.return_value = mock_token_response
            mock_client.get.return_value = mock_user_response
            
            with patch('auth.oauth.User') as mock_user_class:
                mock_user_class.return_value = mock_user
                with patch('auth.oauth.create_access_token', return_value="jwt_token"):
                    response = await google_callback("auth_code", mock_db)
            
            assert isinstance(response, RedirectResponse)
            assert "jwt_token" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_github_callback_success(self, mock_db, mock_user):
        mock_db.query().filter().first.return_value = None
        
        with patch('auth.oauth.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_token_response = Mock()
            mock_token_response.status_code = 200
            mock_token_response.json.return_value = {"access_token": "test_token"}
            
            mock_user_response = Mock()
            mock_user_response.status_code = 200
            mock_user_response.json.return_value = {
                "id": 123456,
                "name": "Test User"
            }
            
            mock_email_response = Mock()
            mock_email_response.status_code = 200
            mock_email_response.json.return_value = [
                {"email": "test@example.com", "primary": True}
            ]
            
            mock_client.post.return_value = mock_token_response
            mock_client.get.side_effect = [mock_user_response, mock_email_response]
            
            with patch('auth.oauth.User') as mock_user_class:
                mock_user_class.return_value = mock_user
                with patch('auth.oauth.create_access_token', return_value="jwt_token"):
                    response = await github_callback("auth_code", mock_db)
            
            assert isinstance(response, RedirectResponse)
            assert "jwt_token" in response.headers["location"]