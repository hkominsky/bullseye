from contextlib import contextmanager
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from decouple import config

from src.model.utils.logger_config import LoggerSetup


class DatabaseManager:
    """
    Simplified database manager focused purely on connection management.
    All data operations moved to repository pattern classes.
    """
    
    def __init__(self):
        self.logger = LoggerSetup.setup_logger(__name__)
        self._pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool."""
        try:
            self._pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=config('DB_POOL_SIZE', default=10, cast=int),
                host=config('DB_HOST'),
                port=config('DB_PORT', default=5432, cast=int),
                database=config('DB_NAME'),
                user=config('DB_USER'),
                password=config('DB_PASSWORD'),
                cursor_factory=RealDictCursor
            )
            self.logger.info("Database connection pool initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections with automatic rollback on error.
        Ensures connection is returned to pool and transactions are properly handled.
        """
        conn = None
        try:
            conn = self._pool.getconn()
            conn.autocommit = False
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                self._pool.putconn(conn)
    
    def test_connection(self) -> bool:
        """Test if database connection is working."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT 1')
                    result = cur.fetchone()
                    return result is not None
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def close_pool(self):
        """Close the connection pool."""
        if self._pool:
            self._pool.closeall()
            self.logger.info("Database connection pool closed")
    
    def __del__(self):
        """Ensure pool is closed on deletion."""
        try:
            self.close_pool()
        except:
            pass