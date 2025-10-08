import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException, BackgroundTasks
from emails.routes import send_watchlist_emails, send_custom_emails
from config.schemas import CustomEmailRequest


class TestSendWatchlistEmails:
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def mock_user(self):
        user = Mock()
        user.email = "test@example.com"
        user.get_watchlist_tickers.return_value = ["AAPL", "MSFT", "GOOGL"]
        return user
    
    @pytest.fixture
    def background_tasks(self):
        return BackgroundTasks()
    
    @pytest.mark.asyncio
    async def test_send_watchlist_emails_success(self, mock_user, mock_db, background_tasks):
        with patch('emails.routes.EmailController') as mock_controller:
            response = await send_watchlist_emails(background_tasks, mock_user, mock_db)
        
        assert response.message == "Email processing started"
        assert response.ticker_count == 3
        assert response.tickers == ["AAPL", "MSFT", "GOOGL"]
        assert response.status == "processing"
        mock_db.refresh.assert_called_once_with(mock_user)
    
    @pytest.mark.asyncio
    async def test_send_watchlist_emails_empty_watchlist(self, mock_user, mock_db, background_tasks):
        mock_user.get_watchlist_tickers.return_value = []
        
        with pytest.raises(HTTPException) as exc_info:
            await send_watchlist_emails(background_tasks, mock_user, mock_db)
        
        assert exc_info.value.status_code == 400
        assert "Watchlist is empty" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_send_watchlist_emails_no_user_email(self, mock_user, mock_db, background_tasks):
        mock_user.email = None
        
        with pytest.raises(HTTPException) as exc_info:
            await send_watchlist_emails(background_tasks, mock_user, mock_db)
        
        assert exc_info.value.status_code == 400
        assert "User email not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_send_watchlist_emails_adds_background_task(self, mock_user, mock_db):
        background_tasks = Mock()
        
        with patch('emails.routes.EmailController') as mock_controller_class:
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            
            await send_watchlist_emails(background_tasks, mock_user, mock_db)
            
            background_tasks.add_task.assert_called_once()
            call_args = background_tasks.add_task.call_args[0]
            assert call_args[0] == mock_controller.send_watchlist_emails
            assert call_args[1] == ["AAPL", "MSFT", "GOOGL"]
            assert call_args[2] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_send_watchlist_emails_general_exception(self, mock_user, mock_db, background_tasks):
        mock_db.refresh.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            await send_watchlist_emails(background_tasks, mock_user, mock_db)
        
        assert exc_info.value.status_code == 500


class TestSendCustomEmails:
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def mock_user(self):
        user = Mock()
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def background_tasks(self):
        return BackgroundTasks()
    
    @pytest.fixture
    def valid_request(self):
        return CustomEmailRequest(tickers=["AAPL", "MSFT", "TSLA"])
    
    @pytest.mark.asyncio
    async def test_send_custom_emails_success(self, valid_request, mock_user, mock_db, background_tasks):
        with patch('emails.routes.EmailController') as mock_controller:
            response = await send_custom_emails(valid_request, background_tasks, mock_user, mock_db)
        
        assert response.message == "Email processing started"
        assert response.ticker_count == 3
        assert response.tickers == ["AAPL", "MSFT", "TSLA"]
        assert response.status == "processing"
    
    @pytest.mark.asyncio
    async def test_send_custom_emails_empty_list(self, mock_user, mock_db, background_tasks):
        request = CustomEmailRequest(tickers=[])
        
        with pytest.raises(HTTPException) as exc_info:
            await send_custom_emails(request, background_tasks, mock_user, mock_db)
        
        assert exc_info.value.status_code == 400
        assert "No tickers provided" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_send_custom_emails_no_user_email(self, valid_request, mock_user, mock_db, background_tasks):
        mock_user.email = None
        
        with pytest.raises(HTTPException) as exc_info:
            await send_custom_emails(valid_request, background_tasks, mock_user, mock_db)
        
        assert exc_info.value.status_code == 400
        assert "User email not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_send_custom_emails_adds_background_task(self, valid_request, mock_user, mock_db):
        background_tasks = Mock()
        
        with patch('emails.routes.EmailController') as mock_controller_class:
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            
            await send_custom_emails(valid_request, background_tasks, mock_user, mock_db)
            
            background_tasks.add_task.assert_called_once()
            call_args = background_tasks.add_task.call_args[0]
            assert call_args[0] == mock_controller.send_custom_emails
            assert call_args[1] == ["AAPL", "MSFT", "TSLA"]
            assert call_args[2] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_send_custom_emails_refreshes_user(self, valid_request, mock_user, mock_db, background_tasks):
        with patch('emails.routes.EmailController'):
            await send_custom_emails(valid_request, background_tasks, mock_user, mock_db)
        
        mock_db.refresh.assert_called_once_with(mock_user)
    
    @pytest.mark.asyncio
    async def test_send_custom_emails_general_exception(self, valid_request, mock_user, mock_db, background_tasks):
        mock_db.refresh.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            await send_custom_emails(valid_request, background_tasks, mock_user, mock_db)
        
        assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_send_custom_emails_single_ticker(self, mock_user, mock_db, background_tasks):
        request = CustomEmailRequest(tickers=["AAPL"])
        
        with patch('emails.routes.EmailController'):
            response = await send_custom_emails(request, background_tasks, mock_user, mock_db)
        
        assert response.ticker_count == 1
        assert response.tickers == ["AAPL"]