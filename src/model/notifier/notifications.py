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

    def send_email(self, raw_df: pd.DataFrame, metrics_df: pd.DataFrame,
                   subject="SEC Financial Report - Raw Data & Metrics",
                   ticker="AAPL"):
        """
        Sends an email with two DataFrames and embedded stock chart using CID attachment.
        
        Args:
            raw_df: Raw financial data DataFrame
            metrics_df: Calculated metrics DataFrame
            subject: Email subject line
            ticker: Stock ticker symbol for chart generation
        """
        html_content, chart_attachment_data = self.email_builder.build_html_content_with_chart(
            raw_df, metrics_df, ticker
        )

        message = Mail(
            from_email=self.sender,
            to_emails=self.recipient,
            subject=subject,
            html_content=html_content
        )

        # Add chart as CID attachment if available
        if chart_attachment_data:
            chart_bytes, content_id, filename = chart_attachment_data
            
            # Convert bytes to base64 for SendGrid attachment
            chart_base64 = base64.b64encode(chart_bytes).decode('utf-8')
            
            # Create SendGrid attachment with CID
            chart_attachment = Attachment(
                FileContent(chart_base64),
                FileName(filename),
                FileType("image/png"),
                Disposition("inline"),
                ContentId(content_id)
            )
            
            message.attachment = chart_attachment
            print(f"✅ Chart generated")
        else:
            print("⚠️ No chart generated")

        try:
            response = self.sg_client.send(message)
            print(f"Email sent successfully! Status: {response.status_code}")
            print(f"📧 Email sent to: {self.recipient}")
            print(f"📊 Report for: {ticker}")
            return response.status_code, response.body, response.headers

        except Exception as e:
            print(f"SendGrid error: {str(e)}")
            return None, str(e), None

    def send_email_without_chart(self, raw_df: pd.DataFrame, metrics_df: pd.DataFrame,
                                subject="SEC Financial Report - Raw Data & Metrics"):
        """
        Sends an email with just the financial data tables (no chart).
        Useful as a fallback or for simpler reports.
        """
        html_content = self.email_builder.build_email_content(raw_df, metrics_df)

        message = Mail(
            from_email=self.sender,
            to_emails=self.recipient,
            subject=subject,
            html_content=html_content
        )

        try:
            response = self.sg_client.send(message)
            print(f"Email sent successfully! Status: {response.status_code}")
            print(f"📧 Email sent to: {self.recipient} (tables only)")
            return response.status_code, response.body, response.headers

        except Exception as e:
            print(f"SendGrid error: {str(e)}")
            return None, str(e), None

    def test_chart_generation(self, ticker="AAPL"):
        """
        Test chart generation without sending email.
        Useful for debugging chart creation issues.
        """
        print(f"Testing chart generation for {ticker}...")
        
        stock_data = self.email_builder.fetch_stock_data(ticker)
        if stock_data.empty:
            print(f"❌ No stock data found for {ticker}")
            return False
            
        chart_bytes, content_id = self.email_builder.create_chart_attachment(ticker, stock_data)
        if chart_bytes and content_id:
            chart_size_kb = len(chart_bytes) / 1024
            print(f"✅ Chart generated successfully!")
            print(f"   - Content ID: {content_id}")
            print(f"   - Size: {chart_size_kb:.1f} KB")
            print(f"   - Data points: {len(stock_data)} trading days")
            return True
        else:
            print(f"❌ Chart generation failed for {ticker}")
            return False

    def get_email_size_estimate(self, raw_df: pd.DataFrame, metrics_df: pd.DataFrame, ticker="AAPL"):
        """
        Estimate the total email size before sending.
        Useful to ensure it stays under email size limits.
        """
        html_content, chart_attachment_data = self.email_builder.build_html_content_with_chart(
            raw_df, metrics_df, ticker
        )
        
        html_size_kb = len(html_content.encode('utf-8')) / 1024
        total_size_kb = html_size_kb
        
        if chart_attachment_data:
            chart_bytes, _, _ = chart_attachment_data
            chart_size_kb = len(chart_bytes) / 1024
            total_size_kb += chart_size_kb
            print(f"📊 Email size breakdown:")
            print(f"   - HTML content: {html_size_kb:.1f} KB")
            print(f"   - Chart attachment: {chart_size_kb:.1f} KB")
            print(f"   - Total: {total_size_kb:.1f} KB")
        else:
            print(f"📊 Email size: {html_size_kb:.1f} KB (HTML only)")
        
        # Warn if approaching limits
        if total_size_kb > 10000:  # 10MB
            print("⚠️ Warning: Email size > 10MB - may be rejected by some providers")
        elif total_size_kb > 1000:  # 1MB
            print("⚠️ Large email size - consider optimizing")
        else:
            print("✅ Email size is within normal limits")
            
        return total_size_kb


# Example usage and testing
if __name__ == "__main__":
    # Example test usage
    try:
        notifier = EmailNotifier()
        
        # Test chart generation first
        print("=== Testing Chart Generation ===")
        chart_works = notifier.test_chart_generation("AAPL")
        
        if chart_works:
            print("\n=== Chart generation successful! ===")
            print("You can now use notifier.send_email() with confidence.")
        else:
            print("\n=== Chart generation failed ===")
            print("You can still send emails without charts using send_email_without_chart()")
            
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nMake sure these environment variables are set:")
        print("- SENDGRID_API_KEY")
        print("- SENDER_EMAIL") 
        print("- EMAIL_TO")
    except Exception as e:
        print(f"❌ Error: {e}")