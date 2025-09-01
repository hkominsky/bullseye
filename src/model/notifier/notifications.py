import os
import pandas as pd
import numpy as np
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class EmailNotifier:
   """
   Email notifier that sends SEC financial data reports via SendGrid Web API,
   using official SendGrid handling and exception patterns.

   Expects the following environment variables:
       SENDGRID_API_KEY: SendGrid API key
       SENDER_EMAIL:    Verified "from" email address in SendGrid
       EMAIL_TO:        Default recipient email address
   """

   def __init__(self):
       self.api_key = os.getenv("SENDGRID_API_KEY")
       self.sender = os.getenv("SENDER_EMAIL")
       self.default_recipient = os.getenv("EMAIL_TO")

       if not all([self.api_key, self.sender, self.default_recipient]):
           raise ValueError("Missing one or more required email environment variables.")

       self.sg_client = SendGridAPIClient(self.api_key)

   def format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
       """
       Formats numeric values in DataFrame with abbreviated suffixes (K, M, B, T).
       Also formats column headers from snake_case to Title Case.
       """
       df_formatted = df.copy()
       
       # Format column headers
       df_formatted.columns = [self._format_column_name(col) for col in df_formatted.columns]
       
       # Format numeric values
       for col in df_formatted.columns:
           if pd.api.types.is_numeric_dtype(df_formatted[col]):
               df_formatted[col] = df_formatted[col].apply(self._format_numeric_value)
           else:
               df_formatted[col] = df_formatted[col].apply(self._format_if_numeric)
       
       return df_formatted
   
   def _format_column_name(self, column_name):
       """
       Converts snake_case column names to Title Case.
       Examples: gross_profit -> Gross Profit
       """
       return str(column_name).replace('_', ' ').title()
   
   def _format_numeric_value(self, value):
       """Format numeric values with abbreviated suffixes (K, M, B, T)."""
       if pd.isnull(value):
           return value
           
       try:
           if np.isnan(value):
               return value
       except (TypeError, ValueError):
           pass
       
       try:
           abs_value = abs(float(value))
           
           if abs_value >= 1e12:  # Trillions
               formatted = f"{value / 1e12:.1f}T"
           elif abs_value >= 1e9:  # Billions
               formatted = f"{value / 1e9:.1f}B"
           elif abs_value >= 1e6:  # Millions
               formatted = f"{value / 1e6:.1f}M"
           elif abs_value >= 1e3:  # Thousands
               formatted = f"{value / 1e3:.1f}K"
           else:
               # For smaller numbers, show as is with appropriate decimals
               if isinstance(value, (int, np.integer)) or float(value).is_integer():
                   return str(int(float(value)))
               else:
                   return f"{float(value):.2f}".rstrip('0').rstrip('.')
           
           # Remove .0 from abbreviated numbers
           return formatted.replace('.0', '')
           
       except (ValueError, TypeError, OverflowError):
           return value
   
   def _format_if_numeric(self, value):
       """Helper function to format values that might be numeric strings."""
       if pd.isnull(value) or value == '' or value is None:
           return value
       
       # Convert to string and clean
       str_value = str(value).strip()
       
       # Skip if it's clearly not a number
       if not any(char.isdigit() for char in str_value):
           return value
       
       try:
           # Remove existing formatting and try to convert
           clean_value = str_value.replace(',', '').replace('$', '').replace('%', '')
           numeric_val = float(clean_value)
           
           # Check if it's a large number worth abbreviating
           abs_val = abs(numeric_val)
           if abs_val >= 1000:
               # Format with abbreviations
               if abs_val >= 1e12:
                   abbreviated = f"{numeric_val / 1e12:.1f}T"
               elif abs_val >= 1e9:
                   abbreviated = f"{numeric_val / 1e9:.1f}B"
               elif abs_val >= 1e6:
                   abbreviated = f"{numeric_val / 1e6:.1f}M"
               else:  # >= 1000
                   abbreviated = f"{numeric_val / 1e3:.1f}K"
               
               # Remove .0 from abbreviated numbers
               abbreviated = abbreviated.replace('.0', '')
               
               # Preserve any prefix/suffix symbols
               if '$' in str_value:
                   abbreviated = '$' + abbreviated
               if '%' in str_value:
                   abbreviated = abbreviated + '%'
               
               return abbreviated
           else:
               return value
               
       except (ValueError, TypeError):
           return value

   def build_email_content(self, raw_df: pd.DataFrame, metrics_df: pd.DataFrame) -> str:
       """
       Converts multiple DataFrames to HTML tables for the email body.
       
       Args:
           raw_df (pd.DataFrame): DataFrame containing raw financial data
           metrics_df (pd.DataFrame): DataFrame containing calculated metrics
           
       Returns:
           str: HTML content with both tables
       """
       # Format both DataFrames
       raw_df_formatted = self.format_dataframe(raw_df)
       metrics_df_formatted = self.format_dataframe(metrics_df)
       
       # Convert to HTML tables
       raw_html_table = raw_df_formatted.to_html(index=False, border=0, justify="center", table_id="raw-data-table")
       metrics_html_table = metrics_df_formatted.to_html(index=False, border=0, justify="center", table_id="metrics-table")
       
       html_content = f"""
       <html>
       <head>
       <style>
       table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
       th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
       th {{ background-color: #f2f2f2; }}
       .numeric {{ text-align: right; }}
       .section-header {{ 
           color: #2c3e50; 
           border-bottom: 2px solid #3498db; 
           padding-bottom: 10px; 
           margin-top: 20px; 
           margin-bottom: 15px; 
       }}
       #raw-data-table {{ margin-bottom: 40px; }}
       #metrics-table {{ margin-top: 20px; }}
       </style>
       </head>
       <body>       
       
       <h3 class="section-header">Raw Data</h3>
       {raw_html_table}
       
       <h3 class="section-header">Calculated Ratios / Metrics</h3>
       {metrics_html_table}
       
       </body>
       </html>
       """
       return html_content

   def send_email(self, raw_df: pd.DataFrame, metrics_df: pd.DataFrame, 
                                 subject="SEC Financial Report - Raw Data & Metrics", recipient=None):
       """
       Sends an email with two DataFrames using SendGrid Web API.
       
       Args:
           raw_df (pd.DataFrame): DataFrame containing raw financial data
           metrics_df (pd.DataFrame): DataFrame containing calculated metrics
           subject (str): Email subject line
           recipient (str, optional): Recipient email address
           
       Returns:
           tuple: (status_code, response_body, response_headers)
       """
       to_email = recipient if recipient else self.default_recipient
       filtered_df = raw_df.drop(columns=["date", "form_type"])
       html_content = self.build_email_content(filtered_df, metrics_df)

       message = Mail(
           from_email=self.sender,
           to_emails=to_email,
           subject=subject,
           html_content=html_content
       )

       try:
           response = self.sg_client.send(message)
           return response.status_code, response.body, response.headers
           
       except Exception as e:
           print(f"SendGrid error: {str(e)}")
           return None, str(e), None