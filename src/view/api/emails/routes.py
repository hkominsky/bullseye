from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List
from pydantic import BaseModel
import logging
from sqlalchemy.orm import Session
from auth.security import get_current_user
from config.database import get_db, User
from config.types import CustomEmailRequest, EmailJobResponse
from src.controller.emails import EmailController

router = APIRouter(prefix="/api/email", tags=["email"])
logger = logging.getLogger(__name__)

@router.post("/send-watchlist", response_model=EmailJobResponse)
async def send_watchlist_emails(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send automated emails for all stocks in user's watchlist."""
    try:
        db.refresh(current_user)
        watchlist_tickers = current_user.get_watchlist_tickers()
        
        if not watchlist_tickers:
            raise HTTPException(
                status_code=400,
                detail="Watchlist is empty. Add stocks before sending emails."
            )
        
        user_email = current_user.email
        if not user_email:
            raise HTTPException(
                status_code=400,
                detail="User email not found in database."
            )
        
        email_controller = EmailController()
        background_tasks.add_task(
            email_controller.send_watchlist_emails,
            watchlist_tickers,
            user_email
        )
                
        return EmailJobResponse(
            message="Email processing started",
            ticker_count=len(watchlist_tickers),
            tickers=watchlist_tickers,
            status="processing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue email job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-custom", response_model=EmailJobResponse)
async def send_custom_emails(
    request: CustomEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send automated emails for custom list of tickers."""
    try:
        if not request.tickers:
            raise HTTPException(status_code=400, detail="No tickers provided")
        
        db.refresh(current_user)
        user_email = current_user.email
        if not user_email:
            raise HTTPException(status_code=400, detail="User email not found")
        
        email_controller = EmailController()
        background_tasks.add_task(
            email_controller.send_custom_emails,
            request.tickers,
            user_email
        )
                
        return EmailJobResponse(
            message="Email processing started",
            ticker_count=len(request.tickers),
            tickers=request.tickers,
            status="processing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue custom email job: {e}")
        raise HTTPException(status_code=500, detail=str(e))