import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


SECTOR_ETF_MAP = {
    "Technology": "XLK",
    "Financial Services": "XLF",
    "Healthcare": "XLV",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Basic Materials": "XLB",
    "Communication Services": "XLC",
}


class SectorPerformance:
    """
    Analyzes the 1-year performance of both a stock ticker and a corresponding sector ETF.
    """

    def __init__(self, ticker: str):
        """
        Initialize SectorPerformance with a stock ticker.
        """
        self.ticker = ticker
        self.sector = self._get_sector(ticker)
        self.sector_etf = self._get_sector_etf()

    def _get_sector(self, ticker: str) -> str:
        """Get sector for the given ticker."""
        stock = yf.Ticker(ticker)
        sector = stock.info.get("sector")
        if not sector:
            raise ValueError(f"Could not find sector for {ticker}")
        return sector

    def _get_sector_etf(self) -> str:
        """Get the ETF for the sector."""
        sector_etf = SECTOR_ETF_MAP.get(self.sector)
        if not sector_etf:
            raise ValueError(f"No ETF mapping found for sector: {self.sector}")
        return sector_etf

    def _get_price_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.Series:
        """Get adjusted close price data using yf.download()."""
        hist_data = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
        
        if 'Close' not in hist_data.columns:
            raise ValueError(f"No Close column found for {symbol}")
        
        return hist_data['Close']

    def _calculate_performance(self, hist: pd.Series, symbol: str) -> float:
        """Calculate 1-year performance percentage."""
        if hist.empty or len(hist) < 2:
            raise ValueError(f"Insufficient historical data for {symbol}")
        
        return (hist.iloc[-1] / hist.iloc[0] - 1) * 100

    def get_sector_performance(self) -> dict:
        """
        Calculate the 1-year performance of both the stock ticker and its sector ETF.
        """
        end_date = datetime.today()
        start_date = end_date - timedelta(days=365)
        
        ticker_hist = self._get_price_data(self.ticker, start_date, end_date)
        ticker_performance = self._calculate_performance(ticker_hist, self.ticker)
        
        etf_hist = self._get_price_data(self.sector_etf, start_date, end_date)
        etf_performance = self._calculate_performance(etf_hist, self.sector_etf)

        if isinstance(ticker_performance, pd.Series):
            ticker_performance = float(ticker_performance.iloc[0])
        if isinstance(etf_performance, pd.Series):
            etf_performance = float(etf_performance.iloc[0])

        return {
            "ticker": self.ticker,
            "sector": self.sector,
            "sector_etf": self.sector_etf,
            "ticker_1y_performance_pct": round(ticker_performance, 2),
            "sector_1y_performance_pct": round(etf_performance, 2),
        }