from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from decouple import config

DB_HOST = config('DB_HOST', default='localhost')
DB_PORT = config('DB_PORT', default='5432')
DB_NAME = config('DB_NAME', default='market_brief_emails')
DB_USER = config('DB_USER', default='developer')
DB_PASSWORD = config('DB_PASSWORD', default='x!')
DB_POOL_SIZE = config('DB_POOL_SIZE', default=10, cast=int)
DB_MAX_OVERFLOW = config('DB_MAX_OVERFLOW', default=20, cast=int)

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    """User model for storing user account information and authentication details."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    oauth_provider = Column(String, nullable=True)
    oauth_provider_id = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
    tickers = Column(String, nullable=True)
    

def get_db():
    """Database dependency that provides a SQLAlchemy session with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()