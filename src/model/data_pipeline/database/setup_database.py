import psycopg2
from psycopg2.extras import RealDictCursor
from decouple import config
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_connection():
    """Test database connection with detailed error reporting."""
    try:
        conn = psycopg2.connect(
            host=config('DB_HOST'),
            port=config('DB_PORT', default=5432, cast=int),
            database=config('DB_NAME'),
            user=config('DB_USER'),
            password=config('DB_PASSWORD')
        )
        with conn.cursor() as cur:
            cur.execute('SELECT version();')
            version = cur.fetchone()[0]
            logger.info(f"Database connection successful. PostgreSQL version: {version}")
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        logger.error(f"Connection failed - Operational Error: {e}")
        logger.error("Check if db server is running and credentials are right")
        return False
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return False

def _create_tables_schema():
    """Helper function that returns the SQL for creating all tables."""
    return """
    CREATE TABLE IF NOT EXISTS tickers (
        ticker VARCHAR(10) PRIMARY KEY,
        company_name VARCHAR(255),
        sector VARCHAR(100),
        sector_etf VARCHAR(10),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sentiment_data (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10) REFERENCES tickers(ticker) ON DELETE CASCADE,
        corporate_sentiment DECIMAL(10,6),
        retail_sentiment DECIMAL(10,6),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS news_articles (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10) REFERENCES tickers(ticker) ON DELETE CASCADE,
        headline TEXT NOT NULL,
        summary TEXT,
        url VARCHAR(2000), -- Increased from 1000 to handle longer URLs
        published_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sector_performance (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10) REFERENCES tickers(ticker) ON DELETE CASCADE,
        ticker_1y_performance_pct DECIMAL(10,4),
        sector_1y_performance_pct DECIMAL(10,4),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS earnings_historical (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10) REFERENCES tickers(ticker) ON DELETE CASCADE,
        fiscal_date_ending DATE,
        reported_eps DECIMAL(10,4),
        estimated_eps DECIMAL(10,4),
        surprise_percentage DECIMAL(10,4),
        one_day_return DECIMAL(10,6),
        five_day_return DECIMAL(10,6),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ticker, fiscal_date_ending)
    );

    CREATE TABLE IF NOT EXISTS earnings_estimates (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10) REFERENCES tickers(ticker) ON DELETE CASCADE,
        next_earnings_date DATE,
        estimated_eps DECIMAL(10,4),
        forward_pe DECIMAL(10,4),
        peg_ratio DECIMAL(10,4),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ticker, next_earnings_date)
    );

    CREATE TABLE IF NOT EXISTS financial_raw_data (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10) REFERENCES tickers(ticker) ON DELETE CASCADE,
        report_date DATE,
        period VARCHAR(20),
        form_type VARCHAR(10),
        revenue BIGINT,
        cost_of_revenue BIGINT,
        gross_profit BIGINT,
        operating_income BIGINT,
        net_income BIGINT,
        research_and_development BIGINT,
        selling_general_admin BIGINT,
        total_assets BIGINT,
        current_assets BIGINT,
        cash_and_equivalents BIGINT,
        accounts_receivable BIGINT,
        inventory BIGINT,
        property_plant_equipment BIGINT,
        total_liabilities BIGINT,
        current_liabilities BIGINT,
        long_term_debt BIGINT,
        shareholders_equity BIGINT,
        operating_cash_flow BIGINT,
        investing_cash_flow BIGINT,
        financing_cash_flow BIGINT,
        capital_expenditures BIGINT,
        shares_outstanding BIGINT,
        weighted_average_shares BIGINT,
        days_sales_outstanding DECIMAL(10,4),
        inventory_turnover DECIMAL(10,4),
        receivables_turnover DECIMAL(10,4),
        debt_to_ebitda DECIMAL(10,4),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ticker, report_date, period)
    );

    CREATE TABLE IF NOT EXISTS financial_metrics (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10) REFERENCES tickers(ticker) ON DELETE CASCADE,
        period VARCHAR(20),
        working_capital BIGINT,
        asset_turnover DECIMAL(10,6),
        altman_z_score DECIMAL(10,6),
        piotroski_f_score INTEGER,
        gross_margin DECIMAL(10,6),
        operating_margin DECIMAL(10,6),
        net_margin DECIMAL(10,6),
        current_ratio DECIMAL(10,6),
        quick_ratio DECIMAL(10,6),
        debt_to_equity DECIMAL(10,6),
        return_on_assets DECIMAL(10,6),
        return_on_equity DECIMAL(10,6),
        free_cash_flow BIGINT,
        earnings_per_share DECIMAL(10,4),
        stock_price DECIMAL(12,4),
        market_cap BIGINT,
        enterprise_value BIGINT,
        book_value_per_share DECIMAL(10,4),
        price_to_earnings DECIMAL(10,4),
        price_to_book DECIMAL(10,4),
        price_to_sales DECIMAL(10,4),
        ev_to_revenue DECIMAL(10,4),
        ev_to_ebitda DECIMAL(10,4),
        revenue_per_share DECIMAL(10,4),
        cash_per_share DECIMAL(10,4),
        fcf_per_share DECIMAL(10,4),
        price_to_fcf DECIMAL(10,4),
        market_to_book_premium DECIMAL(10,4),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ticker, period)
    );

    CREATE TABLE IF NOT EXISTS email_logs (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10) REFERENCES tickers(ticker) ON DELETE CASCADE,
        recipient VARCHAR(255) NOT NULL,
        email_status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
        processing_time_seconds INTEGER,
        error_message TEXT,
        data_snapshot_hash VARCHAR(64),
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

def _create_constraints_schema():
    """Helper function that returns the SQL for creating constraints."""
    return """
    CREATE UNIQUE INDEX IF NOT EXISTS sentiment_data_ticker_date_unique 
        ON sentiment_data (ticker, (created_at::date));

    CREATE UNIQUE INDEX IF NOT EXISTS sector_performance_ticker_date_unique 
        ON sector_performance (ticker, (created_at::date));

    DO $$ 
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'news_articles_ticker_url_key'
        ) THEN
            ALTER TABLE news_articles ADD CONSTRAINT news_articles_ticker_url_key 
            UNIQUE (ticker, url);
        END IF;
    END $$;
    """

def _create_indexes_schema():
    """Helper function that returns the SQL for creating performance indexes."""
    return """
    CREATE INDEX IF NOT EXISTS idx_sentiment_ticker_date 
        ON sentiment_data(ticker, created_at DESC);
        
    CREATE INDEX IF NOT EXISTS idx_news_ticker_published 
        ON news_articles(ticker, published_at DESC);
        
    CREATE INDEX IF NOT EXISTS idx_news_published_global
        ON news_articles(published_at DESC);
        
    CREATE INDEX IF NOT EXISTS idx_earnings_ticker_date 
        ON earnings_historical(ticker, fiscal_date_ending DESC);
        
    CREATE INDEX IF NOT EXISTS idx_financial_raw_ticker_date 
        ON financial_raw_data(ticker, report_date DESC);
        
    CREATE INDEX IF NOT EXISTS idx_financial_metrics_ticker_period
        ON financial_metrics(ticker, period);
        
    CREATE INDEX IF NOT EXISTS idx_email_logs_ticker_sent 
        ON email_logs(ticker, sent_at DESC);
        
    CREATE INDEX IF NOT EXISTS idx_email_logs_status
        ON email_logs(email_status, sent_at DESC);
    """

def _create_triggers_schema():
    """Helper function that returns the SQL for creating triggers."""
    return """
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ LANGUAGE 'plpgsql';

    DROP TRIGGER IF EXISTS update_tickers_updated_at ON tickers;
    CREATE TRIGGER update_tickers_updated_at 
        BEFORE UPDATE ON tickers 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

    DROP TRIGGER IF EXISTS update_earnings_estimates_updated_at ON earnings_estimates;
    CREATE TRIGGER update_earnings_estimates_updated_at 
        BEFORE UPDATE ON earnings_estimates 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """

def _execute_sql_section(conn, sql_section, section_name):
    """Helper to execute SQL sections with error handling."""
    try:
        with conn.cursor() as cur:
            cur.execute(sql_section)
        logger.info(f"{section_name} created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create {section_name}: {e}")
        return False

def create_schema():
    """Create the database schema using helper functions."""
    try:
        conn = psycopg2.connect(
            host=config('DB_HOST'),
            port=config('DB_PORT', default=5432, cast=int),
            database=config('DB_NAME'),
            user=config('DB_USER'),
            password=config('DB_PASSWORD')
        )
        
        sections = [
            (_create_tables_schema(), "Tables"),
            (_create_constraints_schema(), "Constraints"),
            (_create_indexes_schema(), "Indexes"),
            (_create_triggers_schema(), "Triggers")
        ]
        
        for sql, name in sections:
            if not _execute_sql_section(conn, sql, name):
                conn.close()
                return False
        
        conn.commit()
        conn.close()
        logger.info("Database schema created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create database schema: {e}")
        return False

def verify_setup():
    """Verify database setup and functionality."""
    try:
        conn = psycopg2.connect(
            host=config('DB_HOST'),
            port=config('DB_PORT', default=5432, cast=int),
            database=config('DB_NAME'),
            user=config('DB_USER'),
            password=config('DB_PASSWORD'),
            cursor_factory=RealDictCursor
        )
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            tables = [row['table_name'] for row in cur.fetchall()]
            expected_tables = [
                'tickers', 'sentiment_data', 'news_articles', 'sector_performance',
                'earnings_historical', 'earnings_estimates', 'financial_raw_data',
                'financial_metrics', 'email_logs'
            ]
            
            missing_tables = set(expected_tables) - set(tables)
            if missing_tables:
                logger.error(f"Missing tables: {missing_tables}")
                return False
            
            logger.info(f"All {len(expected_tables)} required tables created successfully")
            
            cur.execute("""
                SELECT COUNT(*) as index_count
                FROM pg_indexes 
                WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
            """)
            
            index_count = cur.fetchone()['index_count']
            logger.info(f"{index_count} performance indexes created")
        
        conn.close()
        logger.info("Database verification completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False

def main():
    logger.info("Starting database setup for Market Brief Emails...")
    
    # Test connection
    if not test_connection():
        logger.error("Database connection failed. Please check your configuration.")
        sys.exit(1)
    
    # Create schema
    if not create_schema():
        logger.error("Schema creation failed.")
        sys.exit(1)
    
    # Verify setup
    if not verify_setup():
        logger.error("Verification failed.")
        sys.exit(1)
    
    logger.info("Database setup completed successfully! Your database is ready.")

if __name__ == "__main__":
    main()