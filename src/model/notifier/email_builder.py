import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.io as pio


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

    # ===== STOCK DATA METHODS =====
    def fetch_stock_data(self, ticker: str) -> pd.DataFrame:
        """Fetches stock data for the current year using yfinance."""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period='1y')
            return hist if not hist.empty else pd.DataFrame()
        except Exception as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
            return pd.DataFrame()

    def get_stock_performance_data(self, stock_data: pd.DataFrame) -> dict:
        """Calculate stock performance metrics from stock data."""
        if stock_data.empty:
            return self._empty_performance_dict()
        
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
            return self._empty_performance_dict()

    def _empty_performance_dict(self) -> dict:
        """Helper to return empty performance data structure."""
        return {
            'current_price': None,
            'year_ago_price': None,
            'price_change_pct': None,
            'price_change_abs': None
        }

    # ===== CHART CREATION METHODS =====
    def create_chart_attachment(self, ticker: str, stock_data: pd.DataFrame) -> tuple:
        """Creates a PNG chart and returns it as bytes along with CID for email attachment."""
        try:
            if stock_data.empty:
                return None, None
            
            chart_config = self._prepare_chart_config(stock_data)
            fig = self._create_plotly_figure(stock_data, chart_config)
            
            img_bytes = pio.to_image(fig, format='png', width=1200, height=500, scale=2)
            content_id = f"stock_chart_{ticker.lower()}"
            
            return img_bytes, content_id
            
        except Exception as e:
            print(f"Error creating chart: {str(e)}")
            return None, None

    def _prepare_chart_config(self, stock_data: pd.DataFrame) -> dict:
        """Prepare chart configuration including colors and volume data."""
        first_price = stock_data['Close'].iloc[0]
        last_price = stock_data['Close'].iloc[-1]
        yearly_return = (last_price - first_price) / first_price
        
        line_color = '#22c55e' if yearly_return >= 0 else '#ef4444'
        fill_color = 'rgba(34, 197, 94, 0.1)' if yearly_return >= 0 else 'rgba(239, 68, 68, 0.1)'
        
        volume_binned = self._prepare_volume_data(stock_data)
        
        return {
            'line_color': line_color,
            'fill_color': fill_color,
            'volume_binned': volume_binned
        }

    def _prepare_volume_data(self, stock_data: pd.DataFrame) -> pd.Series:
        """Prepare weekly volume data for chart."""
        start = stock_data.index[0].normalize()
        end = stock_data.index[-1].normalize()
        bins = pd.date_range(start=start, end=end, freq="7D")

        volume_binned = stock_data['Volume'].groupby(
            pd.cut(stock_data.index, bins), observed=False
        ).mean()

        bin_centers = bins[:-1] + (bins[1] - bins[0]) / 2
        volume_binned.index = bin_centers
        
        return volume_binned

    def _create_plotly_figure(self, stock_data: pd.DataFrame, chart_config: dict) -> go.Figure:
        """Create the complete plotly figure with price and volume traces."""
        fig = go.Figure()
        
        # Add price trace
        fig.add_trace(
            go.Scatter(
                x=stock_data.index,
                y=stock_data['Close'],
                mode='lines',
                name='Close Price',
                line=dict(width=2, color=chart_config['line_color']),
                fill='tonexty',
                fillcolor=chart_config['fill_color']
            )
        )
        
        # Add volume trace
        volume_binned = chart_config['volume_binned']
        fig.add_trace(
            go.Bar(
                x=volume_binned.index,
                y=volume_binned.values,
                name='Volume (Weekly Avg)',
                yaxis='y2',
                opacity=0.7,
                marker_color='rgba(156, 163, 175, 0.8)',
                showlegend=False
            )
        )
        
        fig.update_layout(**self._get_chart_layout(stock_data, volume_binned))
        return fig

    def _get_chart_layout(self, stock_data: pd.DataFrame, volume_binned: pd.Series) -> dict:
        """Get the layout configuration for the plotly chart."""
        return {
            'height': 500,
            'template': 'plotly_white',
            'font': dict(size=12),
            'showlegend': False,
            'xaxis': dict(
                title="Date",
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                range=[stock_data.index[0], stock_data.index[-1]]
            ),
            'yaxis': dict(
                title="Price (USD)",
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            ),
            'yaxis2': dict(
                overlaying='y',
                side='right',
                showgrid=False,
                showticklabels=False,
                range=[0, volume_binned.max() * 3]
            ),
            'margin': dict(l=50, r=50, t=60, b=50)
        }

    # ===== DATAFRAME FORMATTING METHODS =====
    def format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Formats numeric values in DataFrame with abbreviated suffixes (K, M, B, T)."""
        df_formatted = df.copy()

        for col in df_formatted.columns:
            if pd.api.types.is_numeric_dtype(df_formatted[col]):
                df_formatted[col] = df_formatted[col].apply(self._format_numeric_value)
            else:
                df_formatted[col] = df_formatted[col].apply(self._format_if_numeric)

        return df_formatted

    def format_column_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format column headers from snake_case to Title Case."""
        df_formatted = df.copy()
        df_formatted.columns = [
            self._format_column_name(col) if self._needs_formatting(col) else col 
            for col in df_formatted.columns
        ]
        return df_formatted

    def format_raw_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Organizes the DataFrame for email presentation."""
        filtered_df = df.drop(columns=["date", "form_type"])
        return self.rename_columns(filtered_df, self.raw_df_mappings)

    def format_metrics_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Organizes the DataFrame for email presentation."""
        return self.rename_columns(df, self.metrics_df_mappings)

    def rename_columns(self, df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
        """Renames columns in the DataFrame according to a provided mapping."""
        return df.rename(columns=mapping, inplace=False)

    def _needs_formatting(self, column_name):
        """Determines if a column name needs formatting."""
        return str(column_name) not in self.all_custom_names

    def _format_column_name(self, column_name):
        """Converts snake_case column names to Title Case."""
        return str(column_name).replace('_', ' ').title()

    # ===== NUMERIC FORMATTING HELPERS =====
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
            formatted = self._get_abbreviated_value(value, abs_value)
            return formatted.replace('.0', '')
        except (ValueError, TypeError, OverflowError):
            return value

    def _get_abbreviated_value(self, value, abs_value):
        """Get abbreviated value based on magnitude."""
        if abs_value >= 1e12:
            return f"{value / 1e12:.1f}T"
        elif abs_value >= 1e9:
            return f"{value / 1e9:.1f}B"
        elif abs_value >= 1e6:
            return f"{value / 1e6:.1f}M"
        elif abs_value >= 1e3:
            return f"{value / 1e3:.1f}K"
        else:
            if isinstance(value, (int, np.integer)) or float(value).is_integer():
                return str(int(float(value)))
            else:
                return f"{float(value):.2f}".rstrip('0').rstrip('.')

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
            
            return self._format_string_numeric(str_value, numeric_val)
        except (ValueError, TypeError):
            return value

    def _format_string_numeric(self, original_str, numeric_val):
        """Format string-based numeric values preserving original symbols."""
        abs_val = abs(numeric_val)
        if abs_val >= 1000:
            abbreviated = self._get_abbreviated_value(numeric_val, abs_val).replace('.0', '')
            
            if '$' in original_str:
                abbreviated = '$' + abbreviated
            if '%' in original_str:
                abbreviated = abbreviated + '%'
                
            return abbreviated
        else:
            return original_str

    # ===== HTML SECTION BUILDERS =====
    def _create_introduction_html(self, ticker: str) -> str:
        """Creates the HTML introduction section for the email."""
        return f'''
        <div class="intro-section">
            <p>This comprehensive financial analysis for <strong>{ticker}</strong> includes recent market performance, current market sentiment, sector analysis, earnings analysis, latest news developments, and detailed financial metrics to provide you with a complete investment overview.</p>
        </div>
        '''

    def _create_stock_header(self, ticker: str, stock_performance: dict) -> str:
        """Creates the stock chart section header with current price and 1Y change."""
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
        """Creates the HTML for the stock chart display."""
        if content_id:
            return f'<img src="cid:{content_id}" alt="{ticker} Stock Chart - Last 12 Months" style="max-width:100%;height:auto;display:block;margin:0 auto;">'
        else:
            return ""

    # ===== SENTIMENT ANALYSIS =====
    def _format_sentiment_analysis(self, corporate_sentiment: float, retail_sentiment: float) -> str:
        """Creates formatted HTML for sentiment analysis display."""
        corp_value, corp_class = self._get_sentiment_details(corporate_sentiment)
        retail_value, retail_class = self._get_sentiment_details(retail_sentiment)

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

    def _get_sentiment_details(self, score):
        """Get sentiment value and CSS class for display."""
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

    # ===== SECTOR PERFORMANCE =====
    def _format_sector_performance(self, ticker: str, sector_performance: dict) -> str:
        """Creates formatted HTML for sector performance display."""
        if not sector_performance or sector_performance.get("sector") == "Unknown":
            return '<div class="info-container">Sector information not available</div>'
        
        sector_data = self._extract_sector_data(sector_performance)
        performance_classes = self._get_sector_performance_classes(sector_data)
        
        return f'''
        <div class="info-container">
            <div class="info-line">
                <span class="info-label">Sector:</span>
                <span class="info-value">{sector_data['sector']}</span>
            </div>
            <div class="info-line">
                <span class="info-label">Valuation ETF:</span>
                <span class="info-value">{sector_data['sector_etf']}</span>
            </div>
            <div class="info-line">
                <span class="info-label">Sector Performance (1Y):</span>
                <span class="info-value {performance_classes['sector']}">{sector_data['sector_performance_pct']:+.2f}%</span>
            </div>
            <div class="info-line">
                <span class="info-label">{ticker} Performance (1Y):</span>
                <span class="info-value {performance_classes['ticker']}">{sector_data['ticker_performance_pct']:+.2f}%</span>
            </div>
            <div class="info-line">
                <span class="info-label">Opportunity Cost (1Y):</span>
                <span class="info-value {performance_classes['opportunity']}">{sector_data['opportunity_cost_pct']:+.2f}%</span>
            </div>
        </div>
        '''

    def _extract_sector_data(self, sector_performance: dict) -> dict:
        """Extract and calculate sector performance data."""
        sector = sector_performance.get("sector", "N/A")
        sector_etf = sector_performance.get("sector_etf", "N/A")
        ticker_performance_pct = sector_performance.get("ticker_1y_performance_pct", 0.0)
        sector_performance_pct = sector_performance.get("sector_1y_performance_pct", 0.0)
        opportunity_cost_pct = ticker_performance_pct - sector_performance_pct
        
        return {
            'sector': sector,
            'sector_etf': sector_etf,
            'ticker_performance_pct': ticker_performance_pct,
            'sector_performance_pct': sector_performance_pct,
            'opportunity_cost_pct': opportunity_cost_pct
        }

    def _get_sector_performance_classes(self, sector_data: dict) -> dict:
        """Get CSS classes for sector performance values."""
        return {
            'sector': self.get_performance_class(sector_data['sector_performance_pct']),
            'ticker': self.get_performance_class(sector_data['ticker_performance_pct']),
            'opportunity': self.get_performance_class(sector_data['opportunity_cost_pct'])
        }

    # ===== EARNINGS ANALYSIS =====
    def _format_earnings_analysis(self, earnings_df: pd.DataFrame, earnings_estimate: dict) -> str:
        """Creates formatted HTML for earnings analysis display."""
        html_parts = []
        
        # Historical earnings section
        if earnings_df is None or earnings_df.empty:
            html_parts.append('<div class="info-container">No historical earnings data available</div>')
        else:
            historical_html = self._format_historical_earnings(earnings_df)
            if historical_html:
                html_parts.extend(historical_html)
        
        # Next earnings estimate section
        estimate_html = self._format_earnings_estimate(earnings_estimate)
        html_parts.extend(estimate_html)
        
        return ''.join(html_parts)

    def _format_historical_earnings(self, earnings_df: pd.DataFrame) -> list:
        """Format historical earnings data into HTML."""
        try:
            earnings_display = self._prepare_earnings_display_df(earnings_df)
            
            earnings_html_table = earnings_display.to_html(
                index=False, 
                border=0, 
                justify="center",
                classes="earnings-table",
                table_id="historical-earnings",
                escape=False
            )
            
            earnings_html_table = earnings_html_table.replace(
                'class="earnings-table"',
                'class="earnings-table" style="font-size: 14px;"'
            )
            
            return [
                '<h4 style="color: #2c3e50; margin: 20px 0 10px 0; font-size: 16px;">Historical Quarterly Earnings</h4>',
                earnings_html_table
            ]
            
        except Exception as e:
            print(f"Error formatting historical earnings data: {str(e)}")
            return ['<div class="info-container">Error processing historical earnings data</div>']

    def _prepare_earnings_display_df(self, earnings_df: pd.DataFrame) -> pd.DataFrame:
        """Prepare earnings DataFrame for display with proper formatting."""
        earnings_display = earnings_df.copy()
        
        # Column mapping
        column_mapping = {
            'fiscalDateEnding': 'Fiscal Date',
            'reportedEPS': 'Reported EPS',
            'estimatedEPS': 'Estimated EPS', 
            'surprisePercentage': 'EPS Surprise %',
            'oneDayReturn': '1-Day Return',
            'fiveDayReturn': '5-Day Return'
        }
        earnings_display.rename(columns=column_mapping, inplace=True)
        
        # Format EPS columns
        for col in ['Reported EPS', 'Estimated EPS']:
            if col in earnings_display.columns:
                earnings_display[col] = pd.to_numeric(earnings_display[col], errors='coerce')
                earnings_display[col] = earnings_display[col].apply(
                    lambda x: f"${x:.2f}" if pd.notna(x) else "N/A"
                )
        
        # Format percentage columns with color coding
        percentage_columns = {
            'EPS Surprise %': False,  # No sign prefix
            '1-Day Return': True,     # Include sign prefix
            '5-Day Return': True      # Include sign prefix
        }
        
        for col, include_sign in percentage_columns.items():
            if col in earnings_display.columns:
                earnings_display[col] = pd.to_numeric(earnings_display[col], errors='coerce')
                earnings_display[col] = earnings_display[col].apply(
                    lambda x: self._format_performance_value(
                        x, is_percentage=True, suffix='%', include_sign=include_sign
                    ) if pd.notna(x) else "N/A"
                )
        
        return earnings_display

    def _format_earnings_estimate(self, earnings_estimate: dict) -> list:
        """Format earnings estimate data into HTML."""
        html_parts = ['<h4 style="color: #2c3e50; margin: 25px 0 10px 0; font-size: 16px;">Next Earnings Estimate</h4>']
        
        if not earnings_estimate or not (earnings_estimate.get('nextEarningsDate') or earnings_estimate.get('estimatedEPS')):
            html_parts.append('<div class="info-container">No upcoming earnings estimate available</div>')
            return html_parts
        
        estimate_data = self._extract_earnings_estimate_data(earnings_estimate)
        
        estimate_html = f'''
        <div class="info-container">
            <div class="info-line">
                <span class="info-label">Expected Earnings:</span>
                <span class="info-value">{estimate_data['formatted_date']}</span>
            </div>
            <div class="info-line">
                <span class="info-label">Estimated EPS:</span>
                <span class="info-value">{estimate_data['formatted_eps']}</span>
            </div>
            <div class="info-line">
                <span class="info-label">Forward P/E:</span>
                <span class="info-value">{estimate_data['formatted_forward_pe']}</span>
            </div>
            <div class="info-line">
                <span class="info-label">PEG:</span>
                <span class="info-value">{estimate_data['formatted_peg_ratio']}</span>
            </div>
        </div>
        '''
        html_parts.append(estimate_html)
        
        return html_parts

    def _extract_earnings_estimate_data(self, earnings_estimate: dict) -> dict:
        """Extract and format earnings estimate data."""
        next_date = earnings_estimate.get('nextEarningsDate')
        estimated_eps = earnings_estimate.get('estimatedEPS')
        forward_pe = earnings_estimate.get('forwardPE')
        peg_ratio = earnings_estimate.get('pegRatio')
        
        formatted_date = self._format_earnings_date(next_date)
        formatted_eps = self._format_earnings_value(estimated_eps, prefix='$', decimals=2)
        formatted_forward_pe = self._format_earnings_value(forward_pe, decimals=2)
        formatted_peg_ratio = self._format_earnings_value(peg_ratio, decimals=2)
        
        return {
            'formatted_date': formatted_date,
            'formatted_eps': formatted_eps,
            'formatted_forward_pe': formatted_forward_pe,
            'formatted_peg_ratio': formatted_peg_ratio
        }

    def _format_earnings_date(self, date_value) -> str:
        """Format earnings date for display."""
        if not date_value:
            return "N/A"
        
        if hasattr(date_value, 'strftime'):
            return date_value.strftime('%Y-%m-%d')
        else:
            return str(date_value)

    def _format_earnings_value(self, value, prefix='', decimals=2) -> str:
        """Format earnings-related numeric values."""
        if not value:
            return "N/A"
        
        try:
            numeric_value = float(value)
            formatted = f"{numeric_value:.{decimals}f}"
            return f"{prefix}{formatted}" if prefix else formatted
        except (ValueError, TypeError):
            return str(value) if value else "N/A"

    def _format_performance_value(self, value, is_percentage=False, suffix='', include_sign=False):
        """Format a performance value with appropriate color coding."""
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            return "N/A"
        
        color_class = self._get_performance_color_class(numeric_value)
        formatted_value = self._get_formatted_performance_string(
            numeric_value, is_percentage, suffix, include_sign
        )
        
        return f'<span class="{color_class}">{formatted_value}</span>'

    def _get_performance_color_class(self, value: float) -> str:
        """Get CSS class for performance value color coding."""
        if value > 0:
            return "performance-positive"
        elif value < 0:
            return "performance-negative"
        else:
            return "performance-neutral"

    def _get_formatted_performance_string(self, value: float, is_percentage: bool, 
                                        suffix: str, include_sign: bool) -> str:
        """Format performance value string with proper precision and symbols."""
        if is_percentage:
            if include_sign:
                return f"{value:+.1f}{suffix}"
            else:
                return f"{value:.1f}{suffix}"
        else:
            return f"{value:.2f}{suffix}"
    
    def get_performance_class(self, performance_pct: float) -> str:
        """Get the performance class based on the performance percentage."""
        return self._get_performance_color_class(performance_pct)

    # ===== NEWS SECTION =====
    def _build_news_html(self, news_df: pd.DataFrame) -> str:
        """Build HTML for news section."""
        if news_df is None or news_df.empty:
            return ""

        df = self._prepare_news_df(news_df)
        news_items = self._create_news_items(df)
        
        if not news_items:
            return ""
            
        return f'<ul class="news-list">{"".join(news_items)}</ul>'

    def _prepare_news_df(self, news_df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and sort news DataFrame."""
        df = news_df.copy()

        if "published_at" in df.columns:
            with pd.option_context('mode.chained_assignment', None):
                df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
            df = df.sort_values("published_at", ascending=False, na_position="last")

        return df

    def _create_news_items(self, df: pd.DataFrame) -> list:
        """Create individual news item HTML."""
        items = []
        
        for _, row in df.head(self.news_limit).iterrows():
            headline = str(row.get("headline", "") or "").strip()
            summary = str(row.get("summary", "") or "").strip()
            url = str(row.get("url", "") or "").strip()

            if not headline and not summary:
                continue

            news_item_html = self._format_single_news_item(headline, summary, url)
            if news_item_html:
                items.append(news_item_html)

        return items

    def _format_single_news_item(self, headline: str, summary: str, url: str) -> str:
        """Format a single news item into HTML."""
        if summary and len(summary) > self.news_summary_chars:
            summary = summary[: self.news_summary_chars - 1].rstrip() + "…"

        headline_html = f'<div class="news-headline">{headline}</div>' if headline else ""
        summary_html = f'<p class="news-summary">{summary}</p>' if summary else ""
        link_html = f' <a href="{url}" target="_blank" rel="noopener noreferrer">Read More...</a>' if url else ""

        return f'<li class="news-item">{headline_html}{summary_html}{link_html}</li>'

    def build_html_content(
        self,
        raw_df: pd.DataFrame,
        metrics_df: pd.DataFrame,
        ticker: str,
        corporate_sentiment: float,
        retail_sentiment: float,
        news_df: pd.DataFrame,
        sector_performance: dict,
        earnings_df: pd.DataFrame,
        earnings_estimate: dict,
    ) -> tuple:
        """
        Build HTML content and return chart attachment info.
        Returns: (html_content, (chart_bytes, content_id, filename)|None)
        """
        sections = self._gather_html_sections(
            ticker, raw_df, metrics_df, corporate_sentiment, retail_sentiment,
            news_df, sector_performance, earnings_df, earnings_estimate
        )
        
        html_content = self._build_complete_html(sections)
        
        return html_content, sections['chart_attachment_data']

    def _gather_html_sections(self, ticker: str, raw_df: pd.DataFrame, metrics_df: pd.DataFrame,
                             corporate_sentiment: float, retail_sentiment: float, news_df: pd.DataFrame,
                             sector_performance: dict, earnings_df: pd.DataFrame, 
                             earnings_estimate: dict) -> dict:
        """Gather all HTML sections and data needed for the email."""
        intro_html = self._create_introduction_html(ticker)

        stock_data = self.fetch_stock_data(ticker)
        stock_performance = self.get_stock_performance_data(stock_data)
        chart_bytes, content_id = self.create_chart_attachment(ticker, stock_data)
        chart_attachment_data = (chart_bytes, content_id, f"{ticker}_chart.png") if (chart_bytes and content_id) else None
        
        stock_header = self._create_stock_header(ticker, stock_performance)
        chart_html = self._create_chart_html(content_id, ticker)

        sentiment_html = self._format_sentiment_analysis(corporate_sentiment, retail_sentiment)
        sector_html = self._format_sector_performance(ticker, sector_performance)
        earnings_html = self._format_earnings_analysis(earnings_df, earnings_estimate)
        news_html = self._build_news_html(news_df)

        raw_html_table, metrics_html_table = self._prepare_financial_tables(raw_df, metrics_df)

        return {
            'intro_html': intro_html,
            'stock_header': stock_header,
            'chart_html': chart_html,
            'sentiment_html': sentiment_html,
            'sector_html': sector_html,
            'earnings_html': earnings_html,
            'news_html': news_html,
            'raw_html_table': raw_html_table,
            'metrics_html_table': metrics_html_table,
            'chart_attachment_data': chart_attachment_data
        }

    def _prepare_financial_tables(self, raw_df: pd.DataFrame, metrics_df: pd.DataFrame) -> tuple:
        """Prepare formatted financial tables."""
        filtered_raw_df = self.format_raw_df(raw_df)
        filtered_metrics_df = self.format_metrics_df(metrics_df)

        raw_df_formatted = self.format_column_headers(self.format_dataframe(filtered_raw_df))
        metrics_df_formatted = self.format_column_headers(self.format_dataframe(filtered_metrics_df))

        raw_html_table = raw_df_formatted.to_html(index=False, border=0, justify="center")
        metrics_html_table = metrics_df_formatted.to_html(index=False, border=0, justify="center")

        return raw_html_table, metrics_html_table

    def _build_complete_html(self, sections: dict) -> str:
        """Build the complete HTML email content."""
        return f"""
        <html>
        <head>
        <meta charset="utf-8">
        {self._get_css_styles()}
        </head>
        <body>

        {sections['intro_html']}

        <h3 class="section-header">{sections['stock_header']}</h3>
        {sections['chart_html']}

        <h3 class="section-header">Sentiment Analysis</h3>
        {sections['sentiment_html']}

        <h3 class="section-header">Sector Analysis</h3>
        {sections['sector_html'] if sections['sector_html'] else '<div class="info-container">Sector information not available</div>'}

        <h3 class="section-header">Earnings Analysis</h3>
        {sections['earnings_html'] if sections['earnings_html'] else '<div class="info-container">No earnings data available</div>'}
            
        <h3 class="section-header">News</h3>
        {sections['news_html'] if sections['news_html'] else '<div class="info-container">No recent news available</div>'}

        <h3 class="section-header">Company Financials</h3>
        {sections['raw_html_table']}

        <h3 class="section-header">Calculated Ratios / Metrics</h3>
        {sections['metrics_html_table']}

        </body>
        </html>
        """

    def _get_css_styles(self) -> str:
        """Return the CSS styles for the email."""
        return '''
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.55;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .intro-section {
                background: #f0f8ff;
                border-left: 4px solid #3498db;
                padding: 15px 20px;
                margin: 20px 0 30px 0;
                border-radius: 4px;
                font-size: 16px;
            }
            
            .section-header {
                color: #2c3e50;
                margin: 28px 0 12px 0;
                border-bottom: 2px solid #3498db;
                padding-bottom: 6px;
                font-size: 20px;
                font-weight: bold;
                text-align: left;
            }
            
            .context-header {
                color: #2c3e50;
                margin: 35px 0 20px 0;
                border-bottom: 3px solid #e74c3c;
                padding-bottom: 8px;
                font-size: 22px;
                font-weight: bold;
                text-align: left;
            }
            
            .financial-header {
                color: #2c3e50;
                margin: 35px 0 20px 0;
                border-bottom: 3px solid #27ae60;
                padding-bottom: 8px;
                font-size: 22px;
                font-weight: bold;
                text-align: left;
            }
            
            table {
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 26px;
            }
            
            th, td {
                border: 1px solid #ddd;
                padding: 10px 8px;
                text-align: center;
            }
            
            th {
                background-color: #f8f9fa;
                font-weight: bold;
                color: #2c3e50;
            }
            
            .info-container {
                background: #f8f9fa;
                border-left: 4px solid #3498db;
                padding: 18px 20px 18px 20px;
                margin: 15px 0;
                border-radius: 4px;
            }

            .info-line {
                display: flex;
                align-items: center;
                justify-content: flex-start;
                margin-bottom: 6px;
                font-size: 14px;
                min-height: 20px;
            }

            .info-line:last-child {
                margin-bottom: 0;
            }
            
            .info-label {
                font-weight: 600;
                margin-right: 12px;
                min-width: 180px;
                flex-shrink: 0;
                text-align: left;
            }
            
            .info-value {
                font-weight: bold;
                font-size: 14px;
                flex-grow: 0;
                text-align: left;
            }
            
            .performance-positive {
                color: #22c55e;
            }
            
            .performance-negative {
                color: #ef4444;
            }
            
            .performance-neutral {
                color: #6b7280;
            }
            
            .news-list {
                list-style: none;
                padding-left: 0;
                margin: 0;
            }
            
            .news-item {
                margin: 0 0 14px 0;
            }
            
            .news-headline {
                margin: 0 0 4px 0;
                font-weight: 600;
            }
            
            .news-summary {
                margin: 0;
            }
            
            a {
                color: #2563eb; text-decoration: none;
            }
            
            a:hover {
                text-decoration: underline;
            }
        </style>
        '''