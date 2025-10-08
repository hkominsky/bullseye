import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import base64
from src.model.notifier.notifications import EmailNotifier


class TestEmailNotifier:
    
    @pytest.fixture
    def mock_env(self):
        with patch.dict('os.environ', {
            'SENDGRID_API_KEY': 'test_api_key',
            'SENDER_EMAIL': 'sender@example.com',
            'EMAIL_TO': 'recipient@example.com'
        }):
            yield
    
    @pytest.fixture
    def notifier(self, mock_env):
        with patch('src.model.notifier.notifications.LoggerSetup'):
            with patch('src.model.notifier.notifications.SendGridAPIClient'):
                with patch('src.model.notifier.notifications.EmailBuilder'):
                    return EmailNotifier()
    
    @pytest.fixture
    def sample_data(self):
        return {
            'ticker': 'AAPL',
            'corporate_sentiment': 0.65,
            'retail_sentiment': 0.45,
            'news_df': pd.DataFrame({'headline': ['Test News']}),
            'sector_performance': {'sector': 'Technology', 'sector_etf': 'XLK'},
            'raw_df': pd.DataFrame({'revenue': [100000]}),
            'metrics_df': pd.DataFrame({'gross_margin': [40.0]}),
            'earnings_df': pd.DataFrame({'reportedEPS': [1.5]}),
            'earnings_estimate': {'nextEarningsDate': '2024-07-01'}
        }
    
    def test_init_success(self, mock_env):
        with patch('src.model.notifier.notifications.LoggerSetup'):
            with patch('src.model.notifier.notifications.SendGridAPIClient'):
                with patch('src.model.notifier.notifications.EmailBuilder'):
                    notifier = EmailNotifier()
                    assert notifier.api_key == 'test_api_key'
                    assert notifier.sender == 'sender@example.com'
                    assert notifier.recipient == 'recipient@example.com'
    
    def test_init_missing_api_key(self):
        with patch.dict('os.environ', {
            'SENDER_EMAIL': 'sender@example.com',
            'EMAIL_TO': 'recipient@example.com'
        }):
            with patch('src.model.notifier.notifications.LoggerSetup'):
                with pytest.raises(ValueError, match="Missing one or more required email environment variables"):
                    EmailNotifier()
    
    def test_init_missing_sender(self):
        with patch.dict('os.environ', {
            'SENDGRID_API_KEY': 'test_key',
            'EMAIL_TO': 'recipient@example.com'
        }):
            with patch('src.model.notifier.notifications.LoggerSetup'):
                with pytest.raises(ValueError, match="Missing one or more required email environment variables"):
                    EmailNotifier()
    
    def test_init_missing_recipient(self):
        with patch.dict('os.environ', {
            'SENDGRID_API_KEY': 'test_key',
            'SENDER_EMAIL': 'sender@example.com'
        }):
            with patch('src.model.notifier.notifications.LoggerSetup'):
                with pytest.raises(ValueError, match="Missing one or more required email environment variables"):
                    EmailNotifier()
    
    @patch('src.model.notifier.notifications.Mail')
    def test_send_email_success_with_chart(self, mock_mail, notifier, sample_data):
        notifier.email_builder.build_html_content = Mock(return_value=(
            '<html>Test Content</html>',
            (b'fake_image_data', 'chart_id', 'chart.png')
        ))
        
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.body = 'Success'
        mock_response.headers = {}
        notifier.sg_client.send = Mock(return_value=mock_response)
        
        status, body, headers = notifier.send_email(**sample_data)
        
        assert status == 202
        assert body == 'Success'
        notifier.sg_client.send.assert_called_once()
    
    @patch('src.model.notifier.notifications.Mail')
    def test_send_email_success_without_chart(self, mock_mail, notifier, sample_data):
        notifier.email_builder.build_html_content = Mock(return_value=(
            '<html>Test Content</html>',
            None
        ))
        
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.body = 'Success'
        mock_response.headers = {}
        notifier.sg_client.send = Mock(return_value=mock_response)
        
        status, body, headers = notifier.send_email(**sample_data)
        
        assert status == 202
    
    @patch('src.model.notifier.notifications.Mail')
    def test_send_email_subject_format(self, mock_mail, notifier, sample_data):
        notifier.email_builder.build_html_content = Mock(return_value=(
            '<html>Test</html>',
            None
        ))
        
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.body = 'Success'
        mock_response.headers = {}
        notifier.sg_client.send = Mock(return_value=mock_response)
        
        notifier.send_email(**sample_data)
        
        call_kwargs = mock_mail.call_args[1]
        assert call_kwargs['subject'] == 'AAPL Market Brief'
    
    @patch('src.model.notifier.notifications.Mail')
    @patch('src.model.notifier.notifications.Attachment')
    def test_send_email_attachment_encoding(self, mock_attachment, mock_mail, notifier, sample_data):
        chart_bytes = b'test_image_data'
        notifier.email_builder.build_html_content = Mock(return_value=(
            '<html>Test</html>',
            (chart_bytes, 'chart_id', 'chart.png')
        ))
        
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.body = 'Success'
        mock_response.headers = {}
        notifier.sg_client.send = Mock(return_value=mock_response)
        
        notifier.send_email(**sample_data)
        
        expected_base64 = base64.b64encode(chart_bytes).decode('utf-8')
        mock_attachment.assert_called_once()
        assert mock_attachment.call_args[0][0].file_content == expected_base64
    
    def test_send_email_exception(self, notifier, sample_data):
        notifier.email_builder.build_html_content = Mock(side_effect=Exception("Build error"))
        
        status, body, headers = notifier.send_email(**sample_data)
        
        assert status is None
        assert "Build error" in body
        assert headers is None
    
    @patch('src.model.notifier.notifications.Mail')
    def test_send_email_sendgrid_exception(self, mock_mail, notifier, sample_data):
        notifier.email_builder.build_html_content = Mock(return_value=(
            '<html>Test</html>',
            None
        ))
        notifier.sg_client.send = Mock(side_effect=Exception("SendGrid error"))
        
        status, body, headers = notifier.send_email(**sample_data)
        
        assert status is None
        assert "SendGrid error" in body
    
    @patch('src.model.notifier.notifications.Mail')
    def test_send_email_calls_builder_with_correct_params(self, mock_mail, notifier, sample_data):
        notifier.email_builder.build_html_content = Mock(return_value=(
            '<html>Test</html>',
            None
        ))
        
        mock_response = Mock()
        mock_response.status_code = 202
        notifier.sg_client.send = Mock(return_value=mock_response)
        
        notifier.send_email(**sample_data)
        
        notifier.email_builder.build_html_content.assert_called_once()
        call_kwargs = notifier.email_builder.build_html_content.call_args[1]
        assert call_kwargs['ticker'] == 'AAPL'
        assert call_kwargs['corporate_sentiment'] == 0.65
    
    @patch('src.model.notifier.notifications.Mail')
    def test_send_email_different_tickers(self, mock_mail, notifier, sample_data):
        notifier.email_builder.build_html_content = Mock(return_value=(
            '<html>Test</html>',
            None
        ))
        
        mock_response = Mock()
        mock_response.status_code = 202
        notifier.sg_client.send = Mock(return_value=mock_response)
        
        sample_data['ticker'] = 'MSFT'
        notifier.send_email(**sample_data)
        
        call_kwargs = mock_mail.call_args[1]
        assert call_kwargs['subject'] == 'MSFT Market Brief'
    
    @patch('src.model.notifier.notifications.Mail')
    @patch('src.model.notifier.notifications.Attachment')
    @patch('src.model.notifier.notifications.FileContent')
    @patch('src.model.notifier.notifications.FileName')
    @patch('src.model.notifier.notifications.FileType')
    @patch('src.model.notifier.notifications.Disposition')
    @patch('src.model.notifier.notifications.ContentId')
    def test_send_email_attachment_properties(self, mock_content_id, mock_disposition, 
                                             mock_file_type, mock_file_name, mock_file_content,
                                             mock_attachment, mock_mail, notifier, sample_data):
        notifier.email_builder.build_html_content = Mock(return_value=(
            '<html>Test</html>',
            (b'image_data', 'chart_aapl', 'AAPL_chart.png')
        ))
        
        mock_response = Mock()
        mock_response.status_code = 202
        notifier.sg_client.send = Mock(return_value=mock_response)
        
        notifier.send_email(**sample_data)
        
        mock_file_name.assert_called_once_with('AAPL_chart.png')
        mock_file_type.assert_called_once_with('image/png')
        mock_disposition.assert_called_once_with('inline')
        mock_content_id.assert_called_once_with('chart_aapl')