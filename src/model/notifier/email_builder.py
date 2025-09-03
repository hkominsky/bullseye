import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.io as pio
import base64


class EmailBuilder:
    """
    Handles the building and formatting of email content from SEC financial data.
    Uses CID attachments for reliable image display without needing external CDN.
    """
    
    def __init__(self):
        # Centralized custom column mappings
        self.raw_df_mappings = {
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
        }
        
        self.metrics_df_mappings = {
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
            "market_cap": "Mkt Cap",
            "enterprise_value": "EV",
            "book_value_per_share": "BVPS",
            "price_to_earnings": "P/E",
            "price_to_book": "P/B",
            "price_to_sales": "P/S",
            "ev_to_revenue": "EV/Rev",
            "ev_to_ebitda": "EV/EBITDA",
            "revenue_per_share": "Rev/Share",
            "cash_per_share": "Cash/Share",
            "fcf_per_share": "FCF/Share",
            "price_to_fcf": "P/FCF",
            "market_to_book_premium": "M/B Premium"
        }
        
        # Combined set of all custom column names for quick lookup
        self.all_custom_names = set(self.raw_df_mappings.values()) | set(self.metrics_df_mappings.values())

    def fetch_stock_data(self, ticker: str) -> pd.DataFrame:
        """
        Fetches stock data for the current year using yfinance.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            
        Returns:
            DataFrame with stock data for current year
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period='1y')
            
            if not hist.empty:
                return hist
                
        except Exception as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
            
        return pd.DataFrame()

    def create_chart_attachment(self, ticker: str, stock_data: pd.DataFrame) -> tuple:
        """
        Creates a PNG chart and returns it as bytes along with CID for email attachment.
        
        Args:
            ticker: Stock ticker symbol
            stock_data: DataFrame with stock data for current year
            
        Returns:
            tuple: (chart_bytes, content_id) or (None, None) if failed
        """
        try:
            if stock_data.empty:
                return None, None
            
            # Calculate 1-year return to determine line color
            first_price = stock_data['Close'].iloc[0]
            last_price = stock_data['Close'].iloc[-1]
            yearly_return = (last_price - first_price) / first_price
            
            # Set color based on performance: green if up, red if down
            line_color = '#22c55e' if yearly_return >= 0 else '#ef4444'
            fill_color = 'rgba(34, 197, 94, 0.1)' if yearly_return >= 0 else 'rgba(239, 68, 68, 0.1)'
            
            # Use proper weekly resampling that aligns to week boundaries
            # 'W' resamples to weekly periods ending on Sunday
            volume_resampled = stock_data['Volume'].resample('W').mean()
            
            fig = go.Figure()
            
            fig.add_trace(
                go.Scatter(
                    x=stock_data.index,
                    y=stock_data['Close'],
                    mode='lines',
                    name='Close Price',
                    line=dict(width=2, color=line_color),
                    fill='tonexty',
                    fillcolor=fill_color
                )
            )
            
            fig.add_trace(
                go.Bar(
                    x=volume_resampled.index,
                    y=volume_resampled.values,
                    name='Volume (Weekly Avg)',
                    yaxis='y2',
                    opacity=0.7,
                    marker_color='rgba(156, 163, 175, 0.8)',
                    showlegend=False
                    # Removed fixed width - let Plotly handle it naturally with proper weekly periods
                )
            )
            
            fig.update_layout(
                height=500,
                template='plotly_white',
                font=dict(size=12),
                showlegend=False,
                xaxis=dict(
                    title="Date",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgray',
                    range=[stock_data.index[0], stock_data.index[-1]]
                ),
                yaxis=dict(
                    title="Price (USD)",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgray'
                ),
                yaxis2=dict(
                    overlaying='y',
                    side='right',
                    showgrid=False,
                    showticklabels=False,
                    range=[0, volume_resampled.max() * 3]
                ),
                margin=dict(l=50, r=50, t=60, b=50)
            )
            
            img_bytes = pio.to_image(fig, format='png', width=1200, height=500, scale=2)
            content_id = f"stock_chart_{ticker.lower()}"
            
            return img_bytes, content_id
            
        except Exception as e:
            print(f"Error creating chart: {str(e)}")
            return None, None

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
        Only formats columns that appear to be unformatted (not custom renamed),
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
        Returns True if the column name is NOT in our custom mappings (meaning it needs generic formatting).
        Returns False if the column name IS in our custom mappings (meaning it's already custom formatted).
        """
        return str(column_name) not in self.all_custom_names

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

        str_value = str(value).strip()
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
        return self.rename_columns(filtered_df, self.raw_df_mappings)

    def format_metrics_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Organizes the DataFrame for email presentation by renaming columns.
        """
        return self.rename_columns(df, self.metrics_df_mappings)

    def rename_columns(self, df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
        """
        Renames columns in the DataFrame according to a provided mapping.
        """
        return df.rename(columns=mapping, inplace=False)

    def build_email_content(self, raw_df: pd.DataFrame, metrics_df: pd.DataFrame) -> str:
        """
        Converts multiple DataFrames to HTML tables for the email body.
        """
        raw_df_formatted = self.format_dataframe(raw_df)
        raw_df_formatted = self.format_column_headers(raw_df_formatted)
        
        metrics_df_formatted = self.format_dataframe(metrics_df)
        metrics_df_formatted = self.format_column_headers(metrics_df_formatted)

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
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }}
        #raw-data-table {{ margin-bottom: 40px; }}
        #metrics-table {{ margin-top: 20px; }}
        </style>
        </head>
        <body>       

        <h3 class="section-header">Company Financials</h3>
        {raw_html_table}

        <h3 class="section-header">Calculated Ratios / Metrics</h3>
        {metrics_html_table}

        </body>
        </html>
        """
        return html_content

    def build_html_content_with_chart(self, raw_df: pd.DataFrame, metrics_df: pd.DataFrame, 
                                     ticker: str) -> tuple:
        """
        Build HTML content and return chart attachment info.
        
        Args:
            raw_df: Raw financial data DataFrame
            metrics_df: Calculated metrics DataFrame
            ticker: Stock ticker symbol
            
        Returns:
            tuple: (html_content, chart_attachment_data) where chart_attachment_data is
                   (chart_bytes, content_id, filename) or None if no chart
        """
        # Fetch stock data
        stock_data = self.fetch_stock_data(ticker)
        
        # Create chart attachment
        chart_bytes, content_id = self.create_chart_attachment(ticker, stock_data)
        chart_attachment_data = None
        
        if chart_bytes and content_id:
            chart_attachment_data = (chart_bytes, content_id, f"{ticker}_chart.png")
        
        # Format dataframes
        filtered_raw_df = self.format_raw_df(raw_df)
        filtered_metrics_df = self.format_metrics_df(metrics_df)
        
        raw_df_formatted = self.format_dataframe(filtered_raw_df)
        raw_df_formatted = self.format_column_headers(raw_df_formatted)
        
        metrics_df_formatted = self.format_dataframe(filtered_metrics_df)
        metrics_df_formatted = self.format_column_headers(metrics_df_formatted)

        raw_html_table = raw_df_formatted.to_html(index=False, border=0, justify="center")
        metrics_html_table = metrics_df_formatted.to_html(index=False, border=0, justify="center")
        
        # Build HTML with CID reference
        chart_html = ""
        if content_id:
            chart_html = f'<img src="cid:{content_id}" alt="{ticker} Stock Chart - Last 12 Months" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px;">'

        html_content = f"""
        <html>
        <head>
        <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        table {{ 
            border-collapse: collapse; 
            width: 100%; 
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 12px 8px; 
            text-align: center; 
        }}
        th {{ 
            background-color: #f8f9fa; 
            font-weight: bold;
            color: #2c3e50;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .section-header {{ 
            color: #2c3e50; 
            margin-top: 30px; 
            margin-bottom: 15px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 8px;
            font-size: 20px;
            font-weight: bold;
            text-align: left;  /* Left align the title */
        }}
        .chart-container {{ 
            background-color: #ffffff; /* White background instead of gray */
            padding: 20px; 
            border-radius: 8px; 
            margin: 25px 0;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        img {{
            max-width: 100% !important;
            width: 100% !important;
            height: auto !important;
            display: block;
            margin: 0 auto;
        }}
        </style>
        </head>
        <body>       

        {f'<div class="chart-container"><h3 class="section-header">{ticker} 1 Year Stock Performance</h3>{chart_html}</div>' if chart_html else ''}

        <h3 class="section-header">Company Financials</h3>
        {raw_html_table}

        <h3 class="section-header">Calculated Ratios / Metrics</h3>
        {metrics_html_table}

        </body>
        </html>
        """
        
        return html_content, chart_attachment_data