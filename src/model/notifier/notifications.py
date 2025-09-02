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
        Note: Column formatting is handled separately to preserve custom column names.
        """
        df_formatted = df.copy()

        # Format numeric values only
        for col in df_formatted.columns:
            if pd.api.types.is_numeric_dtype(df_formatted[col]):
                df_formatted[col] = df_formatted[col].apply(self._format_numeric_value)
            else:
                df_formatted[col] = df_formatted[col].apply(self._format_if_numeric)

        return df_formatted

    def format_column_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Helper function to format column headers from snake_case to Title Case.
        Should be called after custom column renaming is complete.
        Only formats columns that appear to be unformatted (lowercase or contain underscores),
        while preserving custom renamed columns.
        """
        df_formatted = df.copy()
        df_formatted.columns = [
            self._format_column_name(col) if self._needs_formatting(col) else col 
            for col in df_formatted.columns
        ]
        return df_formatted

    def _needs_formatting(self, column_name):
        """
        Determines if a column name needs formatting.
        Returns True for columns that appear to be in snake_case or all lowercase.
        Returns False for columns that appear to be custom renamed (have mixed case, all caps, etc.).
        """
        col_str = str(column_name)
        
        # If it contains underscores, it needs formatting
        if '_' in col_str:
            return True
            
        # If it's all lowercase (like 'ticker', 'period', 'revenue'), it needs formatting
        if col_str.islower():
            return True
            
        # If it's a mix of upper and lower case, numbers, or special chars, 
        # assume it's custom renamed and don't format
        return False

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

    def format_raw_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Organizes the DataFrame for email presentation by renaming columns and
        filtering out unnecessary rows.
        """
        filtered_df = df.drop(columns=["date", "form_type"])
        filtered_df = filtered_df.rename(columns={
            "cost_of_revenue": "COGS",
            "research_and_development": "R&D",
            "selling_general_admin": "SG&A",
            "property_plant_equipment": "PP&E",
            "capital_expenditures": "CapEx",
            "operating_income": "OpInc",
            "net_income": "NI",
            "accounts_receivable": "AR",
            "cash_and_equivalents": "Cash",
            "long_term_debt": "LTD",
            "days_sales_outstanding": "DSO",
            "inventory_turnover": "InvTurn",
            "receivables_turnover": "RTurn",
            "debt_to_ebitda": "Debt/EBITDA",
        })
        return filtered_df

    def format_metrics_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Organizes the DataFrame for email presentation by renaming columns and
        filtering out unnecessary rows.
        """
        filtered_df = df.rename(columns={
            "working_capital": "WC",
            "asset_turnover": "AT",
            "altman_z_score": "Z-Score",
            "piotroski_f_score": "F-Score",
            "gross_margin": "GM",
            "operating_margin": "OpM",
            "net_margin": "NM",
            "current_ratio": "CR",
            "quick_ratio": "QR",
            "debt_to_equity": "D/E",
            "return_on_assets": "ROA",
            "return_on_equity": "ROE",
            "free_cash_flow": "FCF",
            "earnings_per_share": "EPS",
        })
        return filtered_df

    def rename_columns(self, df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
        """
        Renames columns in the DataFrame according to a provided mapping.
        """
        return df.rename(columns=mapping, inplace=False)

    def build_email_content(self, raw_df: pd.DataFrame, metrics_df: pd.DataFrame) -> str:
        """
        Converts multiple DataFrames to HTML tables for the email body.
        """
        # Format numeric values first, then format column headers after custom renaming
        raw_df_formatted = self.format_dataframe(raw_df)
        raw_df_formatted = self.format_column_headers(raw_df_formatted)
        
        metrics_df_formatted = self.format_dataframe(metrics_df)
        metrics_df_formatted = self.format_column_headers(metrics_df_formatted)

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
            margin-top: 20px; 
            margin-bottom: 15px; 
        }}
        #raw-data-table {{ margin-bottom: 40px; }}
        #metrics-table {{ margin-top: 20px; }}
        </style>
        </head>
        <body>       

        <h3 class="section-header">📈 Financial Data</h3>
        {raw_html_table}

        <h3 class="section-header">📊 Calculated Ratios / Metrics</h3>
        {metrics_html_table}

        </body>
        </html>
        """
        return html_content
    
    def send_email(self, raw_df: pd.DataFrame, metrics_df: pd.DataFrame,
                   subject="SEC Financial Report - Raw Data & Metrics", recipient=None):
        """
        Sends an email with two DataFrames using SendGrid Web API.
        """
        to_email = recipient if recipient else self.default_recipient
        filtered_raw_df = self.format_raw_df(raw_df)
        filtered_metrics_df = self.format_metrics_df(metrics_df)
        html_content = self.build_email_content(filtered_raw_df, filtered_metrics_df)

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