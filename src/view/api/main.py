import os
from datetime import datetime, timedelta
from pathlib import Path
import jwt
import base64
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment
from sqlalchemy.orm import Session
from database import get_db, User, engine, Base
from schemas import UserCreate, UserLogin, UserResponse, Token
from auth import get_password_hash, verify_password, create_access_token, verify_token


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bullseye API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
sg = SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetResponse(BaseModel):
    message: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Extract and validate user from JWT token in Authorization header."""
    token = credentials.credentials
    email = verify_token(token)
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

@app.post("/auth/signup", response_model=Token)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account with email and password validation."""
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }

@app.post("/auth/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user with email and password, returning access token."""
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return current_user

@app.post("/auth/reset-password", response_model=PasswordResetResponse)
def reset_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Send a password reset email to the user."""
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            return PasswordResetResponse(message="If the email exists in our system, a reset link has been sent")
        
        reset_token = jwt.encode({
            'email': request.email,
            'purpose': 'password-reset',
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, os.getenv('SECRET_KEY'), algorithm='HS256')
        
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/reset-password-confirm?token={reset_token}"
        
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
                    
                    <p class="email-text">Check the link below to reset your app login password. Please complete the reset within 24 hours.</p>
                    
                    <p class="email-text">Thank you!</p>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" class="reset-button">Reset Password 🡭</a>
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

        Check the link below to reset your app login password. Please complete the reset within 24 hours. 
        
        Thank you!

        {reset_url}

        Sincerely,
        The Bullseye Team
        """
        
        message = Mail(
            from_email=os.getenv('SENDER_EMAIL'),
            to_emails=request.email,
            subject='Reset Password',
            html_content=html_content,
            plain_text_content=text_content
        )
        
        # No more attachment code needed!
        sg.send(message)
        
        return PasswordResetResponse(message="Password reset email sent successfully")
        
    except Exception as e:
        print(f"SendGrid error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send reset email. Please try again.")

@app.post("/auth/confirm-reset-password")
def confirm_reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Confirm password reset and update user's password."""
    try:
        payload = jwt.decode(
            request.token, 
            os.getenv('SECRET_KEY'), 
            algorithms=['HS256']
        )
        
        email = payload.get('email')
        purpose = payload.get('purpose')
        
        if purpose != 'password-reset':
            raise HTTPException(status_code=400, detail="Invalid token")
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.hashed_password = get_password_hash(request.new_password)
        db.commit()
        
        return {"message": "Password reset successfully"}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    except Exception as e:
        print(f"Password reset confirm error: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset password")

@app.get("/")
def read_root():
    """Health check endpoint for API status."""
    return {"message": "Bullseye API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)