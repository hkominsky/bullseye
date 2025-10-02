import os
import secrets
import hashlib
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sqlalchemy.orm import Session
from config.database import get_db, User
from auth.security import get_password_hash
from config.schemas import PasswordResetRequest, PasswordResetResponse, PasswordResetConfirm

send_grid = SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
router = APIRouter()

def generate_reset_token() -> tuple[str, str]:
    """Generate a reset token and its hash."""
    reset_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
    return reset_token, token_hash

def is_reset_token_valid(user: User) -> bool:
    """Check if user already has a valid reset token."""
    return (user.reset_token and user.reset_token_expiry and 
            user.reset_token_expiry > datetime.utcnow())

def update_user_reset_token(user: User, token_hash: str, db: Session) -> None:
    """Update user's reset token and expiry."""
    user.reset_token = token_hash
    user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
    db.commit()

def create_reset_email_content(reset_url: str) -> tuple[str, str]:
    """Create HTML and text content for reset email."""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Password</title>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                line-height: 1.6;
            }}
            
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 8px;
            }}
            
            .email-content {{
                margin-bottom: 40px;
            }}
            
            .email-text {{
                font-size: 16px;
                margin-bottom: 20px;
            }}
            
            .reset-button {{
                display: inline-block;
                margin: 5px 0;
                padding: 7px 17px;
                background-color: #7dca9c;
                border-radius: 13px;
                color: #ffffff !important;
                text-decoration: none !important;
                font-size: 17px;
                font-weight: normal;
                cursor: pointer;
                transition: background-color 0.2s ease;
            }}
            
            .reset-button:hover {{
                background-color: #5cac7c;
                color: #ffffff !important;
            }}
            
            a.reset-button {{
                color: #ffffff !important;
            }}
            
            a.reset-button:visited {{
                color: #ffffff !important;
            }}
            
            a.reset-button:active {{
                color: #ffffff !important;
            }}
            
            @media only screen and (max-width: 600px) {{
                body {{
                    padding: 10px;
                }}
                .email-container {{
                    padding: 20px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="logo-header" style="text-align: center; margin-bottom: 30px; padding-bottom: 20px;">
                <img src="https://cdn.mcauto-images-production.sendgrid.net/2c9d147728e484c3/da122e1a-61cd-416c-9d1d-d39efce750f1/315x80.png" 
                    alt="Bullseye Logo" 
                    style="max-height: 60px; width: auto; object-fit: contain;" />
            </div>
            
            <div class="email-content">
                <p class="email-text">Dear Valued Client,</p>
                
                <p class="email-text">Check the link below to reset your app login password. Please complete the reset within 1 hour.</p>
                
                <p class="email-text">If you didn't request this reset, please ignore this email.</p>
                
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" class="reset-button">Reset Password →</a>
                </p>
                
                <p class="email-text" style="margin-top: 30px;">
                    Sincerely,<br>
                    The Bullseye Team
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Dear Valued Client,

    Check the link below to reset your app login password. Please complete the reset within 1 hour.
    
    If you didn't request this reset, please ignore this email.

    {reset_url}

    Sincerely,
    The Bullseye Team
    """
    
    return html_content, text_content

def send_reset_email(email: str, reset_url: str) -> None:
    """Send password reset email via SendGrid."""
    html_content, text_content = create_reset_email_content(reset_url)
    
    message = Mail(
        from_email=os.getenv('SENDER_EMAIL'),
        to_emails=email,
        subject='Reset Password',
        html_content=html_content,
        plain_text_content=text_content
    )
    
    send_grid.send(message)

def find_user_by_reset_token(token: str, db: Session) -> User:
    """Find user by valid reset token."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    user = db.query(User).filter(
        User.reset_token == token_hash,
        User.reset_token_expiry > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    return user

def clear_reset_token(user: User, new_password: str, db: Session) -> None:
    """Update user password and clear reset token."""
    user.hashed_password = get_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.commit()

@router.post("/reset-password", response_model=PasswordResetResponse)
def reset_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Send a password reset email to the user."""
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            return PasswordResetResponse(message="If the email exists in our system, a reset link has been sent")
        
        if is_reset_token_valid(user):
            return PasswordResetResponse(message="Reset email already sent recently. Please check your inbox.")
        
        reset_token, token_hash = generate_reset_token()
        update_user_reset_token(user, token_hash, db)
        
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/reset-password-confirm?token={reset_token}"
        send_reset_email(request.email, reset_url)
        
        return PasswordResetResponse(message="Password reset email sent successfully")
        
    except Exception as e:
        print(f"SendGrid error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send reset email. Please try again.")

@router.post("/confirm-reset-password")
def confirm_reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Confirm password reset and update user's password."""
    try:
        user = find_user_by_reset_token(request.token, db)
        clear_reset_token(user, request.new_password, db)
        
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Password reset confirm error: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset password")