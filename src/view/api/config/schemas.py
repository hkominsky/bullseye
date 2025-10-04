from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    confirm_password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    created_at: datetime
    updated_at: datetime
    oauth_provider: Optional[str] = None
    oauth_provider_id: Optional[str] = None
    tickers: Optional[str] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    
class OAuthUserInfo(BaseModel):
    email: str
    first_name: str
    last_name: str
    provider: str
    provider_id: str
    
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetResponse(BaseModel):
    message: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
class StockSuggestion(BaseModel):
    symbol: str
    name: str

class StockValidationResponse(BaseModel):
    valid: bool
    symbol: str
    name: Optional[str] = None
    error: Optional[str] = None

class StockSearchResponse(BaseModel):
    suggestions: list[StockSuggestion]
    
class CustomEmailRequest(BaseModel):
    tickers: list[str]

class EmailJobResponse(BaseModel):
    message: str
    ticker_count: int
    tickers: list[str]
    status: str