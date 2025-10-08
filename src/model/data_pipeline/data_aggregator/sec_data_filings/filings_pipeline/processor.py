import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from dataclasses import asdict, replace
from typing import Optional, Any
from src.model.utils.models import FinancialRecord, GrowthMetrics
from src.model.utils.logger_config import LoggerSetup


class SECDataProcessor:
    """
    Processor for SEC financial data that incorporates stock price data
    to calculate comprehensive valuation and market-based metrics.
    """
    
    def __init__(self):
        self.logger = LoggerSetup.setup_logger(__name__)
        self.stock_price_cache = {}
        self.logger.info("SECDataProcessor initialized with stock price cache")
    
    def get_stock_price_for_date(self, ticker: str, date: str, window_days: int = 5) -> Optional[float]:
        """
        Get stock price for a specific date with fallback window.
        """
        cache_key = f"{ticker}_{date}"
        if cache_key in self.stock_price_cache:
            self.logger.debug(f"Using cached stock price for {ticker} on {date}: {self.stock_price_cache[cache_key]}")
            return self.stock_price_cache[cache_key]
        
        try:
            self.logger.debug(f"Fetching stock price for {ticker} on {date} with {window_days} day window")
            target_date = datetime.strptime(date, "%Y-%m-%d")
            start_date = target_date - timedelta(days=window_days)
            end_date = target_date + timedelta(days=window_days)
            
            stock = yf.Ticker(ticker)
            history = stock.history(start=start_date, end=end_date)
            
            if history.empty:
                self.logger.warning(f"No price history found for {ticker} around {date}")
                return None
            
            if target_date.strftime('%Y-%m-%d') in history.index.strftime('%Y-%m-%d'):
                price = history.loc[history.index.strftime('%Y-%m-%d') == target_date.strftime('%Y-%m-%d'), 'Close'].iloc[0]
                self.logger.debug(f"Found exact price for {ticker} on {date}: {price}")
            else:
                price = history['Close'].iloc[-1]
                self.logger.debug(f"Using fallback price for {ticker} near {date}: {price}")
            
            self.stock_price_cache[cache_key] = float(price)
            return float(price)
            
        except Exception as e:
            self.logger.error(f"Error fetching stock price for {ticker} on {date}: {e}")
            return None
    
    def create_financial_dataframe(self, financial_data: dict[str, list[FinancialRecord]]) -> pd.DataFrame:
        """
        Convert financial records dictionary to a pandas DataFrame with enhanced metrics.
        """
        self.logger.info(f"Creating financial DataFrame for {len(financial_data)} tickers")
        df_records = []
        
        for ticker, records in financial_data.items():
            self.logger.debug(f"Processing {len(records)} records for ticker {ticker}")
            enhanced_records = self._enhance_records_with_all_metrics(records)
            
            for record in enhanced_records:
                record_dict = asdict(record)
                record_dict['ticker'] = ticker
                df_records.append(record_dict)
        
        result_df = pd.DataFrame(df_records)
        self.logger.info(f"Created DataFrame with {len(result_df)} total records")
        return result_df
    
    def create_split_dataframes(self, financial_data: dict[str, list[FinancialRecord]]) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Create two separate DataFrames: one with raw financial data and one with calculated metrics.
        """
        self.logger.info("Creating split DataFrames (raw and metrics)")
        full_df = self.create_financial_dataframe(financial_data)
        
        if full_df.empty:
            self.logger.warning("Full DataFrame is empty, returning empty DataFrames")
            return pd.DataFrame(), pd.DataFrame()
        
        calculated_fields = {
            'working_capital', 'free_cash_flow', 'gross_margin', 'operating_margin',
            'net_margin', 'current_ratio', 'quick_ratio', 'debt_to_equity',
            'return_on_assets', 'return_on_equity', 'earnings_per_share',
            'asset_turnover', 'altman_z_score', 'piotroski_f_score',
            'stock_price', 'market_cap', 'enterprise_value', 'book_value_per_share',
            'price_to_earnings', 'price_to_book', 'price_to_sales', 'ev_to_revenue',
            'ev_to_ebitda', 'revenue_per_share', 'cash_per_share', 'fcf_per_share',
            'price_to_fcf', 'market_to_book_premium'
        }
        
        all_columns = full_df.columns.tolist()
        raw_columns = [col for col in all_columns if col not in calculated_fields]
        metrics_columns = ['ticker', 'period'] + [col for col in all_columns if col in calculated_fields]
        
        raw_df = full_df[raw_columns].copy()
        metrics_df = full_df[metrics_columns].copy()
        
        self.logger.info(f"Split complete - Raw DataFrame: {len(raw_df)} rows, Metrics DataFrame: {len(metrics_df)} rows")
        return raw_df, metrics_df
    
    def calculate_growth_metrics(self, tickers: list[str], 
                               financial_data: dict[str, list[FinancialRecord]]) -> dict[str, list[GrowthMetrics]]:
        """
        Calculate comprehensive growth metrics for specified tickers.
        """
        self.logger.info(f"Calculating growth metrics for {len(tickers)} tickers")
        growth_data = {}
        
        for ticker in tickers:
            self.logger.debug(f"Processing growth metrics for {ticker}")
            records = financial_data.get(ticker, [])
            if len(records) < 2:
                self.logger.warning(f"Insufficient records ({len(records)}) for growth calculations for {ticker}")
                growth_data[ticker] = []
                continue
                
            sorted_records = sorted(records, key=lambda x: x.date)
            growth_metrics = []
            
            for i in range(1, len(sorted_records)):
                current = sorted_records[i]
                
                growth_metric = GrowthMetrics(ticker=ticker, period=current.period)
                
                self._calculate_qoq_growth(growth_metric, current, sorted_records[i-1])
                self._calculate_yoy_growth(growth_metric, current, sorted_records, i)
                self._calculate_revenue_acceleration(growth_metric, sorted_records, i)
                self._determine_trends(growth_metric, sorted_records, i)
                
                growth_metrics.append(growth_metric)
            
            growth_data[ticker] = growth_metrics
            self.logger.debug(f"Calculated {len(growth_metrics)} growth periods for {ticker}")
        
        self.logger.info("Growth metrics calculation completed")
        return growth_data
    
    def process_records_with_metrics(self, records: list[FinancialRecord]) -> list[FinancialRecord]:
        """
        Process financial records by calculating missing metrics and advanced scores.
        """
        self.logger.info(f"Processing {len(records)} financial records with metrics")
        enhanced_records = self._enhance_records_with_all_metrics(records)
        self.logger.info(f"Enhanced {len(enhanced_records)} financial records")
        return enhanced_records
    
    def generate_financial_summary(self, ticker: str, profile, 
                                 financial_records: list[FinancialRecord], 
                                 growth_data: list[GrowthMetrics]) -> dict[str, Any]:
        """
        Generate a comprehensive financial summary for a company.
        """
        self.logger.info(f"Generating financial summary for {ticker}")
        
        if not financial_records:
            self.logger.error(f"No financial data available for {ticker}")
            return {'error': f'No financial data available for {ticker}'}
        
        latest_record = max(financial_records, key=lambda x: x.date)
        self.logger.debug(f"Using latest record from {latest_record.date} for {ticker}")
        
        summary = {
            'company_info': {
                'ticker': ticker,
                'name': getattr(profile, 'company_name', 'Unknown'),
                'industry': getattr(profile, 'industry', 'Unknown'),
                'latest_filing_date': latest_record.date
            },
            'latest_financials': self._extract_latest_financials(latest_record),
            'key_ratios': self._extract_key_ratios(latest_record),
            'market_metrics': self._extract_market_metrics(latest_record),
            'growth_metrics': growth_data
        }
        
        self.logger.info(f"Financial summary generated for {ticker}")
        return summary
    
    def _enhance_records_with_all_metrics(self, records: list[FinancialRecord]) -> list[FinancialRecord]:
        """
        Enhance records with both fundamental and market-based metrics.
        """
        self.logger.debug(f"Enhancing {len(records)} records with all metrics")
        enhanced_records = []
        
        for i, record in enumerate(records):
            self.logger.debug(f"Enhancing record {i+1}/{len(records)} for {getattr(record, 'ticker', 'unknown')} on {record.date}")
            record_dict = asdict(record)
            
            self._calculate_all_financial_metrics(record_dict)
            
            stock_price = self.get_stock_price_for_date(record.ticker, record.date)
            if stock_price and record.shares_outstanding:
                self._add_market_metrics_to_dict(record_dict, record, stock_price)
            else:
                if not stock_price:
                    self.logger.debug(f"No stock price found for {record.ticker} on {record.date}")
                if not record.shares_outstanding:
                    self.logger.debug(f"No shares outstanding data for {record.ticker} on {record.date}")
            
            enhanced_record = self._create_record_from_dict(record_dict)
            final_record = replace(
                enhanced_record,
                altman_z_score=self._calculate_altman_z_score(enhanced_record),
                piotroski_f_score=self._calculate_piotroski_f_score(enhanced_record)
            )
            
            enhanced_records.append(final_record)
        
        self.logger.debug(f"Enhanced {len(enhanced_records)} records")
        return enhanced_records
    
    def _calculate_all_financial_metrics(self, data: dict) -> None:
        """
        Calculate ALL financial metrics including margins, ratios, and derived values.
        """
        self.logger.debug("Calculating all financial metrics")
        self._calculate_derived_values(data)
        self._calculate_margins(data)
        self._calculate_ratios(data)
        self._calculate_per_share_metrics_dict(data)
        self._calculate_advanced_metrics_dict(data)
    
    def _calculate_derived_values(self, data: dict) -> None:
        """Calculate derived financial values"""
        # Gross profit
        if self._both_not_none(data, 'revenue', 'cost_of_revenue'):
            data['gross_profit'] = data['revenue'] - data['cost_of_revenue']
            self.logger.debug(f"Calculated gross profit: {data['gross_profit']}")
        
        # Working capital
        if self._both_not_none(data, 'current_assets', 'current_liabilities'):
            data['working_capital'] = data['current_assets'] - data['current_liabilities']
            self.logger.debug(f"Calculated working capital: {data['working_capital']}")
        
        # Free cash flow
        if self._both_not_none(data, 'operating_cash_flow', 'capital_expenditures'):
            data['free_cash_flow'] = data['operating_cash_flow'] - data['capital_expenditures']
            self.logger.debug(f"Calculated free cash flow: {data['free_cash_flow']}")
    
    def _calculate_margins(self, data: dict) -> None:
        """Calculate profit margins as percentages"""
        revenue = data.get('revenue')
        if not revenue or revenue <= 0:
            self.logger.debug("Cannot calculate margins: invalid revenue")
            return
        
        margin_fields = [
            ('gross_profit', 'gross_margin'),
            ('operating_income', 'operating_margin'),
            ('net_income', 'net_margin')
        ]
        
        for profit_field, margin_field in margin_fields:
            profit = data.get(profit_field)
            if profit is not None:
                margin = (profit / revenue) * 100
                data[margin_field] = margin
                self.logger.debug(f"Calculated {margin_field}: {margin:.2f}%")
    
    def _calculate_ratios(self, data: dict) -> None:
        """Calculate financial ratios for liquidity, leverage, and profitability"""
        # Liquidity ratios
        if self._safe_divide(data, 'current_assets', 'current_liabilities'):
            data['current_ratio'] = data['current_assets'] / data['current_liabilities']
            # Quick ratio
            quick_assets = data['current_assets'] - data.get('inventory', 0)
            data['quick_ratio'] = quick_assets / data['current_liabilities']
            self.logger.debug(f"Calculated liquidity ratios - Current: {data['current_ratio']:.2f}, Quick: {data['quick_ratio']:.2f}")
        
        # Leverage ratios
        if self._safe_divide(data, 'total_liabilities', 'shareholders_equity'):
            data['debt_to_equity'] = data['total_liabilities'] / data['shareholders_equity']
            self.logger.debug(f"Calculated debt-to-equity: {data['debt_to_equity']:.2f}")
        
        # Profitability ratios
        net_income = data.get('net_income')
        if net_income is not None:
            if self._safe_divide(data, 'net_income', 'total_assets'):
                data['return_on_assets'] = (net_income / data['total_assets']) * 100
                self.logger.debug(f"Calculated ROA: {data['return_on_assets']:.2f}%")
            if self._safe_divide(data, 'net_income', 'shareholders_equity'):
                data['return_on_equity'] = (net_income / data['shareholders_equity']) * 100
                self.logger.debug(f"Calculated ROE: {data['return_on_equity']:.2f}%")
    
    def _calculate_per_share_metrics_dict(self, data: dict) -> None:
        """Calculate per-share metrics"""
        # EPS
        if self._safe_divide(data, 'net_income', 'weighted_average_shares'):
            data['earnings_per_share'] = data['net_income'] / data['weighted_average_shares']
            self.logger.debug(f"Calculated EPS: {data['earnings_per_share']:.2f}")
    
    def _calculate_advanced_metrics_dict(self, data: dict) -> None:
        """Calculate advanced financial health metrics"""
        # Asset Turnover
        if self._safe_divide(data, 'revenue', 'total_assets'):
            data['asset_turnover'] = data['revenue'] / data['total_assets']
            self.logger.debug(f"Calculated asset turnover: {data['asset_turnover']:.2f}")
        
        # Inventory Turnover
        if self._safe_divide(data, 'cost_of_revenue', 'inventory'):
            data['inventory_turnover'] = data['cost_of_revenue'] / data['inventory']
            self.logger.debug(f"Calculated inventory turnover: {data['inventory_turnover']:.2f}")
        
        # Receivables Turnover & DSO
        if self._safe_divide(data, 'revenue', 'accounts_receivable'):
            data['receivables_turnover'] = data['revenue'] / data['accounts_receivable']
            data['days_sales_outstanding'] = 365 / data['receivables_turnover']
            self.logger.debug(f"Calculated receivables turnover: {data['receivables_turnover']:.2f}, DSO: {data['days_sales_outstanding']:.1f}")
        
        # Debt to EBITDA (using operating income as proxy)
        if self._safe_divide(data, 'total_liabilities', 'operating_income'):
            data['debt_to_ebitda'] = data['total_liabilities'] / data['operating_income']
            self.logger.debug(f"Calculated debt-to-EBITDA: {data['debt_to_ebitda']:.2f}")
    
    def _add_market_metrics_to_dict(self, data: dict, original_record: FinancialRecord, stock_price: float) -> None:
        """Add market-based metrics to data dictionary"""
        self.logger.debug(f"Adding market metrics with stock price: {stock_price}")
        
        market_cap = stock_price * original_record.shares_outstanding if original_record.shares_outstanding else None
        enterprise_value = self._calculate_enterprise_value(market_cap, original_record.long_term_debt, original_record.cash_and_equivalents)
        book_value_per_share = (original_record.shareholders_equity / original_record.shares_outstanding 
                               if original_record.shareholders_equity and original_record.shares_outstanding else None)
        
        market_metrics = {
            'stock_price': stock_price,
            'market_cap': market_cap,
            'enterprise_value': enterprise_value,
            'book_value_per_share': book_value_per_share,
            'price_to_earnings': self._safe_divide_values(stock_price, data.get('earnings_per_share')),
            'price_to_book': self._safe_divide_values(stock_price, book_value_per_share),
            'price_to_sales': self._safe_divide_values(market_cap, original_record.revenue),
            'ev_to_revenue': self._safe_divide_values(enterprise_value, original_record.revenue),
            'ev_to_ebitda': self._calculate_ev_to_ebitda(enterprise_value, original_record.operating_income),
            'revenue_per_share': self._safe_divide_values(original_record.revenue, original_record.shares_outstanding),
            'cash_per_share': self._safe_divide_values(original_record.cash_and_equivalents, original_record.shares_outstanding),
            'fcf_per_share': self._safe_divide_values(data.get('free_cash_flow'), original_record.shares_outstanding),
            'price_to_fcf': self._safe_divide_values(market_cap, data.get('free_cash_flow')),
            'market_to_book_premium': self._calculate_market_to_book_premium(market_cap, original_record.shareholders_equity)
        }
        
        data.update(market_metrics)
        self.logger.debug(f"Added market metrics - Market cap: {market_cap}, P/E: {market_metrics['price_to_earnings']}")
    
    def _calculate_enterprise_value(self, market_cap: Optional[float], 
                                  long_term_debt: Optional[float], 
                                  cash: Optional[float]) -> Optional[float]:
        """Calculate Enterprise Value = Market Cap + Total Debt - Cash"""
        if market_cap is None:
            return None
        
        debt = long_term_debt or 0
        cash_amount = cash or 0
        
        enterprise_value = market_cap + debt - cash_amount
        self.logger.debug(f"Calculated enterprise value: {enterprise_value} (Market cap: {market_cap}, Debt: {debt}, Cash: {cash_amount})")
        return enterprise_value
    
    def _calculate_ev_to_ebitda(self, enterprise_value: Optional[float], 
                               operating_income: Optional[float]) -> Optional[float]:
        """Calculate EV/EBITDA ratio (using operating income as EBITDA proxy)"""
        if not enterprise_value or not operating_income or operating_income <= 0:
            return None
        ratio = enterprise_value / operating_income
        self.logger.debug(f"Calculated EV/EBITDA: {ratio:.2f}")
        return ratio
    
    def _calculate_market_to_book_premium(self, market_cap: Optional[float], 
                                        shareholders_equity: Optional[float]) -> Optional[float]:
        """Calculate market-to-book premium as percentage"""
        if not market_cap or not shareholders_equity or shareholders_equity <= 0:
            return None
        premium = ((market_cap - shareholders_equity) / shareholders_equity) * 100
        self.logger.debug(f"Calculated market-to-book premium: {premium:.2f}%")
        return premium
    
    def _calculate_qoq_growth(self, growth_metric: GrowthMetrics, 
                            current: FinancialRecord, previous: FinancialRecord) -> None:
        """Calculate quarter-over-quarter growth rates"""
        growth_calculations = [
            ('revenue', 'revenue_growth_qoq'),
            ('net_income', 'net_income_growth_qoq'),
            ('operating_income', 'operating_income_growth_qoq')
        ]
        
        for field, growth_field in growth_calculations:
            current_val = getattr(current, field)
            previous_val = getattr(previous, field)
            
            if current_val is not None and previous_val not in (None, 0):
                growth_rate = ((current_val - previous_val) / previous_val) * 100
                setattr(growth_metric, growth_field, growth_rate)
                self.logger.debug(f"Calculated {growth_field}: {growth_rate:.2f}%")
    
    def _calculate_yoy_growth(self, growth_metric: GrowthMetrics, current: FinancialRecord,
                            sorted_records: list[FinancialRecord], current_index: int) -> None:
        """Calculate year-over-year growth rates (4 quarters back)"""
        yoy_record = self._find_yoy_record(sorted_records, current_index)
        if not yoy_record:
            self.logger.debug("No YoY record found for growth calculations")
            return
        
        yoy_calculations = [
            ('revenue', 'revenue_growth_yoy'),
            ('net_income', 'net_income_growth_yoy'),
            ('earnings_per_share', 'eps_growth_yoy')
        ]
        
        for field, growth_field in yoy_calculations:
            current_val = getattr(current, field)
            yoy_val = getattr(yoy_record, field)
            
            if current_val is not None and yoy_val not in (None, 0):
                growth_rate = ((current_val - yoy_val) / yoy_val) * 100
                setattr(growth_metric, growth_field, growth_rate)
                self.logger.debug(f"Calculated {growth_field}: {growth_rate:.2f}%")
    
    def _calculate_revenue_acceleration(self, growth_metric: GrowthMetrics,
                                      sorted_records: list[FinancialRecord], current_index: int) -> None:
        """Calculate revenue growth acceleration (change in growth rate)"""
        if current_index < 2:
            self.logger.debug("Insufficient records for revenue acceleration calculation")
            return
        
        current = sorted_records[current_index]
        previous = sorted_records[current_index - 1]
        prev_period = sorted_records[current_index - 2]
        
        current_growth = self._calculate_period_growth(current.revenue, previous.revenue)
        prev_growth = self._calculate_period_growth(previous.revenue, prev_period.revenue)
        
        if current_growth is not None and prev_growth is not None:
            acceleration = current_growth - prev_growth
            growth_metric.revenue_growth_acceleration = acceleration
            self.logger.debug(f"Calculated revenue growth acceleration: {acceleration:.2f}%")
    
    def _determine_trends(self, growth_metric: GrowthMetrics, 
                         sorted_records: list[FinancialRecord], current_index: int) -> None:
        """Determine revenue and profitability trends over recent periods"""
        start_index = max(0, current_index - 2)
        recent_records = sorted_records[start_index:current_index + 1]
        
        revenue_values = [r.revenue for r in recent_records if r.revenue is not None]
        profitability_values = [r.net_margin for r in recent_records if r.net_margin is not None]
        
        growth_metric.revenue_trend = self._determine_trend_direction(revenue_values)
        growth_metric.profitability_trend = self._determine_trend_direction(profitability_values)
        
        self.logger.debug(f"Determined trends - Revenue: {growth_metric.revenue_trend}, Profitability: {growth_metric.profitability_trend}")
    
    def _calculate_altman_z_score(self, record: FinancialRecord) -> Optional[float]:
        """Calculate Altman Z-Score for bankruptcy prediction"""
        if not record.total_assets or record.total_assets <= 0:
            return None
        
        total_assets = record.total_assets
        
        wc_to_assets = self._safe_ratio(record.working_capital, total_assets)
        re_to_assets = self._safe_ratio(record.shareholders_equity, total_assets)
        ebit_to_assets = self._safe_ratio(record.operating_income, total_assets)
        equity_to_liabilities = self._safe_ratio(record.shareholders_equity, record.total_liabilities)
        sales_to_assets = self._safe_ratio(record.revenue, total_assets)
        
        z_score = (1.2 * wc_to_assets + 1.4 * re_to_assets + 3.3 * ebit_to_assets + 
                   0.6 * equity_to_liabilities + 1.0 * sales_to_assets)
        
        self.logger.debug(f"Calculated Altman Z-Score: {z_score:.2f}")
        return z_score
    
    def _calculate_piotroski_f_score(self, record: FinancialRecord) -> Optional[int]:
        """Calculate Piotroski F-Score (0-8 scale) for fundamental analysis"""
        score = 0
        
        if self._is_positive(record.net_income):
            score += 1
        if self._is_positive(record.operating_cash_flow):
            score += 1
        if self._is_positive(record.return_on_assets):
            score += 1
        if (record.operating_cash_flow and record.net_income and 
            record.operating_cash_flow > record.net_income):
            score += 1
        
        if self._is_above_threshold(record.current_ratio, 1.5):
            score += 1
        if self._is_below_threshold(record.debt_to_equity, 0.4):
            score += 1
        
        if self._is_above_threshold(record.asset_turnover, 0.5):
            score += 1
        if self._is_above_threshold(record.gross_margin, 20):
            score += 1
        
        self.logger.debug(f"Calculated Piotroski F-Score: {score}")
        return score
    
    def _create_record_from_dict(self, data: dict) -> FinancialRecord:
        """Create FinancialRecord from dictionary with enhanced data"""
        return FinancialRecord(**{k: v for k, v in data.items() if k in FinancialRecord.__annotations__})
    
    def _extract_latest_financials(self, record: FinancialRecord) -> dict:
        """Extract latest financial figures"""
        return {
            'revenue': record.revenue,
            'net_income': record.net_income,
            'total_assets': record.total_assets,
            'shareholders_equity': record.shareholders_equity,
            'operating_cash_flow': record.operating_cash_flow,
            'free_cash_flow': record.free_cash_flow
        }
    
    def _extract_key_ratios(self, record: FinancialRecord) -> dict:
        """Extract key financial ratios"""
        return {
            'gross_margin': record.gross_margin,
            'operating_margin': record.operating_margin,
            'net_margin': record.net_margin,
            'current_ratio': record.current_ratio,
            'debt_to_equity': record.debt_to_equity,
            'return_on_equity': record.return_on_equity,
            'altman_z_score': record.altman_z_score
        }
    
    def _extract_market_metrics(self, record: FinancialRecord) -> dict:
        """Extract market-based metrics"""
        return {
            'stock_price': getattr(record, 'stock_price', None),
            'market_cap': getattr(record, 'market_cap', None),
            'price_to_earnings': getattr(record, 'price_to_earnings', None),
            'price_to_book': getattr(record, 'price_to_book', None),
            'ev_to_revenue': getattr(record, 'ev_to_revenue', None),
            'price_to_fcf': getattr(record, 'price_to_fcf', None)
        }
    
    def _find_yoy_record(self, records: list[FinancialRecord], current_index: int) -> Optional[FinancialRecord]:
        """Find year-over-year comparison record (4 quarters back)"""
        yoy_index = current_index - 4
        return records[yoy_index] if yoy_index >= 0 else None
    
    def _determine_trend_direction(self, values: list[float]) -> str:
        """Determine trend direction from a series of values"""
        if len(values) < 2:
            return "stable"
        
        differences = [b - a for a, b in zip(values, values[1:])]
        
        if all(d > 0 for d in differences):
            return "increasing"
        elif all(d < 0 for d in differences):
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_period_growth(self, current: Optional[float], previous: Optional[float]) -> Optional[float]:
        """Calculate growth rate between two periods"""
        if current is None or previous in (None, 0):
            return None
        return ((current - previous) / previous) * 100
    
    def _both_not_none(self, data: dict, key1: str, key2: str) -> bool:
        """Check if both keys exist and are not None"""
        return data.get(key1) is not None and data.get(key2) is not None
    
    def _safe_divide(self, data: dict, numerator_key: str, denominator_key: str) -> bool:
        """Check if division is safe (both values exist and denominator > 0)"""
        return (data.get(numerator_key) is not None and 
                data.get(denominator_key) is not None and 
                data[denominator_key] > 0)
    
    def _safe_divide_values(self, numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
        """Safely divide two values, returning None if not possible"""
        if numerator is None or denominator is None or denominator == 0:
            return None
        return numerator / denominator
    
    def _safe_ratio(self, numerator: Optional[float], denominator: Optional[float]) -> float:
        """Calculate ratio safely, returning 0 if not possible"""
        if numerator is None or denominator is None or denominator == 0:
            return 0
        return numerator / denominator
    
    def _is_positive(self, value: Optional[float]) -> bool:
        """Check if value is positive"""
        return value is not None and value > 0
    
    def _is_above_threshold(self, value: Optional[float], threshold: float) -> bool:
        """Check if value is above threshold"""
        return value is not None and value > threshold
    
    def _is_below_threshold(self, value: Optional[float], threshold: float) -> bool:
        """Check if value is below threshold"""
        return value is not None and value < threshold