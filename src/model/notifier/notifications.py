import os
import pandas as pd
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId
from src.model.notifier.email_builder import EmailBuilder


class EmailNotifier:
    """
    Email notifier that sends SEC financial data reports via SendGrid Web API,
    using CID attachments for reliable image display without external CDN.

    Expects the following environment variables:
        SENDGRID_API_KEY: SendGrid API key
        SENDER_EMAIL:    Verified "from" email address in SendGrid
        EMAIL_TO:        Recipient email address
    """

    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.sender = os.getenv("SENDER_EMAIL")
        self.recipient = os.getenv("EMAIL_TO")

        if not all([self.api_key, self.sender, self.recipient]):
            raise ValueError("Missing one or more required email environment variables.")

        self.sg_client = SendGridAPIClient(self.api_key)
        self.email_builder = EmailBuilder()

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
        Sends an email with all relevant data including financial records, calculated ratios, stock pricing,
        news, sector performance, earnings analysis (historical + estimate), and ticker sentiment.
        """
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
        else:
            print("No chart generated.")

        try:
            response = self.sg_client.send(message)
            return response.status_code, response.body, response.headers
        except Exception as e:
            print(f"[{ticker}] SendGrid error: {str(e)}")
            return None, str(e), None