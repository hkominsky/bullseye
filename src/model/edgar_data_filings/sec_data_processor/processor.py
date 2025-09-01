import pandas as pd
from dataclasses import asdict, replace
from typing import Optional, Any
from src.model.utils.models import FinancialRecord, GrowthMetrics


class SECDataProcessor:
    """
    A comprehensive processor for SEC financial data that calculates metrics, 
    growth rates, and generates financial summaries.
    
    This class handles financial data transformation, metric calculations,
    and trend analysis for publicly traded companies using SEC filing data.
    """
    
    def create_financial_dataframe(self, financial_data: dict[str, list[FinancialRecord]]) -> pd.DataFrame:
        """
        Convert financial records dictionary to a pandas DataFrame.
        
        Args:
            financial_data (dict[str, list[FinancialRecord]]): Dictionary mapping ticker symbols to lists of FinancialRecord objects.
            
        Returns:
            pd.DataFrame: DataFrame with all financial records including ticker column.
            
        Example:
            >>> processor = SECDataProcessor()
            >>> data = {'AAPL': [record1, record2], 'MSFT': [record3]}
            >>> df = processor.create_financial_dataframe(data)
        """
        df_records = []
        
        for ticker, records in financial_data.items():
            for record in records:
                record_dict = asdict(record)
                record_dict['ticker'] = ticker
                df_records.append(record_dict)
        
        return pd.DataFrame(df_records)
    
    def create_split_dataframes(self, financial_data: dict[str, list[FinancialRecord]]) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Create two separate DataFrames: one with raw financial data and one with calculated metrics.
        
        Args:
            financial_data (dict[str, list[FinancialRecord]]): Dictionary mapping ticker symbols to lists of FinancialRecord objects.
            
        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (raw_data_df, calculated_metrics_df)
        """
        # Use existing method to create the full DataFrame with proper column order
        full_df = self.create_financial_dataframe(financial_data)
        
        if full_df.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        # Define which fields are calculated metrics (everything else is considered raw)
        calculated_fields = {
            'working_capital', 'free_cash_flow', 'gross_margin', 'operating_margin',
            'net_margin', 'current_ratio', 'quick_ratio', 'debt_to_equity',
            'return_on_assets', 'return_on_equity', 'earnings_per_share',
            'asset_turnover', 'altman_z_score', 'piotroski_f_score'
        }
        
        # Split columns dynamically
        all_columns = full_df.columns.tolist()
        
        # Raw columns: all columns except calculated ones
        raw_columns = [col for col in all_columns if col not in calculated_fields]
        
        # Metrics columns: ticker, period (for identification) + calculated fields
        metrics_columns = ['ticker', 'period'] + [col for col in all_columns if col in calculated_fields]
        
        # Create split DataFrames preserving original column order
        raw_df = full_df[raw_columns].copy()
        metrics_df = full_df[metrics_columns].copy()
        
        return raw_df, metrics_df
    
    def calculate_growth_metrics(self, tickers: list[str], 
                               financial_data: dict[str, list[FinancialRecord]]) -> dict[str, list[GrowthMetrics]]:
        """
        Calculate comprehensive growth metrics for specified tickers.
        
        Computes quarter-over-quarter, year-over-year growth rates, 
        revenue acceleration, and trend analysis.
        
        Args:
            tickers (list[str]): List of ticker symbols to process.
            financial_data (dict[str, list[FinancialRecord]]): Dictionary mapping tickers to financial records.
            
        Returns:
            dict[str, list[GrowthMetrics]]: Dictionary mapping tickers to lists of GrowthMetrics objects.
            
        Note:
            Requires at least 2 quarters of data for QoQ growth,
            5 quarters for YoY growth calculations.
        """
        growth_data = {}
        
        for ticker in tickers:
            records = financial_data.get(ticker, [])
            if len(records) < 2:
                growth_data[ticker] = []
                continue
                
            # Sort chronologically for proper growth calculations
            sorted_records = sorted(records, key=lambda x: x.date)
            growth_metrics = []
            
            for i in range(1, len(sorted_records)):
                current = sorted_records[i]
                
                growth_metric = GrowthMetrics(ticker=ticker, period=current.period)
                
                # Calculate all growth metrics
                self._calculate_qoq_growth(growth_metric, current, sorted_records[i-1])
                self._calculate_yoy_growth(growth_metric, current, sorted_records, i)
                self._calculate_revenue_acceleration(growth_metric, sorted_records, i)
                self._determine_trends(growth_metric, sorted_records, i)
                
                growth_metrics.append(growth_metric)
            
            growth_data[ticker] = growth_metrics
        
        return growth_data
    
    def process_records_with_metrics(self, records: list[FinancialRecord]) -> list[FinancialRecord]:
        """
        Process financial records by calculating missing metrics and advanced scores.
        
        Calculates basic financial ratios, margins, and advanced scoring metrics
        like Altman Z-Score and Piotroski F-Score for each record.
        
        Args:
            records (list[FinancialRecord]): List of FinancialRecord objects to process.
            
        Returns:
            list[FinancialRecord]: List of enhanced FinancialRecord objects with calculated metrics.
            
        Note:
            Uses dataclass replace() for immutable updates to maintain data integrity.
        """
        processed_records = []
        
        for record in records:
            # Calculate basic metrics
            enhanced_data = self._calculate_basic_metrics(asdict(record))
            
            # Create updated record with basic metrics
            updated_record = self._create_updated_record(record, enhanced_data)
            
            # Add advanced scoring metrics
            final_record = replace(
                updated_record,
                altman_z_score=self._calculate_altman_z_score(updated_record),
                piotroski_f_score=self._calculate_piotroski_f_score(updated_record)
            )
            
            processed_records.append(final_record)
        
        return processed_records
    
    def generate_financial_summary(self, ticker: str, profile, 
                                 financial_records: list[FinancialRecord], 
                                 growth_data: list[GrowthMetrics]) -> dict[str, Any]:
        """
        Generate a comprehensive financial summary for a company.
        
        Creates a structured summary including company info, latest financials,
        key ratios, and growth metrics.
        
        Args:
            ticker (str): Stock ticker symbol.
            profile: Company profile object with basic company information.
            financial_records (list[FinancialRecord]): List of financial records for the company.
            growth_data (list[GrowthMetrics]): List of growth metrics for the company.
            
        Returns:
            dict[str, Any]: Dictionary containing structured financial summary with sections:
                - company_info: Basic company details
                - latest_financials: Most recent financial figures
                - key_ratios: Important financial ratios
                - growth_metrics: Growth and trend data
            
        Note:
            Returns error dict if no financial data is available.
        """
        if not financial_records:
            return {'error': f'No financial data available for {ticker}'}
        
        # Get most recent data
        latest_record = max(financial_records, key=lambda x: x.date)
        
        return {
            'company_info': {
                'ticker': ticker,
                'name': getattr(profile, 'company_name', 'Unknown'),
                'industry': getattr(profile, 'industry', 'Unknown'),
                'latest_filing_date': latest_record.date
            },
            'latest_financials': self._extract_latest_financials(latest_record),
            'key_ratios': self._extract_key_ratios(latest_record),
            'growth_metrics': growth_data
        }
    
    def _calculate_basic_metrics(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate basic financial metrics from raw financial data.
        
        Computes margins, ratios, and derived values like free cash flow,
        working capital, and various profitability metrics.
        
        Args:
            data (dict[str, Any]): Dictionary containing raw financial data.
            
        Returns:
            dict[str, Any]: Dictionary with calculated metrics added.
        """
        # Derived calculations
        self._calculate_derived_values(data)
        
        # Margin calculations
        self._calculate_margins(data)
        
        # Ratio calculations
        self._calculate_ratios(data)
        
        return data
    
    def _calculate_derived_values(self, data: dict[str, Any]) -> None:
        """
        Calculate derived financial values like gross profit and free cash flow.
        
        Args:
            data (dict[str, Any]): Dictionary containing raw financial data to be enhanced with derived values.
        """
        # Gross profit
        if self._both_not_none(data, 'revenue', 'cost_of_revenue'):
            data['gross_profit'] = data['revenue'] - data['cost_of_revenue']
        
        # Working capital
        if self._both_not_none(data, 'current_assets', 'current_liabilities'):
            data['working_capital'] = data['current_assets'] - data['current_liabilities']
        
        # Free cash flow
        if self._both_not_none(data, 'operating_cash_flow', 'capital_expenditures'):
            data['free_cash_flow'] = data['operating_cash_flow'] - data['capital_expenditures']
    
    def _calculate_margins(self, data: dict[str, Any]) -> None:
        """
        Calculate profit margins as percentages.
        
        Args:
            data (dict[str, Any]): Dictionary containing financial data where margin calculations will be added.
        """
        revenue = data.get('revenue')
        if not revenue or revenue <= 0:
            return
        
        margin_fields = [
            ('gross_profit', 'gross_margin'),
            ('operating_income', 'operating_margin'),
            ('net_income', 'net_margin')
        ]
        
        for profit_field, margin_field in margin_fields:
            profit = data.get(profit_field)
            if profit is not None:
                data[margin_field] = (profit / revenue) * 100
                
    def _calculate_ratios(self, data: dict[str, Any]) -> None:
        """
        Calculate financial ratios for liquidity, leverage, and profitability analysis.

        Args:
            data (dict[str, Any]): Financial data dictionary where calculated ratios will be added.
        """
        if self._safe_divide(data, 'current_assets', 'current_liabilities'):
            data['current_ratio'] = data['current_assets'] / data['current_liabilities']
            quick_assets = data['current_assets'] - data.get('inventory', 0)
            data['quick_ratio'] = quick_assets / data['current_liabilities']
        if self._safe_divide(data, 'total_liabilities', 'shareholders_equity'):
            data['debt_to_equity'] = data['total_liabilities'] / data['shareholders_equity']
        net_income = data.get('net_income')
        if net_income is not None:
            if self._safe_divide(data, 'net_income', 'total_assets'):
                data['return_on_assets'] = (net_income / data['total_assets']) * 100
            if self._safe_divide(data, 'net_income', 'shareholders_equity'):
                data['return_on_equity'] = (net_income / data['shareholders_equity']) * 100
        if self._safe_divide(data, 'net_income', 'weighted_average_shares'):
            data['earnings_per_share'] = data['net_income'] / data['weighted_average_shares']
        if self._safe_divide(data, 'revenue', 'total_assets'):
            data['asset_turnover'] = data['revenue'] / data['total_assets']
    
    def _calculate_qoq_growth(self, growth_metric: GrowthMetrics, 
                            current: FinancialRecord, previous: FinancialRecord) -> None:
        """
        Calculate quarter-over-quarter growth rates.
        
        Args:
            growth_metric (GrowthMetrics): GrowthMetrics object to update with QoQ growth rates.
            current (FinancialRecord): Current period's financial record.
            previous (FinancialRecord): Previous period's financial record.
        """
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
    
    def _calculate_yoy_growth(self, growth_metric: GrowthMetrics, current: FinancialRecord,
                            sorted_records: list[FinancialRecord], current_index: int) -> None:
        """
        Calculate year-over-year growth rates (4 quarters back).
        
        Args:
            growth_metric (GrowthMetrics): GrowthMetrics object to update with YoY growth rates.
            current (FinancialRecord): Current period's financial record.
            sorted_records (list[FinancialRecord]): Chronologically sorted financial records.
            current_index (int): Index of the current record in sorted_records.
        """
        yoy_record = self._find_yoy_record(sorted_records, current_index)
        if not yoy_record:
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
    
    def _calculate_revenue_acceleration(self, growth_metric: GrowthMetrics,
                                      sorted_records: list[FinancialRecord], current_index: int) -> None:
        """
        Calculate revenue growth acceleration (change in growth rate).
        
        Args:
            growth_metric (GrowthMetrics): GrowthMetrics object to update.
            sorted_records (list[FinancialRecord]): Chronologically sorted financial records.
            current_index (int): Index of the current record in sorted_records.
        """
        if current_index < 2:
            return
        
        current = sorted_records[current_index]
        previous = sorted_records[current_index - 1]
        prev_period = sorted_records[current_index - 2]
        
        # Calculate current and previous period growth rates
        current_growth = self._calculate_period_growth(current.revenue, previous.revenue)
        prev_growth = self._calculate_period_growth(previous.revenue, prev_period.revenue)
        
        if current_growth is not None and prev_growth is not None:
            growth_metric.revenue_growth_acceleration = current_growth - prev_growth
    
    def _determine_trends(self, growth_metric: GrowthMetrics, 
                         sorted_records: list[FinancialRecord], current_index: int) -> None:
        """
        Determine revenue and profitability trends over recent periods.
        
        Args:
            growth_metric (GrowthMetrics): GrowthMetrics object to update with trend information.
            sorted_records (list[FinancialRecord]): Chronologically sorted financial records.
            current_index (int): Index of the current record in sorted_records.
        """
        # Get last 3 periods of data (including current)
        start_index = max(0, current_index - 2)
        recent_records = sorted_records[start_index:current_index + 1]
        
        # Extract values for trend analysis
        revenue_values = [r.revenue for r in recent_records if r.revenue is not None]
        profitability_values = [r.net_margin for r in recent_records if r.net_margin is not None]
        
        growth_metric.revenue_trend = self._determine_trend_direction(revenue_values)
        growth_metric.profitability_trend = self._determine_trend_direction(profitability_values)
    
    def _calculate_altman_z_score(self, record: FinancialRecord) -> Optional[float]:
        """
        Calculate Altman Z-Score for bankruptcy prediction.
        
        Z-Score components:
        - 1.2 × (Working Capital / Total Assets)
        - 1.4 × (Retained Earnings / Total Assets) 
        - 3.3 × (EBIT / Total Assets)
        - 0.6 × (Market Value Equity / Total Liabilities)
        - 1.0 × (Sales / Total Assets)
        
        Args:
            record (FinancialRecord): Financial record containing the data for Z-Score calculation.
            
        Returns:
            Optional[float]: Altman Z-Score value, or None if insufficient data.
                - > 3.0: Safe zone
                - 1.8-3.0: Gray zone
                - < 1.8: Distress zone
        """
        if not record.total_assets or record.total_assets <= 0:
            return None
        
        total_assets = record.total_assets
        
        # Calculate components safely
        wc_to_assets = self._safe_ratio(record.working_capital, total_assets)
        re_to_assets = self._safe_ratio(record.shareholders_equity, total_assets)  # Proxy for retained earnings
        ebit_to_assets = self._safe_ratio(record.operating_income, total_assets)
        equity_to_liabilities = self._safe_ratio(record.shareholders_equity, record.total_liabilities)
        sales_to_assets = self._safe_ratio(record.revenue, total_assets)
        
        return (1.2 * wc_to_assets + 1.4 * re_to_assets + 3.3 * ebit_to_assets + 
                0.6 * equity_to_liabilities + 1.0 * sales_to_assets)
    
    def _calculate_piotroski_f_score(self, record: FinancialRecord) -> Optional[int]:
        """
        Calculate Piotroski F-Score (0-8 scale) for fundamental analysis.
        
        Scoring criteria:
        - Profitability: positive net income, positive operating cash flow, 
          positive ROA, operating cash flow > net income
        - Leverage/Liquidity: improving current ratio, decreasing debt ratio
        - Operating Efficiency: improving asset turnover, improving gross margin
        
        Args:
            record (FinancialRecord): Financial record containing data for F-Score calculation.
            
        Returns:
            Optional[int]: Piotroski F-Score (0-8), where:
                - 8-9: Excellent fundamentals
                - 6-7: Good fundamentals  
                - 4-5: Average fundamentals
                - 0-3: Poor fundamentals
        """
        score = 0
        
        # Profitability criteria (4 points possible)
        if self._is_positive(record.net_income):
            score += 1
        if self._is_positive(record.operating_cash_flow):
            score += 1
        if self._is_positive(record.return_on_assets):
            score += 1
        if (record.operating_cash_flow and record.net_income and 
            record.operating_cash_flow > record.net_income):
            score += 1
        
        # Leverage and liquidity criteria (2 points possible)
        if self._is_above_threshold(record.current_ratio, 1.5):
            score += 1
        if self._is_below_threshold(record.debt_to_equity, 0.4):
            score += 1
        
        # Operating efficiency criteria (2 points possible)
        if self._is_above_threshold(record.asset_turnover, 0.5):
            score += 1
        if self._is_above_threshold(record.gross_margin, 20):  # Assuming percentage format
            score += 1
        
        return score
    
    # Helper methods for cleaner code
    def _create_updated_record(self, original: FinancialRecord, enhanced_data: dict) -> FinancialRecord:
        """
        Create updated FinancialRecord with enhanced data.
        
        Args:
            original (FinancialRecord): Original financial record.
            enhanced_data (dict): Dictionary containing enhanced financial data.
            
        Returns:
            FinancialRecord: Updated financial record with enhanced metrics.
        """
        if hasattr(FinancialRecord, 'from_dict'):
            return FinancialRecord.from_dict(enhanced_data)
        return FinancialRecord(**enhanced_data)
    
    def _extract_latest_financials(self, record: FinancialRecord) -> dict:
        """
        Extract latest financial figures.
        
        Args:
            record (FinancialRecord): Financial record to extract data from.
            
        Returns:
            dict: Dictionary containing key financial figures.
        """
        return {
            'revenue': record.revenue,
            'net_income': record.net_income,
            'total_assets': record.total_assets,
            'shareholders_equity': record.shareholders_equity,
            'operating_cash_flow': record.operating_cash_flow,
            'free_cash_flow': record.free_cash_flow
        }
    
    def _extract_key_ratios(self, record: FinancialRecord) -> dict:
        """
        Extract key financial ratios.
        
        Args:
            record (FinancialRecord): Financial record to extract ratios from.
            
        Returns:
            dict: Dictionary containing important financial ratios.
        """
        return {
            'gross_margin': record.gross_margin,
            'operating_margin': record.operating_margin,
            'net_margin': record.net_margin,
            'current_ratio': record.current_ratio,
            'debt_to_equity': record.debt_to_equity,
            'return_on_equity': record.return_on_equity,
            'altman_z_score': record.altman_z_score
        }
    
    def _find_yoy_record(self, records: list[FinancialRecord], current_index: int) -> Optional[FinancialRecord]:
        """
        Find year-over-year comparison record (4 quarters back).
        
        Args:
            records (list[FinancialRecord]): List of chronologically sorted financial records.
            current_index (int): Index of the current record.
            
        Returns:
            Optional[FinancialRecord]: Record from 4 quarters ago, or None if not available.
        """
        yoy_index = current_index - 4
        return records[yoy_index] if yoy_index >= 0 else None
    
    def _determine_trend_direction(self, values: list[float]) -> str:
        """
        Determine trend direction from a series of values.
        
        Args:
            values (list[float]): List of values to analyze for trend direction.
            
        Returns:
            str: Trend direction - "increasing", "decreasing", or "stable".
        """
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
        """
        Calculate growth rate between two periods.
        
        Args:
            current (Optional[float]): Current period value.
            previous (Optional[float]): Previous period value.
            
        Returns:
            Optional[float]: Growth rate as percentage, or None if calculation not possible.
        """
        if current is None or previous in (None, 0):
            return None
        return ((current - previous) / previous) * 100
    
    # Utility methods for safe calculations
    def _both_not_none(self, data: dict, key1: str, key2: str) -> bool:
        """
        Check if both keys exist and are not None.
        
        Args:
            data (dict): Dictionary to check.
            key1 (str): First key to check.
            key2 (str): Second key to check.
            
        Returns:
            bool: True if both keys exist and are not None.
        """
        return data.get(key1) is not None and data.get(key2) is not None
    
    def _safe_divide(self, data: dict, numerator_key: str, denominator_key: str) -> bool:
        """
        Check if division is safe (both values exist and denominator > 0).
        
        Args:
            data (dict): Dictionary containing the values.
            numerator_key (str): Key for the numerator value.
            denominator_key (str): Key for the denominator value.
            
        Returns:
            bool: True if division is safe to perform.
        """
        return (data.get(numerator_key) is not None and 
                data.get(denominator_key) is not None and 
                data[denominator_key] > 0)
    
    def _safe_ratio(self, numerator: Optional[float], denominator: Optional[float]) -> float:
        """
        Calculate ratio safely, returning 0 if not possible.
        
        Args:
            numerator (Optional[float]): Numerator value.
            denominator (Optional[float]): Denominator value.
            
        Returns:
            float: Calculated ratio, or 0 if calculation not possible.
        """
        if numerator is None or denominator is None or denominator == 0:
            return 0
        return numerator / denominator
    
    def _is_positive(self, value: Optional[float]) -> bool:
        """
        Check if value is positive.
        
        Args:
            value (Optional[float]): Value to check.
            
        Returns:
            bool: True if value is positive.
        """
        return value is not None and value > 0
    
    def _is_above_threshold(self, value: Optional[float], threshold: float) -> bool:
        """
        Check if value is above threshold.
        
        Args:
            value (Optional[float]): Value to check.
            threshold (float): Threshold to compare against.
            
        Returns:
            bool: True if value is above threshold.
        """
        return value is not None and value > threshold
    
    def _is_below_threshold(self, value: Optional[float], threshold: float) -> bool:
        """
        Check if value is below threshold.
        
        Args:
            value (Optional[float]): Value to check.
            threshold (float): Threshold to compare against.
            
        Returns:
            bool: True if value is below threshold.
        """
        return value is not None and value < threshold