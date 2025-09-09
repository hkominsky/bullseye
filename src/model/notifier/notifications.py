import os
import pandas as pd
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId
from src.model.notifier.email_builder import EmailBuilder
from src.model.utils.logger_config import LoggerSetup


class EmailNotifier:
    """
    Email notifier that sends SEC financial data reports via SendGrid.
    """

    def __init__(self):
        self.logger = LoggerSetup.setup_logger(__name__)
        
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.sender = os.getenv("SENDER_EMAIL")
        self.recipient = os.getenv("EMAIL_TO")

        if not all([self.api_key, self.sender, self.recipient]):
            self.logger.error("Missing one or more required email environment variables")
            raise ValueError("Missing one or more required email environment variables.")

        self.sg_client = SendGridAPIClient(self.api_key)
        self.email_builder = EmailBuilder()
        
        self.logger.info(f"EmailNotifier initialized - Sender: {self.sender}, Recipient: {self.recipient}")

    def send_email(
        self,
        ticker: str,
        corporate_sentiment: float,
        retail_sentiment: float,
        news_df: pd.DataFrame,
        sector_performance: dict,
        raw_df: pd.DataFrame,
        metrics_df: pd.DataFrame,
        earnings_df: pd.DataFrame,
        earnings_estimate: dict,
    ):
        """
        Handles sending the email generated from the EmailBuilder.
        """
        self.logger.info(f"Preparing to send email for ticker: {ticker}")
        
        try:
            html_content, chart_attachment_data = self.email_builder.build_html_content(
                raw_df=raw_df,
                metrics_df=metrics_df,
                ticker=ticker,
                corporate_sentiment=corporate_sentiment,
                retail_sentiment=retail_sentiment,
                news_df=news_df,
                sector_performance=sector_performance,
                earnings_df=earnings_df,
                earnings_estimate=earnings_estimate,
            )
            
            self.logger.debug(f"HTML content built for {ticker}")

            subject = f"{ticker} Market Brief"

            message = Mail(
                from_email=self.sender,
                to_emails=self.recipient,
                subject=subject,
                html_content=html_content
            )

            if chart_attachment_data:
                chart_bytes, content_id, filename = chart_attachment_data
                chart_base64 = base64.b64encode(chart_bytes).decode('utf-8')
                chart_attachment = Attachment(
                    FileContent(chart_base64),
                    FileName(filename),
                    FileType("image/png"),
                    Disposition("inline"),
                    ContentId(content_id)
                )                      
                message.attachment = chart_attachment
                self.logger.debug(f"Chart attachment added for {ticker}: {filename}")
            else:
                self.logger.warning(f"No chart generated for {ticker}")

            response = self.sg_client.send(message)
            self.logger.info(f"Email sent successfully for {ticker} - Status: {response.status_code}")
            return response.status_code, response.body, response.headers
            
        except Exception as e:
            self.logger.error(f"SendGrid error for {ticker}: {str(e)}")
            return None, str(e), None