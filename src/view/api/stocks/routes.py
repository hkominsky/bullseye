import yfinance as yf
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from config.database import get_db, User
from auth.security import get_current_user
from config.schemas import StockSuggestion, StockValidationResponse, StockSearchResponse
import pandas as pd

router = APIRouter(prefix="/api/stocks", tags=["stocks"])

def get_ticker_info(symbol: str) -> Optional[dict]:
    """Fetch ticker info safely."""
    try:
        ticker_obj = yf.Ticker(symbol.upper())
        info = ticker_obj.get_info()
        return info if info and 'symbol' in info else None
    except:
        return None

def has_valid_price(info: dict) -> bool:
    """Check if ticker has valid price data."""
    return (
        info.get('regularMarketPrice') is not None or 
        info.get('currentPrice') is not None or
        info.get('previousClose') is not None
    )

def has_sufficient_data(info: dict) -> tuple[bool, Optional[str]]:
    """
    Check if stock has sufficient data to be useful.
    Returns (is_valid, error_message)
    """
    if not has_valid_price(info):
        return False, "⚠︎ Ticker exists but has no valid price data."
    
    if info.get('marketCap') is None:
        return False, "⚠︎ Ticker has insufficient fundamental data."
    
    return True, None

def create_stock_suggestion(symbol: str, info: dict) -> StockSuggestion:
    """Create a StockSuggestion from ticker info."""
    return StockSuggestion(
        symbol=symbol,
        name=info.get('longName', info.get('shortName', symbol)),
        exchange=info.get('exchange', 'Unknown')
    )

def get_popular_stocks() -> List[str]:
    """Return list of popular stock tickers."""
    return [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
        'AMD', 'INTC', 'CRM', 'ORCL', 'ADBE', 'NOW', 'UBER', 'LYFT',
        'SPOT', 'SQ', 'PYPL', 'V', 'MA', 'JPM', 'BAC', 'WFC', 'GS',
        'SPY', 'QQQ', 'IWM', 'VTI', 'VOO'
    ]

def matches_search_query(stock: str, query: str) -> bool:
    """Check if stock matches search query."""
    return stock.startswith(query) or query in stock

@router.get("/search")
async def search_stocks(
    q: str, 
    limit: int = 10,
    current_user: User = Depends(get_current_user)
) -> StockSearchResponse:
    """Search for stock tickers using yfinance."""
    if len(q) < 1:
        return StockSearchResponse(suggestions=[])
    
    try:
        suggestions = []
        ticker_upper = q.upper()
        
        info = get_ticker_info(ticker_upper)
        if info and has_valid_price(info):
            suggestions.append(create_stock_suggestion(ticker_upper, info))
        
        for stock in get_popular_stocks():
            if len(suggestions) >= limit:
                break
            
            if matches_search_query(stock, ticker_upper):
                if not any(s.symbol == stock for s in suggestions):
                    info = get_ticker_info(stock)
                    if info:
                        suggestions.append(create_stock_suggestion(stock, info))
        
        return StockSearchResponse(suggestions=suggestions[:limit])
        
    except Exception as e:
        print(f"Stock search error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Search service temporarily unavailable"
        )

@router.get("/validate/{symbol}")
async def validate_stock(
    symbol: str,
    current_user: User = Depends(get_current_user)
) -> StockValidationResponse:
    """Validate if a stock ticker exists and is tradeable."""
    try:
        ticker_upper = symbol.upper()
        info = get_ticker_info(ticker_upper)
        
        if not info:
            return StockValidationResponse(
                valid=False, 
                symbol=ticker_upper,
                error="Stock ticker not found"
            )
        
        if not has_valid_price(info):
            return StockValidationResponse(
                valid=False, 
                symbol=ticker_upper,
                error="Stock exists but has no valid price data (may be delisted)"
            )
        
        is_valid, error_msg = has_sufficient_data(info)
        if not is_valid:
            return StockValidationResponse(
                valid=False,
                symbol=ticker_upper,
                error=error_msg
            )
        
        return StockValidationResponse(
            valid=True, 
            symbol=ticker_upper,
            name=info.get('longName', info.get('shortName'))
        )
            
    except Exception as e:
        print(f"Stock validation error for {symbol}: {e}")
        return StockValidationResponse(
            valid=False, 
            symbol=symbol.upper(),
            error="Unable to validate ticker at this time"
        )

def get_current_price(info: dict) -> Optional[float]:
    """Extract current price from info."""
    return info.get('regularMarketPrice', info.get('currentPrice'))

def get_previous_close(info: dict) -> Optional[float]:
    """Extract previous close from info."""
    return info.get('regularMarketPreviousClose', info.get('previousClose'))

def calculate_price_changes(current_price: float, previous_close: float) -> tuple[Optional[float], Optional[float]]:
    """Calculate price change and percent change."""
    if not current_price or not previous_close:
        return None, None
    
    price_change = current_price - previous_close
    percent_change = (price_change / previous_close) * 100
    return round(price_change, 2), round(percent_change, 2)

def format_chart_data(hist: pd.DataFrame) -> List[dict]:
    """Format historical data for chart."""
    return [
        {
            "timestamp": index.isoformat(),
            "price": float(row['Close'])
        }
        for index, row in hist.iterrows()
    ]

def _parse_calendar_for_date(calendar) -> Optional[pd.Timestamp]:
    """Extract earnings date from Yahoo Finance calendar DataFrame or dict."""
    if calendar is not None:
        if isinstance(calendar, dict) and "Earnings Date" in calendar:
            earnings_dates = calendar["Earnings Date"]
            
            if isinstance(earnings_dates, list) and len(earnings_dates) > 0:
                for date in earnings_dates:
                    ts = pd.Timestamp(date)
                    if ts > pd.Timestamp.now():
                        return ts
        
        elif hasattr(calendar, 'index') and "Earnings Date" in calendar.index:
            raw_date = calendar.loc["Earnings Date"].values[0]
            parsed_date = pd.to_datetime(raw_date).tz_localize(None)
            return parsed_date
    
    return None

def _fallback_from_earnings_dates(stock: yf.Ticker) -> Optional[pd.Timestamp]:
    """Fallback: use get_earnings_dates() to find the next earnings date."""
    try:
        earnings_dates = stock.get_earnings_dates(limit=8)
        
        if earnings_dates is not None and not earnings_dates.empty:
            if earnings_dates.index.tz is not None:
                idx = earnings_dates.index.tz_localize(None)
            else:
                idx = earnings_dates.index
            
            future = earnings_dates.loc[idx > pd.Timestamp.now()]
            
            if not future.empty:
                return future.index.min()
            
    except Exception as e:
        print(f"Error fetching earnings dates: {e}")
    
    return None

def get_next_earnings_date(ticker_obj: yf.Ticker, symbol: str) -> Dict[str, Optional[str]]:
    """
    Fetch the next earnings date for a stock.
    Uses Yahoo Finance calendar first, then falls back to get_earnings_dates().
    """
    try:
        earnings_date = _parse_calendar_for_date(ticker_obj.calendar)
        if earnings_date:
            return {"nextEarningsDate": earnings_date.isoformat()}

        earnings_date = _fallback_from_earnings_dates(ticker_obj)
        if earnings_date:
            return {"nextEarningsDate": earnings_date.isoformat()}

    except Exception as e:
        print(f"Error fetching next earnings for {symbol}: {e}")

    return {"nextEarningsDate": None}

@router.get("/info/{symbol}")
async def get_stock_info(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Get stock symbol, current price, daily changes, chart data, and earnings info."""
    try:
        ticker_obj = yf.Ticker(symbol.upper())
        info = ticker_obj.get_info()
        
        is_valid, error_msg = has_sufficient_data(info)
        if not is_valid:
            raise HTTPException(status_code=404, detail=error_msg)
        
        hist = ticker_obj.history(period="1d", interval="5m")
        if hist.empty:
            raise HTTPException(
                status_code=404, 
                detail="Stock exists but has no valid price data (may be delisted)"
            )
        
        current_price = get_current_price(info)
        previous_close = get_previous_close(info)
        
        if not current_price:
            raise HTTPException(
                status_code=404, 
                detail="Stock exists but has no valid price data (may be delisted)"
            )
        
        price_change, percent_change = calculate_price_changes(current_price, previous_close)
        
        price_history = format_chart_data(hist)
        earnings_result = get_next_earnings_date(ticker_obj, symbol)
        next_earnings_date = earnings_result.get("nextEarningsDate")
        
        volume = info.get('volume')
        avg_volume_10d = info.get('averageVolume10days')
        
        return {
            "symbol": symbol.upper(),
            "name": info.get('longName', info.get('shortName', symbol.upper())),
            "price": current_price,
            "priceChange": price_change,
            "percentChange": percent_change,
            "priceHistory": price_history,
            "marketCap": info.get('marketCap'),
            "volume": volume,
            "avgVolume": avg_volume_10d,
            "relativeVolume": (volume / avg_volume_10d) * 100 if avg_volume_10d else None,
            "nextEarningsDate": next_earnings_date,
            "peRatio": info.get('trailingPE'),
            "trailingEPS": info.get('trailingEps'),
            "forwardEPS": info.get('forwardEps'),
            "recommendation": info.get('recommendationKey', '').replace("_", " ").title() if info.get('recommendationKey') else None,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching stock info for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stock information")

@router.get("/user/watchlist")
async def get_user_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's saved watchlist tickers."""
    try:
        db.refresh(current_user)
        tickers = current_user.get_watchlist_tickers()
        return {"tickers": tickers}
    except Exception as e:
        print(f"Error fetching watchlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch watchlist")

@router.post("/user/watchlist/{symbol}")
async def add_to_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a ticker to user's watchlist."""
    try:
        db.refresh(current_user)
        tickers = current_user.get_watchlist_tickers()
        symbol_upper = symbol.upper()
        
        if symbol_upper not in tickers:
            tickers.append(symbol_upper)
            current_user.set_watchlist_tickers(tickers)
            db.add(current_user)
            db.commit()
            db.refresh(current_user)
        
        return {"tickers": tickers}
    except Exception as e:
        print(f"Error adding to watchlist: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add stock to watchlist")

@router.delete("/user/watchlist/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a ticker from user's watchlist."""
    try:
        db.refresh(current_user)
        tickers = current_user.get_watchlist_tickers()
        symbol_upper = symbol.upper()
        
        if symbol_upper in tickers:
            tickers.remove(symbol_upper)
            current_user.set_watchlist_tickers(tickers)
            db.add(current_user)
            db.commit()
            db.refresh(current_user)
        
        return {"tickers": tickers}
    except Exception as e:
        print(f"Error removing from watchlist: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to remove stock from watchlist")

@router.get("/user/reserve")
async def get_user_reserve(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's saved reserve tickers."""
    try:
        db.refresh(current_user)
        tickers = current_user.get_reserve_tickers()
        return {"tickers": tickers}
    except Exception as e:
        print(f"Error fetching reserve: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch reserve list")

@router.post("/user/reserve/{symbol}")
async def add_to_reserve(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a ticker to user's reserve list."""
    try:
        db.refresh(current_user)
        tickers = current_user.get_reserve_tickers()
        symbol_upper = symbol.upper()
        
        if symbol_upper not in tickers:
            tickers.append(symbol_upper)
            current_user.set_reserve_tickers(tickers)
            db.add(current_user)
            db.commit()
            db.refresh(current_user)
        
        return {"tickers": tickers}
    except Exception as e:
        print(f"Error adding to reserve: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add stock to reserve list")

@router.delete("/user/reserve/{symbol}")
async def remove_from_reserve(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a ticker from user's reserve list."""
    try:
        db.refresh(current_user)
        tickers = current_user.get_reserve_tickers()
        symbol_upper = symbol.upper()
        
        if symbol_upper in tickers:
            tickers.remove(symbol_upper)
            current_user.set_reserve_tickers(tickers)
            db.add(current_user)
            db.commit()
            db.refresh(current_user)
        
        return {"tickers": tickers}
    except Exception as e:
        print(f"Error removing from reserve: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to remove stock from reserve list")

@router.post("/user/watchlist/{symbol}/move-to-reserve")
async def move_watchlist_to_reserve(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Move a ticker from watchlist to reserve."""
    try:
        db.refresh(current_user)
        symbol_upper = symbol.upper()
        
        watchlist = current_user.get_watchlist_tickers()
        reserve = current_user.get_reserve_tickers()
        
        if symbol_upper in watchlist and symbol_upper not in reserve:
            watchlist.remove(symbol_upper)
            reserve.append(symbol_upper)
            current_user.set_watchlist_tickers(watchlist)
            current_user.set_reserve_tickers(reserve)
            db.add(current_user)
            db.commit()
            db.refresh(current_user)
        
        return {"watchlist": watchlist, "reserve": reserve}
    except Exception as e:
        print(f"Error moving stock to reserve: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to move stock to reserve list")

@router.post("/user/reserve/{symbol}/move-to-watchlist")
async def move_reserve_to_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Move a ticker from reserve to watchlist."""
    try:
        db.refresh(current_user)
        symbol_upper = symbol.upper()
        
        watchlist = current_user.get_watchlist_tickers()
        reserve = current_user.get_reserve_tickers()
        
        if symbol_upper in reserve and symbol_upper not in watchlist:
            reserve.remove(symbol_upper)
            watchlist.append(symbol_upper)
            current_user.set_watchlist_tickers(watchlist)
            current_user.set_reserve_tickers(reserve)
            db.add(current_user)
            db.commit()
            db.refresh(current_user)
        
        return {"watchlist": watchlist, "reserve": reserve}
    except Exception as e:
        print(f"Error moving stock to watchlist: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to move stock to watchlist")