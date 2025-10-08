from dataclasses import dataclass
from typing import Optional


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
    period: str
    form_type: str
    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    research_and_development: Optional[float] = None
    selling_general_admin: Optional[float] = None
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
    operating_cash_flow: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None
    shares_outstanding: Optional[float] = None
    weighted_average_shares: Optional[float] = None
    working_capital: Optional[float] = None
    days_sales_outstanding: Optional[float] = None
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None
    debt_to_ebitda: Optional[float] = None
    altman_z_score: Optional[float] = None
    piotroski_f_score: Optional[float] = None
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
    stock_price: Optional[float] = None
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    book_value_per_share: Optional[float] = None
    price_to_earnings: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    ev_to_revenue: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    revenue_per_share: Optional[float] = None
    cash_per_share: Optional[float] = None
    fcf_per_share: Optional[float] = None
    price_to_fcf: Optional[float] = None
    market_to_book_premium: Optional[float] = None

@dataclass
class GrowthMetrics:
    ticker: str
    period: str
    revenue_growth_yoy: Optional[float] = None
    revenue_growth_qoq: Optional[float] = None
    net_income_growth_yoy: Optional[float] = None
    net_income_growth_qoq: Optional[float] = None
    operating_income_growth_yoy: Optional[float] = None
    operating_income_growth_qoq: Optional[float] = None
    eps_growth_yoy: Optional[float] = None
    revenue_growth_acceleration: Optional[float] = None
    margin_expansion_rate: Optional[float] = None
    organic_growth_rate: Optional[float] = None
    revenue_trend: Optional[str] = None
    profitability_trend: Optional[str] = None
    efficiency_trend: Optional[str] = None