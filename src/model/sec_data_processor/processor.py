from model.utils.http_client import HttpClient
from cache import FileCache
from ticker_service import TickerMappingService
from sec_service import SECDataService
from models import Filing, FinancialRecord, CompanyProfile, GrowthMetrics, FinancialAlert
import pandas as pd
from typing import List, Dict, Optional, Tuple
from notifications import Notifier
from datetime import datetime, timedelta
import statistics


class SECDataProcessor:
    def __init__(self, user_agent: str, notifiers: List[Notifier] = None):
        self.http_client = HttpClient(user_agent)
        self.cache = FileCache()
        self.ticker_service = TickerMappingService(self.http_client, self.cache)
        ticker_mapping = self.ticker_service.get_ticker_to_cik_mapping()
        self.sec_service = SECDataService(self.http_client, ticker_mapping)
        self.notifiers = notifiers or []
        
        # Alert thresholds
        self.alert_thresholds = {
            'revenue_decline_threshold': -0.10,
            'margin_decline_threshold': -0.05,
            'liquidity_threshold': 1.0,
            'debt_threshold': 2.0,
            'negative_cash_flow_periods': 2
        }
    
    def get_filings(self, tickers: List[str]) -> Dict[str, List[Filing]]:
        """Get recent filings for multiple tickers"""
        filings_data = {}
        for ticker in tickers:
            try:
                filings = self.sec_service.get_recent_filings(ticker)
                filings_data[ticker] = filings
                self.notify(f"Retrieved {len(filings)} filings for {ticker}")
            except Exception as e:
                self.notify(f"Error retrieving filings for {ticker}: {str(e)}")
                filings_data[ticker] = []
        
        return filings_data
    
    def get_company_profiles(self, tickers: List[str]) -> Dict[str, Optional[CompanyProfile]]:
        """Get company profile information for multiple tickers"""
        profiles = {}
        for ticker in tickers:
            try:
                profile = self.sec_service.get_company_profile(ticker)
                profiles[ticker] = profile
            except Exception as e:
                self.notify(f"Error retrieving profile for {ticker}: {str(e)}")
                profiles[ticker] = None
        
        return profiles
    
    def get_comprehensive_financial_data(self, tickers: List[str], periods: int = 8) -> Dict[str, List[FinancialRecord]]:
        """Get comprehensive financial data for multiple tickers"""
        financial_data = {}
        
        for ticker in tickers:
            try:
                records = self.sec_service.get_comprehensive_financials(ticker, periods)
                financial_data[ticker] = records
                
                if records:
                    alerts = self._check_financial_alerts(ticker, records)
                    for alert in alerts:
                        self.notify(f"ALERT - {ticker}: {alert.message}")
                
            except Exception as e:
                self.notify(f"Error retrieving financial data for {ticker}: {str(e)}")
                financial_data[ticker] = []
        
        return financial_data
    
    def get_financial_dataframe(self, tickers: List[str]) -> pd.DataFrame:
        """Create comprehensive financial DataFrame with calculated metrics"""
        df_records = []
        financial_data = self.get_comprehensive_financial_data(tickers)
        
        for ticker, records in financial_data.items():
            for record in records:
                record_dict = {
                    'ticker': record.ticker,
                    'date': record.date,
                    'period': record.period,
                    'form_type': record.form_type,
                    'revenue': record.revenue,
                    'gross_profit': record.gross_profit,
                    'operating_income': record.operating_income,
                    'net_income': record.net_income,
                    'research_and_development': record.research_and_development,
                    'total_assets': record.total_assets,
                    'current_assets': record.current_assets,
                    'cash_and_equivalents': record.cash_and_equivalents,
                    'total_liabilities': record.total_liabilities,
                    'current_liabilities': record.current_liabilities,
                    'shareholders_equity': record.shareholders_equity,
                    'operating_cash_flow': record.operating_cash_flow,
                    'free_cash_flow': record.free_cash_flow,
                    'gross_margin': record.gross_margin,
                    'operating_margin': record.operating_margin,
                    'net_margin': record.net_margin,
                    'current_ratio': record.current_ratio,
                    'debt_to_equity': record.debt_to_equity,
                    'return_on_equity': record.return_on_equity,
                    'return_on_assets': record.return_on_assets,
                    'earnings_per_share': record.earnings_per_share
                }
                
                df_records.append(record_dict)
        
        return pd.DataFrame(df_records)
    
    def calculate_growth_metrics(self, tickers: List[str]) -> Dict[str, List[GrowthMetrics]]:
        """Calculate growth metrics for each ticker"""
        growth_data = {}
        financial_data = self.get_comprehensive_financial_data(tickers)
        
        for ticker, records in financial_data.items():
            growth_metrics = []
            
            sorted_records = sorted(records, key=lambda x: x.date)
            
            for i in range(1, len(sorted_records)):
                current = sorted_records[i]
                previous = sorted_records[i-1]
                
                growth_metric = GrowthMetrics(
                    ticker=ticker,
                    period=current.period
                )
                
                # Growth rate calculations
                if current.revenue and previous.revenue and previous.revenue != 0:
                    growth_metric.revenue_growth_qoq = ((current.revenue - previous.revenue) / previous.revenue) * 100
                
                if current.net_income and previous.net_income and previous.net_income != 0:
                    growth_metric.net_income_growth_qoq = ((current.net_income - previous.net_income) / previous.net_income) * 100
                
                if current.operating_income and previous.operating_income and previous.operating_income != 0:
                    growth_metric.operating_income_growth_qoq = ((current.operating_income - previous.operating_income) / previous.operating_income) * 100
                
                # Year-over-year comparison (look for record ~4 quarters ago)
                yoy_record = self._find_yoy_record(sorted_records, current, i)
                if yoy_record:
                    if current.revenue and yoy_record.revenue and yoy_record.revenue != 0:
                        growth_metric.revenue_growth_yoy = ((current.revenue - yoy_record.revenue) / yoy_record.revenue) * 100
                    
                    if current.net_income and yoy_record.net_income and yoy_record.net_income != 0:
                        growth_metric.net_income_growth_yoy = ((current.net_income - yoy_record.net_income) / yoy_record.net_income) * 100
                    
                    if current.earnings_per_share and yoy_record.earnings_per_share and yoy_record.earnings_per_share != 0:
                        growth_metric.eps_growth_yoy = ((current.earnings_per_share - yoy_record.earnings_per_share) / yoy_record.earnings_per_share) * 100
                
                # Determine trends
                growth_metric.revenue_trend = self._determine_trend([r.revenue for r in sorted_records[max(0, i-2):i+1] if r.revenue])
                growth_metric.profitability_trend = self._determine_trend([r.net_margin for r in sorted_records[max(0, i-2):i+1] if r.net_margin])
                
                growth_metrics.append(growth_metric)
            
            growth_data[ticker] = growth_metrics
        
        return growth_data
    
    def generate_financial_summary(self, ticker: str) -> Dict[str, any]:
        """Generate a comprehensive financial summary for a ticker"""
        try:
            profile = self.sec_service.get_company_profile(ticker)
            financial_records = self.sec_service.get_comprehensive_financials(ticker, 8)
            growth_data = self.calculate_growth_metrics([ticker])
            
            if not financial_records:
                return {'error': f'No financial data available for {ticker}'}
            
            latest_record = financial_records[0]
            
            summary = {
                'company_info': {
                    'ticker': ticker,
                    'name': profile.company_name if profile else 'Unknown',
                    'industry': profile.industry if profile else 'Unknown',
                    'latest_filing_date': latest_record.date
                },
                'latest_financials': {
                    'revenue': latest_record.revenue,
                    'net_income': latest_record.net_income,
                    'total_assets': latest_record.total_assets,
                    'shareholders_equity': latest_record.shareholders_equity,
                    'operating_cash_flow': latest_record.operating_cash_flow
                },
                'key_ratios': {
                    'gross_margin': latest_record.gross_margin,
                    'operating_margin': latest_record.operating_margin,
                    'net_margin': latest_record.net_margin,
                    'current_ratio': latest_record.current_ratio,
                    'debt_to_equity': latest_record.debt_to_equity,
                    'return_on_equity': latest_record.return_on_equity
                },
                'growth_metrics': growth_data.get(ticker, [])[:4],
                'alerts': self._check_financial_alerts(ticker, financial_records)
            }
            
            return summary
            
        except Exception as e:
            return {'error': f'Error