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
        
        self.all_custom_names = set(self.raw_df_mappings.values()) | set(self.metrics_df_mappings.values())
        self.news_limit = 5
        self.news_summary_chars = 220

    def fetch_stock_data(self, ticker: str) -> pd.DataFrame:
        """
        Fetches stock data for the current year using yfinance.
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period='1y')
            
            if not hist.empty:
                return hist
                
        except Exception as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
            
        return pd.DataFrame()

    def get_stock_performance_data(self, stock_data: pd.DataFrame) -> dict:
        """
        Calculate stock performance metrics from stock data.
        Returns dict with current_price, year_ago_price, price_change_pct, and price_change_abs.
        """
        if stock_data.empty:
            return {
                'current_price': None,
                'year_ago_price': None,
                'price_change_pct': None,
                'price_change_abs': None
            }
        
        try:
            current_price = stock_data['Close'].iloc[-1]
            year_ago_price = stock_data['Close'].iloc[0]
            price_change_abs = current_price - year_ago_price
            price_change_pct = (price_change_abs / year_ago_price) * 100
            
            return {
                'current_price': current_price,
                'year_ago_price': year_ago_price,
                'price_change_pct': price_change_pct,
                'price_change_abs': price_change_abs
            }
        except Exception as e:
            print(f"Error calculating stock performance: {str(e)}")
            return {
                'current_price': None,
                'year_ago_price': None,
                'price_change_pct': None,
                'price_change_abs': None
            }

    def create_chart_attachment(self, ticker: str, stock_data: pd.DataFrame) -> tuple:
        """
        Creates a PNG chart and returns it as bytes along with CID for email attachment.
        """
        try:
            if stock_data.empty:
                return None, None
            
            first_price = stock_data['Close'].iloc[0]
            last_price = stock_data['Close'].iloc[-1]
            yearly_return = (last_price - first_price) / first_price
            
            line_color = '#22c55e' if yearly_return >= 0 else '#ef4444'
            fill_color = 'rgba(34, 197, 94, 0.1)' if yearly_return >= 0 else 'rgba(239, 68, 68, 0.1)'
            
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

            if abs_value >= 1e12:
                formatted = f"{value / 1e12:.1f}T"
            elif abs_value >= 1e9:
                formatted = f"{value / 1e9:.1f}B"
            elif abs_value >= 1e6:
                formatted = f"{value / 1e6:.1f}M"
            elif abs_value >= 1e3:
                formatted = f"{value / 1e3:.1f}K"
            else:
                if isinstance(value, (int, np.integer)) or float(value).is_integer():
                    return str(int(float(value)))
                else:
                    return f"{float(value):.2f}".rstrip('0').rstrip('.')

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
            clean_value = str_value.replace(',', '').replace('$', '').replace('%', '')
            numeric_val = float(clean_value)

            abs_val = abs(numeric_val)
            if abs_val >= 1000:
                if abs_val >= 1e12:
                    abbreviated = f"{numeric_val / 1e12:.1f}T"
                elif abs_val >= 1e9:
                    abbreviated = f"{numeric_val / 1e9:.1f}B"
                elif abs_val >= 1e6:
                    abbreviated = f"{numeric_val / 1e6:.1f}M"
                else:
                    abbreviated = f"{numeric_val / 1e3:.1f}K"

                abbreviated = abbreviated.replace('.0', '')

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

    def _create_introduction_html(self, ticker: str) -> str:
        """
        Creates the HTML introduction section for the email.
        """
        return f'''
        <div class="intro-section">
            <p>This comprehensive financial analysis for <strong>{ticker}</strong> includes recent market performance, current market sentiment, sector analysis, latest news developments, and detailed financial metrics to provide you with a complete investment overview.</p>
        </div>
        '''

    def _create_stock_header(self, ticker: str, stock_performance: dict) -> str:
        """
        Creates the stock chart section header with current price and 1Y change.
        """
        current_price = stock_performance.get('current_price')
        price_change_pct = stock_performance.get('price_change_pct')
        
        if current_price is None or price_change_pct is None:
            return f"{ticker}"
        
        price_str = f"${current_price:.2f}"
        pct_change_str = f"{price_change_pct:+.2f}%"
        perf_class = self.get_performance_class(price_change_pct)
        
        return f'''
        {ticker} Stock Performance 
        <span style="font-size: 16px; margin-left: 15px;">
            <span style="color: #2c3e50; font-weight: normal;">{price_str}</span>
            <span class="{perf_class}" style="margin-left: 8px; font-weight: normal;">
                {pct_change_str} 1Y
            </span>
        </span>
        '''

    def _create_chart_html(self, content_id: str, ticker: str) -> str:
        """
        Creates the HTML for the stock chart display.
        """
        if content_id:
            return f'<img src="cid:{content_id}" alt="{ticker} Stock Chart - Last 12 Months" style="max-width:100%;height:auto;display:block;margin:0 auto;">'
        else:
            return ""

    def _format_sentiment_analysis(self, corporate_sentiment: float, retail_sentiment: float) -> str:
        """
        Creates formatted HTML for sentiment analysis display with consistent styling.
        """
        def get_sentiment_details(score):
            try:
                s = float(score)
            except Exception:
                return "N/A", "performance-neutral"

            if s > 0.05:
                return f"{s:+.2f}", "performance-positive"
            elif s < -0.05:
                return f"{s:+.2f}", "performance-negative"
            else:
                return f"{s:+.2f}", "performance-neutral"
        
        corp_value, corp_class = get_sentiment_details(corporate_sentiment)
        retail_value, retail_class = get_sentiment_details(retail_sentiment)

        return f'''
        <div class="info-container">
            <div class="info-line">
                <span class="info-label">Corporate Sentiment:</span>
                <span class="info-value {corp_class}">{corp_value}</span>
            </div>
            <div class="info-line">
                <span class="info-label">Retail Sentiment:</span>
                <span class="info-value {retail_class}">{retail_value}</span>
            </div>
        </div>
        '''

    def _format_sector_performance(self, ticker: str, sector_performance: dict) -> str:
        """
        Creates formatted HTML for sector performance display with consistent styling.
        """
        if not sector_performance or sector_performance.get("sector") == "Unknown":
            return '<div class="info-container">Sector information not available</div>'
        
        sector = sector_performance.get("sector", "N/A")
        sector_etf = sector_performance.get("sector_etf", "N/A")
        ticker_performance_pct = sector_performance.get("ticker_1y_performance_pct", 0.0)
        sector_performance_pct = sector_performance.get("sector_1y_performance_pct", 0.0)
        opportunity_cost_pct = ticker_performance_pct - sector_performance_pct

        sector_perf_class = self.get_performance_class(sector_performance_pct)
        ticker_perf_class = self.get_performance_class(ticker_performance_pct)
        opportunity_cost_class = self.get_performance_class(opportunity_cost_pct)

        return f'''
        <div class="info-container">
            <div class="info-line">
                <span class="info-label">Sector:</span>
                <span class="info-value">{sector}</span>
            </div>
            <div class="info-line">
                <span class="info-label">Valuation ETF:</span>
                <span class="info-value">{sector_etf}</span>
            </div>
            <div class="info-line">
                <span class="info-label">Sector Performance (1Y):</span>
                <span class="info-value {sector_perf_class}">{sector_performance_pct:+.2f}%</span>
            </div>
            <div class="info-line">
                <span class="info-label">{ticker} Performance (1Y):</span>
                <span class="info-value {ticker_perf_class}">{ticker_performance_pct:+.2f}%</span>
            </div>
            <div class="info-line">
                <span class="info-label">Opportunity Cost (1Y):</span>
                <span class="info-value {opportunity_cost_class}">{opportunity_cost_pct:+.2f}%</span>
            </div>
        </div>
        '''

    def get_performance_class(self, performance_pct: float) -> str:
        """
        Get the performance class based on the performance percentage.
        """
        if performance_pct > 0:
            return "performance-positive"
        elif performance_pct < 0:
            return "performance-negative"
        else:
            return "performance-neutral"

    def _build_news_html(self, news_df: pd.DataFrame) -> str:
        if news_df is None or news_df.empty:
            return ""

        df = news_df.copy()

        if "published_at" in df.columns:
            with pd.option_context('mode.chained_assignment', None):
                df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
            df = df.sort_values("published_at", ascending=False, na_position="last")

        items = []
        for _, row in df.head(self.news_limit).iterrows():
            headline = str(row.get("headline", "") or "").strip()
            summary = str(row.get("summary", "") or "").strip()
            url = str(row.get("url", "") or "").strip()

            if not headline and not summary:
                continue

            if summary and len(summary) > self.news_summary_chars:
                summary = summary[: self.news_summary_chars - 1].rstrip() + "…"

            headline_html = f'<div class="news-headline">{headline}</div>' if headline else ""
            summary_html = f'<p class="news-summary">{summary}</p>' if summary else ""
            link_html = f' <a href="{url}" target="_blank" rel="noopener noreferrer">Read More...</a>' if url else ""

            items.append(f'<li class="news-item">{headline_html}{summary_html}{link_html}</li>')

        if not items:
            return ""
        return f'<ul class="news-list">{"".join(items)}</ul>'

    def build_html_content(
        self,
        raw_df: pd.DataFrame,
        metrics_df: pd.DataFrame,
        ticker: str,
        corporate_sentiment: float,
        retail_sentiment: float,
        news_df: pd.DataFrame,
        sector_performance: dict = None,
    ) -> tuple:
        """
        Build HTML content and return chart attachment info.
        Returns:
            (html_content, (chart_bytes, content_id, filename)|None)
        """
        # 1. Introduction HTML (first in email)
        intro_html = self._create_introduction_html(ticker)

        # 2. Stock data and chart preparation (second in email)
        stock_data = self.fetch_stock_data(ticker)
        stock_performance = self.get_stock_performance_data(stock_data)
        chart_bytes, content_id = self.create_chart_attachment(ticker, stock_data)
        chart_attachment_data = (chart_bytes, content_id, f"{ticker}_chart.png") if (chart_bytes and content_id) else None
        
        stock_header = self._create_stock_header(ticker, stock_performance)
        chart_html = self._create_chart_html(content_id, ticker)

        # 3. Sentiment HTML (third in email)
        sentiment_html = self._format_sentiment_analysis(corporate_sentiment, retail_sentiment)

        # 4. Sector HTML (fourth in email)
        sector_html = self._format_sector_performance(ticker, sector_performance)

        # 5. News HTML (fifth in email)
        news_html = self._build_news_html(news_df)

        # 6. Financial DataFrames (sixth and seventh in email)
        filtered_raw_df = self.format_raw_df(raw_df)
        filtered_metrics_df = self.format_metrics_df(metrics_df)

        raw_df_formatted = self.format_column_headers(self.format_dataframe(filtered_raw_df))
        metrics_df_formatted = self.format_column_headers(self.format_dataframe(filtered_metrics_df))

        raw_html_table = raw_df_formatted.to_html(index=False, border=0, justify="center")
        metrics_html_table = metrics_df_formatted.to_html(index=False, border=0, justify="center")

        # Assemble HTML in display order
        html_content = f"""
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.55;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            
            .intro-section {{
                background: #f0f8ff;
                border-left: 4px solid #3498db;
                padding: 15px 20px;
                margin: 20px 0 30px 0;
                border-radius: 4px;
                font-size: 16px;
            }}
            
            .section-header {{
                color: #2c3e50;
                margin: 28px 0 12px 0;
                border-bottom: 2px solid #3498db;
                padding-bottom: 6px;
                font-size: 20px;
                font-weight: bold;
                text-align: left;
            }}
            
            .context-header {{
                color: #2c3e50;
                margin: 35px 0 20px 0;
                border-bottom: 3px solid #e74c3c;
                padding-bottom: 8px;
                font-size: 22px;
                font-weight: bold;
                text-align: left;
            }}
            
            .financial-header {{
                color: #2c3e50;
                margin: 35px 0 20px 0;
                border-bottom: 3px solid #27ae60;
                padding-bottom: 8px;
                font-size: 22px;
                font-weight: bold;
                text-align: left;
            }}
            
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 26px;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 10px 8px;
                text-align: center;
            }}
            
            th {{
                background-color: #f8f9fa;
                font-weight: bold;
                color: #2c3e50;
            }}
            
            .info-container {{
                background: #f8f9fa;
                border-left: 4px solid #3498db;
                padding: 15px 20px;
                margin: 15px 0;
                border-radius: 4px;
            }}
            .info-line {{
                display: flex;
                align-items: center;
                justify-content: flex-start;
                margin-bottom: 8px;
                font-size: 14px;
                min-height: 20px;
            }}
            
            .info-line:last-child {{
                margin-bottom: 0;
            }}
            
            .info-label {{
                font-weight: 600;
                margin-right: 12px;
                min-width: 180px;
                flex-shrink: 0;
                text-align: left;
            }}
            
            .info-value {{
                font-weight: bold;
                font-size: 14px;
                flex-grow: 0;
                text-align: left;
            }}
            
            .performance-positive {{
                color: #22c55e;
            }}
            
            .performance-negative {{
                color: #ef4444;
            }}
            
            .performance-neutral {{
                color: #6b7280;
            }}
            
            .news-list {{
                list-style: none;
                padding-left: 0;
                margin: 0;
            }}
            
            .news-item {{
                margin: 0 0 14px 0;
            }}
            
            .news-headline {{
                margin: 0 0 4px 0;
                font-weight: 600;
            }}
            
            .news-summary {{
                margin: 0;
            }}
            
            a {{
                color: #2563eb; text-decoration: none;
            }}
            
            a:hover {{
                text-decoration: underline;
            }}
        </style>
        </head>
        <body>

        {intro_html}

        <h3 class="section-header">{stock_header}</h3>
        {chart_html}

        <h3 class="section-header">Sentiment Analysis</h3>
        {sentiment_html}

        <h3 class="section-header">Sector Analysis</h3>
        {sector_html if sector_html else '<div class="info-container">Sector information not available</div>'}
            
        <h3 class="section-header">News</h3>
        {news_html if news_html else '<div class="info-container">No recent news available</div>'}

        <h3 class="section-header">Company Financials</h3>
        {raw_html_table}

        <h3 class="section-header">Calculated Ratios / Metrics</h3>
        {metrics_html_table}

        </body>
        </html>
        """
        return html_content, chart_attachment_data