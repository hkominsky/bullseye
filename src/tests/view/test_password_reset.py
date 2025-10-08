import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi import HTTPException
from auth.password_reset import (
    get_sendgrid_client,
    generate_reset_token,
    is_reset_token_valid,
    update_user_reset_token,
    create_reset_email_content,
    send_reset_email,
    find_user_by_reset_token,
    clear_reset_token,
    reset_password,
    confirm_reset_password,
    test_sendgrid
)
from config.types import PasswordResetRequest, PasswordResetConfirm


class TestPasswordResetHelpers:
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def mock_user(self):
        user = Mock()
        user.email = "test@example.com"
        user.reset_token = None
        user.reset_token_expiry = None
        user.hashed_password = "old_hash"
        return user
    
    def test_get_sendgrid_client_success(self):
        with patch.dict('os.environ', {'SENDGRID_API_KEY': 'test_key'}):
            with patch('auth.password_reset.SendGridAPIClient') as mock_sg:
                client = get_sendgrid_client()
                mock_sg.assert_called_once_with(api_key='test_key')
    
    def test_get_sendgrid_client_no_api_key(self):
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="SENDGRID_API_KEY"):
                get_sendgrid_client()
    
    def test_generate_reset_token(self):
        token, token_hash = generate_reset_token()
        
        assert len(token) > 0
        assert len(token_hash) == 64  # SHA256 produces 64 character hex string
        assert token != token_hash
    
    def test_generate_reset_token_uniqueness(self):
        token1, hash1 = generate_reset_token()
        token2, hash2 = generate_reset_token()
        
        assert token1 != token2
        assert hash1 != hash2
    
    def test_is_reset_token_valid_true(self, mock_user):
        mock_user.reset_token = "valid_token"
        mock_user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=30)
        
        assert is_reset_token_valid(mock_user) == True
    
    def test_is_reset_token_valid_expired(self, mock_user):
        mock_user.reset_token = "valid_token"
        mock_user.reset_token_expiry = datetime.utcnow() - timedelta(minutes=30)
        
        assert is_reset_token_valid(mock_user) == False
    
    def test_is_reset_token_valid_no_token(self, mock_user):
        assert is_reset_token_valid(mock_user) == False
    
    def test_update_user_reset_token(self, mock_user, mock_db):
        token_hash = "test_hash"
        
        update_user_reset_token(mock_user, token_hash, mock_db)
        
        assert mock_user.reset_token == token_hash
        assert mock_user.reset_token_expiry > datetime.utcnow()
        mock_db.commit.assert_called_once()
    
    def test_create_reset_email_content(self):
        reset_url = "http://example.com/reset?token=abc123"
        
        html, text = create_reset_email_content(reset_url)
        
        assert reset_url in html
        assert reset_url in text
        assert "Reset Password" in html
        assert "Bullseye" in html
        assert "Bullseye" in text
    
    def test_create_reset_email_content_html_structure(self):
        reset_url = "http://example.com/reset"
        html, _ = create_reset_email_content(reset_url)
        
        assert "<!DOCTYPE html>" in html
        assert "reset-button" in html
        assert "email-container" in html
    
    def test_send_reset_email_success(self):
        with patch('auth.password_reset.get_sendgrid_client') as mock_get_client:
            with patch('auth.password_reset.Mail') as mock_mail:
                with patch.dict('os.environ', {'SENDER_EMAIL': 'sender@example.com'}):
                    mock_sg = Mock()
                    mock_response = Mock()
                    mock_response.status_code = 202
                    mock_sg.send.return_value = mock_response
                    mock_get_client.return_value = mock_sg
                    
                    send_reset_email("test@example.com", "http://reset.url")
                    
                    mock_sg.send.assert_called_once()
    
    def test_send_reset_email_exception(self):
        with patch('auth.password_reset.get_sendgrid_client') as mock_get_client:
            mock_sg = Mock()
            mock_sg.send.side_effect = Exception("SendGrid error")
            mock_get_client.return_value = mock_sg
            
            with patch.dict('os.environ', {'SENDER_EMAIL': 'sender@example.com'}):
                with pytest.raises(Exception):
                    send_reset_email("test@example.com", "http://reset.url")
    
    def test_find_user_by_reset_token_success(self, mock_db, mock_user):
        token = "test_token"
        mock_user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=30)
        mock_db.query().filter().first.return_value = mock_user
        
        result = find_user_by_reset_token(token, mock_db)
        
        assert result == mock_user
    
    def test_find_user_by_reset_token_invalid(self, mock_db):
        mock_db.query().filter().first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            find_user_by_reset_token("invalid_token", mock_db)
        
        assert exc_info.value.status_code == 400
        assert "Invalid or expired" in exc_info.value.detail
    
    def test_clear_reset_token(self, mock_user, mock_db):
        with patch('auth.password_reset.get_password_hash') as mock_hash:
            mock_hash.return_value = "new_hash"
            
            clear_reset_token(mock_user, "new_password", mock_db)
            
            assert mock_user.hashed_password == "new_hash"
            assert mock_user.reset_token is None
            assert mock_user.reset_token_expiry is None
            mock_db.commit.assert_called_once()


class TestPasswordResetEndpoints:
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def mock_user(self):
        user = Mock()
        user.email = "test@example.com"
        user.reset_token = None
        user.reset_token_expiry = None
        return user
    
    def test_reset_password_user_not_found(self, mock_db):
        mock_db.query().filter().first.return_value = None
        request = PasswordResetRequest(email="nonexistent@example.com")
        
        response = reset_password(request, mock_db)
        
        assert "If the email exists" in response.message
    
    def test_reset_password_success(self, mock_db, mock_user):
        mock_db.query().filter().first.return_value = mock_user
        request = PasswordResetRequest(email="test@example.com")
        
        with patch('auth.passwo