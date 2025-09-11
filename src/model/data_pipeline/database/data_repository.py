from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import hashlib
import json
import pandas as pd
from psycopg2.extras import execute_values

from src.model.data_pipeline.database.db_manager import DatabaseManager
from src.model.data_pipeline.database.data_validator import DataValidator
from src.model.utils.logger_config import LoggerSetup


class DataRepository:
    """Production-ready repository for consolidated financial data operations with transactions."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.validator = DataValidator()
        self.logger = LoggerSetup.setup_logger(__name__)
    
    def save_complete_ticker_data(self, ticker: str, data_package: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Save all ticker data in a single transaction for consistency.
        Returns (success, error_message)
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    self._save_ticker_info(cur, ticker, data_package)
                    self._save_sentiment_data(cur, ticker, data_package)
                    self._save_sector_performance(cur, ticker, data_package)
                    self._save_news_articles(cur, ticker, data_package)
                    self._save_earnings_data(cur, ticker, data_package)
                    self._save_earnings_estimates(cur, ticker, data_package)
                    self._save_raw_financial_data(cur, ticker, data_package)
                    self._save_financial_metrics(cur, ticker, data_package)
                    
                    conn.commit()
                    self.logger.info(f"Successfully saved complete ticker data package for {ticker}")
                    return True, ""
                    
        except Exception as e:
            error_msg = f"Failed to save complete ticker data for {ticker}: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _save_ticker_info(self, cur, ticker: str, data_package: Dict[str, Any]) -> None:
        """Save basic ticker information."""
        sector_data = data_package.get('sector_performance_data', {})
        company_name = sector_data.get('company_name', f"{ticker} Inc.")
        
        cur.execute("""
            INSERT INTO tickers (ticker, company_name, sector, sector_etf, updated_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ticker) DO UPDATE SET
                company_name = COALESCE(EXCLUDED.company_name, tickers.company_name),
                sector = COALESCE(EXCLUDED.sector, tickers.sector),
                sector_etf = COALESCE(EXCLUDED.sector_etf, tickers.sector_etf),
                updated_at = EXCLUDED.updated_at
        """, (
            ticker, 
            company_name,
            self.validator.safe_string(sector_data.get('sector'), 100),
            self.validator.safe_string(sector_data.get('sector_etf'), 10),
            datetime.now()
        ))
    
    def _save_sentiment_data(self, cur, ticker: str, data_package: Dict[str, Any]) -> None:
        """Save sentiment analysis data."""
        corporate_sentiment = self.validator.safe_decimal(data_package.get('corporate_sentiment', 0.0))
        retail_sentiment = self.validator.safe_decimal(data_package.get('retail_sentiment', 0.0))
        
        cur.execute("""
            INSERT INTO sentiment_data (ticker, corporate_sentiment, retail_sentiment)
            VALUES (%s, %s, %s)
            ON CONFLICT (ticker, (created_at::date)) DO UPDATE SET
                corporate_sentiment = EXCLUDED.corporate_sentiment,
                retail_sentiment = EXCLUDED.retail_sentiment
        """, (ticker, corporate_sentiment, retail_sentiment))
    
    def _save_sector_performance(self, cur, ticker: str, data_package: Dict[str, Any]) -> None:
        """Save sector performance data."""
        sector_data = data_package.get('sector_performance_data', {})
        
        cur.execute("""
            INSERT INTO sector_performance 
            (ticker, ticker_1y_performance_pct, sector_1y_performance_pct)
            VALUES (%s, %s, %s)
            ON CONFLICT (ticker, (created_at::date)) DO UPDATE SET
                ticker_1y_performance_pct = EXCLUDED.ticker_1y_performance_pct,
                sector_1y_performance_pct = EXCLUDED.sector_1y_performance_pct
        """, (
            ticker,
            self.validator.safe_decimal(sector_data.get('ticker_1y_performance_pct')),
            self.validator.safe_decimal(sector_data.get('sector_1y_performance_pct'))
        ))
    
    def _save_news_articles(self, cur, ticker: str, data_package: Dict[str, Any]) -> None:
        """Save news articles data."""
        news_df = data_package.get('ticker_news_df', pd.DataFrame())
        if news_df.empty:
            return
        
        news_data = self.validator.prepare_news_articles_data(ticker, news_df)
        if not news_data:
            return
        
        execute_values(
            cur,
            """
            INSERT INTO news_articles (ticker, headline, summary, url, published_at)
            VALUES %s
            ON CONFLICT (ticker, url) DO NOTHING
            """,
            news_data,
            page_size=1000
        )
        self.logger.info(f"Saved {len(news_data)} news articles for {ticker}")
    
    def _save_earnings_data(self, cur, ticker: str, data_package: Dict[str, Any]) -> None:
        """Save historical earnings data."""
        earnings_df = data_package.get('earnings_df', pd.DataFrame())
        if earnings_df.empty:
            return
        
        earnings_data = self.validator.prepare_earnings_data(ticker, earnings_df)
        if not earnings_data:
            return
        
        execute_values(
            cur,
            """
            INSERT INTO earnings_historical 
            (ticker, fiscal_date_ending, reported_eps, estimated_eps, 
             surprise_percentage, one_day_return, five_day_return)
            VALUES %s
            ON CONFLICT (ticker, fiscal_date_ending) DO UPDATE SET
                reported_eps = EXCLUDED.reported_eps,
                estimated_eps = EXCLUDED.estimated_eps,
                surprise_percentage = EXCLUDED.surprise_percentage,
                one_day_return = EXCLUDED.one_day_return,
                five_day_return = EXCLUDED.five_day_return
            """,
            earnings_data,
            page_size=1000
        )
        self.logger.info(f"Saved {len(earnings_data)} earnings records for {ticker}")
    
    def _save_earnings_estimates(self, cur, ticker: str, data_package: Dict[str, Any]) -> None:
        """Save earnings estimates data."""
        earnings_estimate = data_package.get('earnings_estimate', {})
        if not earnings_estimate or not isinstance(earnings_estimate, dict):
            return
        
        next_earnings_date = self.validator.safe_date(earnings_estimate.get('nextEarningsDate'))
        if not next_earnings_date:
            return
        
        cur.execute("""
            INSERT INTO earnings_estimates 
            (ticker, next_earnings_date, estimated_eps, forward_pe, peg_ratio)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ticker, next_earnings_date) DO UPDATE SET
                estimated_eps = EXCLUDED.estimated_eps,
                forward_pe = EXCLUDED.forward_pe,
                peg_ratio = EXCLUDED.peg_ratio,
                updated_at = CURRENT_TIMESTAMP
        """, (
            ticker,
            next_earnings_date,
            self.validator.safe_decimal(earnings_estimate.get('estimatedEPS')),
            self.validator.safe_decimal(earnings_estimate.get('forwardPE')),
            self.validator.safe_decimal(earnings_estimate.get('pegRatio'))
        ))
        self.logger.info(f"Saved earnings estimate for {ticker}")
    
    def _save_raw_financial_data(self, cur, ticker: str, data_package: Dict[str, Any]) -> None:
        """Save raw financial data."""
        raw_df = data_package.get('raw_df', pd.DataFrame())
        if raw_df.empty:
            return
        
        raw_data = self.validator.prepare_raw_financial_data(ticker, raw_df)
        if not raw_data:
            return
        
        execute_values(
            cur,
            """
            INSERT INTO financial_raw_data 
            (ticker, report_date, period, form_type, revenue, cost_of_revenue,
             gross_profit, operating_income, net_income, total_assets,
             current_assets, cash_and_equivalents, total_liabilities,
             current_liabilities, shareholders_equity)
            VALUES %s
            ON CONFLICT (ticker, report_date, period) DO UPDATE SET
                revenue = EXCLUDED.revenue,
                cost_of_revenue = EXCLUDED.cost_of_revenue,
                gross_profit = EXCLUDED.gross_profit,
                operating_income = EXCLUDED.operating_income,
                net_income = EXCLUDED.net_income,
                total_assets = EXCLUDED.total_assets,
                current_assets = EXCLUDED.current_assets,
                cash_and_equivalents = EXCLUDED.cash_and_equivalents,
                total_liabilities = EXCLUDED.total_liabilities,
                current_liabilities = EXCLUDED.current_liabilities,
                shareholders_equity = EXCLUDED.shareholders_equity
            """,
            raw_data,
            page_size=1000
        )
        self.logger.info(f"Saved {len(raw_data)} raw financial records for {ticker}")
    
    def _save_financial_metrics(self, cur, ticker: str, data_package: Dict[str, Any]) -> None:
        """Save financial metrics data."""
        metrics_df = data_package.get('metrics_df', pd.DataFrame())
        if metrics_df.empty:
            return
        
        metrics_data = self.validator.prepare_metrics_data(ticker, metrics_df)
        if not metrics_data:
            return
        
        execute_values(
            cur,
            """
            INSERT INTO financial_metrics 
            (ticker, period, working_capital, asset_turnover, altman_z_score,
            piotroski_f_score, gross_margin, operating_margin, net_margin,
            current_ratio, quick_ratio, debt_to_equity, return_on_assets,
            return_on_equity, free_cash_flow, earnings_per_share,
            book_value_per_share, revenue_per_share, cash_per_share,
            fcf_per_share, stock_price, market_cap, enterprise_value,
            price_to_earnings, price_to_book, price_to_sales,
            ev_to_revenue, ev_to_ebitda, price_to_fcf, market_to_book_premium)
            VALUES %s
            ON CONFLICT (ticker, period) DO UPDATE SET
                working_capital = EXCLUDED.working_capital,
                asset_turnover = EXCLUDED.asset_turnover,
                altman_z_score = EXCLUDED.altman_z_score,
                piotroski_f_score = EXCLUDED.piotroski_f_score,
                gross_margin = EXCLUDED.gross_margin,
                operating_margin = EXCLUDED.operating_margin,
                net_margin = EXCLUDED.net_margin,
                current_ratio = EXCLUDED.current_ratio,
                quick_ratio = EXCLUDED.quick_ratio,
                debt_to_equity = EXCLUDED.debt_to_equity,
                return_on_assets = EXCLUDED.return_on_assets,
                return_on_equity = EXCLUDED.return_on_equity,
                free_cash_flow = EXCLUDED.free_cash_flow,
                earnings_per_share = EXCLUDED.earnings_per_share,
                book_value_per_share = EXCLUDED.book_value_per_share,
                revenue_per_share = EXCLUDED.revenue_per_share,
                cash_per_share = EXCLUDED.cash_per_share,
                fcf_per_share = EXCLUDED.fcf_per_share,
                stock_price = EXCLUDED.stock_price,
                market_cap = EXCLUDED.market_cap,
                enterprise_value = EXCLUDED.enterprise_value,
                price_to_earnings = EXCLUDED.price_to_earnings,
                price_to_book = EXCLUDED.price_to_book,
                price_to_sales = EXCLUDED.price_to_sales,
                ev_to_revenue = EXCLUDED.ev_to_revenue,
                ev_to_ebitda = EXCLUDED.ev_to_ebitda,
                price_to_fcf = EXCLUDED.price_to_fcf,
                market_to_book_premium = EXCLUDED.market_to_book_premium
            """,
            metrics_data,
            page_size=1000
        )
        self.logger.info(f"Saved {len(metrics_data)} financial metrics for {ticker}")
        
    def log_processing_result(self, ticker: str, recipient: str, processing_time: int,
                            data_hash: str, status: str = "SUCCESS", 
                            error_message: Optional[str] = None) -> bool:
        """Log email processing results with proper error handling."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO email_logs 
                        (ticker, recipient, email_status, processing_time_seconds,
                         error_message, data_snapshot_hash)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        ticker, 
                        self.validator.safe_string(recipient, 255), 
                        self.validator.safe_string(status, 50), 
                        processing_time, 
                        self.validator.safe_string(error_message) if error_message else None, 
                        self.validator.safe_string(data_hash, 64)
                    ))
                    conn.commit()
                    self.logger.info(f"Successfully logged processing result for {ticker}: {status}")
                    return True
        except Exception as e:
            self.logger.error(f"Failed to log processing result for {ticker}: {e}")
            return False
    
    def get_latest_data_summary(self, ticker: str) -> Dict[str, Any]:
        """Get a comprehensive summary of the latest stored data for a ticker."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    result = self._fetch_ticker_summary(cur, ticker)
                    if result:
                        summary = dict(result)
                        summary['data_completeness'] = self._calculate_completeness(summary)
                        return summary
                    else:
                        return {'ticker': ticker, 'status': 'not_found'}
                        
        except Exception as e:
            self.logger.error(f"Failed to get data summary for {ticker}: {e}")
            return {'ticker': ticker, 'status': 'error', 'error': str(e)}
    
    def _fetch_ticker_summary(self, cur, ticker: str):
        """Execute the complex query to fetch ticker summary data."""
        cur.execute("""
            SELECT 
                t.ticker,
                t.company_name,
                t.sector,
                t.sector_etf,
                s.corporate_sentiment,
                s.retail_sentiment,
                s.created_at as sentiment_date,
                sp.ticker_1y_performance_pct,
                sp.sector_1y_performance_pct,
                sp.created_at as performance_date,
                COUNT(DISTINCT n.id) as news_count,
                COUNT(DISTINCT eh.id) as historical_earnings_count,
                COUNT(DISTINCT fr.period) as financial_periods,
                COUNT(DISTINCT fm.period) as metrics_periods,
                MAX(el.sent_at) as last_email_sent,
                COUNT(CASE WHEN el.email_status = 'SUCCESS' THEN 1 END) as successful_emails,
                COUNT(CASE WHEN el.email_status != 'SUCCESS' THEN 1 END) as failed_emails
            FROM tickers t
            LEFT JOIN sentiment_data s ON t.ticker = s.ticker 
                AND s.created_at >= CURRENT_DATE
            LEFT JOIN sector_performance sp ON t.ticker = sp.ticker 
                AND sp.created_at >= CURRENT_DATE
            LEFT JOIN news_articles n ON t.ticker = n.ticker 
                AND n.created_at >= CURRENT_DATE
            LEFT JOIN earnings_historical eh ON t.ticker = eh.ticker
            LEFT JOIN financial_raw_data fr ON t.ticker = fr.ticker
            LEFT JOIN financial_metrics fm ON t.ticker = fm.ticker
            LEFT JOIN email_logs el ON t.ticker = el.ticker
            WHERE t.ticker = %s
            GROUP BY t.ticker, t.company_name, t.sector, t.sector_etf, 
                     s.corporate_sentiment, s.retail_sentiment, s.created_at,
                     sp.ticker_1y_performance_pct, sp.sector_1y_performance_pct, sp.created_at
        """, (ticker,))
        
        return cur.fetchone()
    
    def _calculate_completeness(self, summary: Dict) -> Dict[str, bool]:
        """Calculate data completeness metrics."""
        return {
            'has_ticker_info': bool(summary.get('company_name')),
            'has_sentiment': summary.get('corporate_sentiment') is not None,
            'has_performance': summary.get('ticker_1y_performance_pct') is not None,
            'has_news': (summary.get('news_count') or 0) > 0,
            'has_earnings': (summary.get('historical_earnings_count') or 0) > 0,
            'has_financials': (summary.get('financial_periods') or 0) > 0,
            'has_metrics': (summary.get('metrics_periods') or 0) > 0,
            'recent_processing': summary.get('last_email_sent') is not None
        }
    
    @staticmethod
    def generate_data_hash(data_components: List[Any]) -> str:
        """Generate a stable hash of data components for integrity tracking."""
        try:
            stable_components = DataRepository._normalize_data_components(data_components)
            combined_data = json.dumps(stable_components, default=str, sort_keys=True)
            return hashlib.sha256(combined_data.encode('utf-8')).hexdigest()
            
        except Exception as e:
            fallback_data = str(data_components)
            return hashlib.sha256(fallback_data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def _normalize_data_components(data_components: List[Any]) -> List[Any]:
        """Normalize data components for consistent hashing."""
        stable_components = []
        for component in data_components:
            if isinstance(component, pd.DataFrame):
                if not component.empty:
                    sorted_df = component.reindex(sorted(component.columns), axis=1)
                    stable_components.append(sorted_df.to_dict('records'))
                else:
                    stable_components.append({})
            elif isinstance(component, dict):
                stable_components.append(dict(sorted(component.items())))
            else:
                stable_components.append(component)
        return stable_components