import logging
from typing import List, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv
from src.model.data_pipeline.data_manager import DataManager
from src.model.utils.logger_config import LoggerSetup
from src.model.utils.progress_tracker import ProgressTracker


class EmailController:
    """
    Controller for handling automated email operations from the web API.
    Processes stock data and sends emails to users.
    """
    
    def __init__(self):
        """Initialize the email controller with logging."""
        self.logger = LoggerSetup.setup_logger(__name__)
        load_dotenv()
    
    def send_stock_emails(
        self,
        tickers: List[str],
        user_email: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """
        Process stock data and send emails for specified tickers.
        """
        self.logger.info(f"Starting email processing for {len(tickers)} tickers")
        self.logger.info(f"Target email: {user_email}")
        
        manager = DataManager(user_agent)
        results = {
            "success": [],
            "failed": [],
            "total": len(tickers),
            "timestamp": datetime.utcnow().isoformat(),
            "user_email": user_email
        }
        
        for ticker in tickers:
            self.logger.info(f"Processing ticker: {ticker}")
            progress_tracker = ProgressTracker()
            progress_tracker.start(ticker)
            
            try:
                manager.process_ticker(ticker, progress_tracker)
                self.logger.info(f"Successfully completed processing for {ticker}")
                progress_tracker.complete(ticker)
                results["success"].append(ticker)
            except Exception as e:
                self.logger.error(f"Failed to process ticker {ticker}: {e}")
                results["failed"].append({
                    "ticker": ticker,
                    "error": str(e)
                })
        
        self.logger.info(
            f"Email processing completed. Success: {len(results['success'])}, "
            f"Failed: {len(results['failed'])}"
        )
        
        return results
    
    def send_watchlist_emails(
        self,
        watchlist_tickers: List[str],
        user_email: str
    ) -> Dict[str, Any]:
        """Send automated emails for all stocks in user's watchlist."""
        if not watchlist_tickers:
            return {
                "success": [],
                "failed": [],
                "total": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Watchlist is empty"
            }
        
        user_agent = os.getenv("USER_AGENT", "StockDashboard/1.0")
        return self.send_stock_emails(watchlist_tickers, user_email, user_agent)
    
    def send_custom_emails(
        self,
        tickers: List[str],
        user_email: str
    ) -> Dict[str, Any]:
        """Send automated emails for a custom list of tickers."""
        if not tickers:
            return {
                "success": [],
                "failed": [],
                "total": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "error": "No tickers provided"
            }
        
        user_agent = os.getenv("USER_AGENT", "StockDashboard/1.0")
        return self.send_stock_emails(tickers, user_email, user_agent)