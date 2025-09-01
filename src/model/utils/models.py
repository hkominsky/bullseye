from dataclasses import dataclass
from typing import Optional, Dict, List
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
    
    # Enhanced Financial Health Metrics
    interest_coverage_ratio: Optional[float] = None
    working_capital: Optional[float] = None
    days_sales_outstanding: Optional[float] = None
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None
    debt_to_ebitda: Optional[float] = None
    altman_z_score: Optional[float] = None
    piotroski_f_score: Optional[float] = None
    
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
        self._calculate_advanced_metrics()
    
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
        
        # Working Capital
        if self.current_assets and self.current_liabilities:
            self.working_capital = self.current_assets - self.current_liabilities
        
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
    
    def _calculate_advanced_metrics(self):
        """Calculate advanced financial health metrics"""
        
        # Asset Turnover
        if self.revenue and self.total_assets and self.total_assets > 0:
            self.asset_turnover = self.revenue / self.total_assets
        
        # Inventory Turnover
        if self.cost_of_revenue and self.inventory and self.inventory > 0:
            self.inventory_turnover = self.cost_of_revenue / self.inventory
        
        # Receivables Turnover & DSO
        if self.revenue and self.accounts_receivable and self.accounts_receivable > 0:
            self.receivables_turnover = self.revenue / self.accounts_receivable
            self.days_sales_outstanding = 365 / self.receivables_turnover
        
        # Debt to EBITDA (approximation using operating income)
        if self.operating_income and self.total_liabilities and self.operating_income > 0:
            self.debt_to_ebitda = self.total_liabilities / self.operating_income

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
    operating_income_growth_qoq: Optional[float] = None
    eps_growth_yoy: Optional[float] = None
    
    # Advanced growth metrics
    revenue_growth_acceleration: Optional[float] = None
    margin_expansion_rate: Optional[float] = None
    organic_growth_rate: Optional[float] = None
    
    # Trend indicators
    revenue_trend: Optional[str] = None  # "increasing", "decreasing", "stable"
    profitability_trend: Optional[str] = None
    efficiency_trend: Optional[str] = None