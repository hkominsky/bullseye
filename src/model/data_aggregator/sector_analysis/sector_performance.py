import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from src.model.utils.logger_config import LoggerSetup

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
        self.logger = LoggerSetup.setup_logger(__name__)
        self.ticker = ticker
        
        try:
            self.sector = self._get_sector(ticker)
            self.sector_etf = self._get_sector_etf()
            self.logger.info(f"SectorPerformance initialized for {ticker} - Sector: {self.sector}, ETF: {self.sector_etf}")
        except Exception as e:
            self.logger.error(f"Failed to initialize SectorPerformance for {ticker}: {e}")
            raise

    def _get_sector(self, ticker: str) -> str:
        """Get sector for the given ticker."""
        try:
            self.logger.debug(f"Fetching sector information for {ticker}")
            stock = yf.Ticker(ticker)
            sector = stock.info.get("sector")
            if not sector:
                self.logger.error(f"Could not find sector for {ticker}")
                raise ValueError(f"Could not find sector for {ticker}")
            self.logger.debug(f"Found sector for {ticker}: {sector}")
            return sector
        except Exception as e:
            self.logger.error(f"Error getting sector for {ticker}: {e}")
            raise

    def _get_sector_etf(self) -> str:
        """Get the ETF for the sector."""
        sector_etf = SECTOR_ETF_MAP.get(self.sector)
        if not sector_etf:
            self.logger.error(f"No ETF mapping found for sector: {self.sector}")
            raise ValueError(f"No ETF mapping found for sector: {self.sector}")
        self.logger.debug(f"Mapped sector {self.sector} to ETF {sector_etf}")
        return sector_etf

    def _get_price_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.Series:
        """Get adjusted close price data using yf.download()."""
        try:
            self.logger.debug(f"Downloading price data for {symbol} from {start_date.date()} to {end_date.date()}")
            hist_data = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
            
            if 'Close' not in hist_data.columns:
                self.logger.error(f"No Close column found for {symbol}")
                raise ValueError(f"No Close column found for {symbol}")
            
            self.logger.debug(f"Successfully downloaded {len(hist_data)} price points for {symbol}")
            return hist_data['Close']
        except Exception as e:
            self.logger.error(f"Error downloading price data for {symbol}: {e}")
            raise

    def _calculate_performance(self, hist: pd.Series, symbol: str) -> float:
        """Calculate 1-year performance percentage."""
        if hist.empty or len(hist) < 2:
            self.logger.error(f"Insufficient historical data for {symbol}: {len(hist)} data points")
            raise ValueError(f"Insufficient historical data for {symbol}")
        
        performance = (hist.iloc[-1] / hist.iloc[0] - 1) * 100
        self.logger.debug(f"Calculated 1-year performance for {symbol}: {performance:.2f}%")
        return performance

    def get_sector_performance(self) -> dict:
        """
        Calculate the 1-year performance of both the stock ticker and its sector ETF.
        """
        try:
            self.logger.info(f"Starting sector performance calculation for {self.ticker}")
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

            result = {
                "ticker": self.ticker,
                "sector": self.sector,
                "sector_etf": self.sector_etf,
                "ticker_1y_performance_pct": round(ticker_performance, 2),
                "sector_1y_performance_pct": round(etf_performance, 2),
            }
            
            self.logger.info(f"Sector performance calculation completed for {self.ticker} - Ticker: {result['ticker_1y_performance_pct']}%, Sector: {result['sector_1y_performance_pct']}%")
            return result
        except Exception as e:
            self.logger.error(f"Failed to calculate sector performance for {self.ticker}: {e}")
            raise