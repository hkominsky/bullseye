import yfinance as yf
import pandas as pd

class StockPriceGetter:
    """
        Class to fetch stock prices for a specified stock and period to add to greater filing data frame from EDGAR API.
    """
    
    def get_stock_prices(self, ticker: str, period: str = "6mo") -> pd.DataFrame:
        """
        Fetch historical stock prices for a specified ticker and period.

        Args:
            ticker (str): Stock symbol (e.g., "AAPL").
            period (str): Time period for historical data (e.g., "1mo", "3mo", "6mo", "1y", "2y", "5y", "max").

        Returns:
            pd.DataFrame: Historical stock data including Open, High, Low, Close, Volume, and Dividends.
        """
        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period=period)
            if history.empty:
                print(f"No data found for {ticker} for period {period}")
            return history
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()
