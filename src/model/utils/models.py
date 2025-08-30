from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime


@dataclass
class Filing:
    ticker: str
    form_type: str
    filing_date: str
    accession_number: str
    filing_url: str
    period_of_report: Optional[str] = None
    document_count: Optional[int] = None
    size_bytes: Optional[int] = None
    is_amended: Optional[bool] = None
    primary_document: Optional[str] = None


@dataclass
class FinancialRecord:
    ticker: str
    date: str
    period: str  # "Q1", "Q2", "Q3", "Q4", "FY"
    form_type: str  # "10-K", "10-Q"
    
    # Revenue & Profitability
    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    research_and_development: Optional[float] = None
    selling_general_admin: Optional[float] = None
    interest_expense: Optional[float] = None
    
    # Balance Sheet
    total_assets: Optional[float] = None
    current_assets: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    property_plant_equipment: Optional[float] = None
    total_liabilities: Optional[float] = None
    current_liabilities: Optional[float] = None
    long_term_debt: Optional[float] = None
    shareholders_equity: Optional[float] = None
    
    # Cash Flow
    operating_cash_flow: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None
    
    # Share Information
    shares_outstanding: Optional[float] = None
    weighted_average_shares: Optional[float] = None
    
    # Calculated Metrics (populated by processor)
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    free_cash_flow: Optional[float] = None
    earnings_per_share: Optional[float] = None
    
    def __post_init__(self):
        """Calculate basic ratios after initialization"""
        self._calculate_margins()
        self._calculate_ratios()
        self._calculate_per_share_metrics()
    
    def _calculate_margins(self):
        """Calculate profit margins"""
        if self.revenue and self.revenue != 0:
            if self.gross_profit:
                self.gross_margin = (self.gross_profit / self.revenue) * 100
            if self.operating_income:
                self.operating_margin = (self.operating_income / self.revenue) * 100
            if self.net_income:
                self.net_margin = (self.net_income / self.revenue) * 100
    
    def _calculate_ratios(self):
        """Calculate financial ratios"""
        # Liquidity ratios
        if self.current_assets and self.current_liabilities and self.current_liabilities != 0:
            self.current_ratio = self.current_assets / self.current_liabilities
            
            # Quick ratio (current assets - inventory) / current liabilities
            quick_assets = self.current_assets
            if self.inventory:
                quick_assets -= self.inventory
            self.quick_ratio = quick_assets / self.current_liabilities
        
        # Leverage ratios
        if self.total_liabilities and self.shareholders_equity and self.shareholders_equity != 0:
            self.debt_to_equity = self.total_liabilities / self.shareholders_equity
        
        # Profitability ratios
        if self.net_income:
            if self.total_assets and self.total_assets != 0:
                self.return_on_assets = (self.net_income / self.total_assets) * 100
            if self.shareholders_equity and self.shareholders_equity != 0:
                self.return_on_equity = (self.net_income / self.shareholders_equity) * 100
        
        # Free cash flow
        if self.operating_cash_flow and self.capital_expenditures:
            self.free_cash_flow = self.operating_cash_flow - self.capital_expenditures
    
    def _calculate_per_share_metrics(self):
        """Calculate per-share metrics"""
        if self.net_income and self.weighted_average_shares and self.weighted_average_shares != 0:
            self.earnings_per_share = self.net_income / self.weighted_average_shares


@dataclass
class CompanyProfile:
    ticker: str
    cik: str
    company_name: str
    sic_code: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    latest_filing_date: Optional[str] = None
    exchange: Optional[str] = None
    business_address: Optional[Dict[str, str]] = None


@dataclass
class GrowthMetrics:
    ticker: str
    period: str
    
    # Growth rates (as percentages)
    revenue_growth_yoy: Optional[float] = None
    revenue_growth_qoq: Optional[float] = None
    net_income_growth_yoy: Optional[float] = None
    net_income_growth_qoq: Optional[float] = None
    operating_income_growth_yoy: Optional[float] = None
    eps_growth_yoy: Optional[float] = None
    
    # Trend indicators
    revenue_trend: Optional[str] = None  # "increasing", "decreasing", "stable"
    profitability_trend: Optional[str] = None


@dataclass
class FinancialAlert:
    ticker: str
    alert_type: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    date_triggered: Optional[str] = None
    
    def __post_init__(self):
        if not self.date_triggered:
            self.date_triggered = datetime.now().isoformat()


@dataclass
class IndustryBenchmark:
    industry_code: str
    metric_name: str
    median_value: float
    percentile_25: float
    percentile_75: float
    sample_size: int
    period: str  # "Q1 2024", "FY 2023", etc.