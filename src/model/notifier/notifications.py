import os
import pandas as pd
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from src.model.notifier.email_builder import EmailBuilder


class EmailNotifier:
    """
    Email notifier that sends SEC financial data reports via SendGrid Web API,
    using official SendGrid handling and exception patterns.

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

    def send_email(self, raw_df: pd.DataFrame, metrics_df: pd.DataFrame,
                   subject="SEC Financial Report - Raw Data & Metrics"):
        """
        Sends an email with two DataFrames using SendGrid Web API.
        """
        html_content = self.email_builder.build_html_content(raw_df, metrics_df)

        message = Mail(
            from_email=self.sender,
            to_emails=self.recipient,
            subject=subject,
            html_content=html_content
        )

        try:
            response = self.sg_client.send(message)
            return response.status_code, response.body, response.headers

        except Exception as e:
            print(f"SendGrid error: {str(e)}")
            return None, str(e), None