import os
import httpx
import secrets
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import jwt
import base64
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
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

# OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"

GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
GITHUB_REDIRECT_URI = "http://localhost:8000/auth/github/callback"

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetResponse(BaseModel):
    message: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class OAuthUserInfo(BaseModel):
    email: str
    first_name: str
    last_name: str
    provider: str
    provider_id: str

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

def get_or_create_oauth_user(user_info: OAuthUserInfo, db: Session):
    """Get existing user or create new one from OAuth provider."""
    user = db.query(User).filter(User.email == user_info.email).first()
    
    if not user:
        # Create new user
        user = User(
            email=user_info.email,
            first_name=user_info.first_name,
            last_name=user_info.last_name,
            hashed_password="",  # OAuth users don't have passwords
            oauth_provider=user_info.provider,
            oauth_provider_id=user_info.provider_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update existing user with OAuth info if not already set
        if not user.oauth_provider:
            user.oauth_provider = user_info.provider
            user.oauth_provider_id = user_info.provider_id
            db.commit()
    
    return user

# Google OAuth Routes
@app.get("/auth/google")
def google_auth():
    """Initiate Google OAuth flow."""
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"scope=openid email profile&"
        f"response_type=code&"
        f"access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)

@app.get("/auth/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback."""
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": GOOGLE_REDIRECT_URI,
                }
            )
            
            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get user info")
            
            user_data = user_response.json()
            
            user_info = OAuthUserInfo(
                email=user_data["email"],
                first_name=user_data.get("given_name", ""),
                last_name=user_data.get("family_name", ""),
                provider="google",
                provider_id=user_data["id"]
            )
            
            user = get_or_create_oauth_user(user_info, db)
            
            access_token_expires = timedelta(minutes=30)
            jwt_token = create_access_token(
                data={"sub": user.email}, expires_delta=access_token_expires
            )
            
            return RedirectResponse(
                url=f"{FRONTEND_URL}/auth/callback?token={jwt_token}&provider=google"
            )
            
    except Exception as e:
        print(f"Google OAuth error: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=oauth_failed")

@app.get("/auth/github")
def github_auth():
    """Initiate GitHub OAuth flow."""
    github_auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={GITHUB_CLIENT_ID}&"
        f"redirect_uri={GITHUB_REDIRECT_URI}&"
        f"scope=user:email"
    )
    return RedirectResponse(url=github_auth_url)

@app.get("/auth/github/callback")
async def github_callback(code: str, db: Session = Depends(get_db)):
    """Handle GitHub OAuth callback."""
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code,
                },
                headers={"Accept": "application/json"}
            )
            
            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            user_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {access_token}"}
            )
            
            if user_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get user info")
            
            user_data = user_response.json()
            
            email_response = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"token {access_token}"}
            )
            
            emails = email_response.json() if email_response.status_code == 200 else []
            primary_email = next((email["email"] for email in emails if email["primary"]), user_data.get("email"))
            
            if not primary_email:
                raise HTTPException(status_code=400, detail="No email found in GitHub profile")
            
            full_name = user_data.get("name", "").split(" ", 1)
            first_name = full_name[0] if full_name else ""
            last_name = full_name[1] if len(full_name) > 1 else ""
            
            user_info = OAuthUserInfo(
                email=primary_email,
                first_name=first_name,
                last_name=last_name,
                provider="github",
                provider_id=str(user_data["id"])
            )
            
            user = get_or_create_oauth_user(user_info, db)
            
            access_token_expires = timedelta(minutes=30)
            jwt_token = create_access_token(
                data={"sub": user.email}, expires_delta=access_token_expires
            )
            
            return RedirectResponse(
                url=f"{FRONTEND_URL}/auth/callback?token={jwt_token}&provider=github"
            )
            
    except Exception as e:
        print(f"GitHub OAuth error: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=oauth_failed")

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
        
        # Check if user already has a recent reset request (optional rate limiting)
        if (user.reset_token and user.reset_token_expiry and 
            user.reset_token_expiry > datetime.utcnow()):
            return PasswordResetResponse(message="Reset email already sent recently. Please check your inbox.")
        
        # Generate a secure random token
        reset_token = secrets.token_urlsafe(32)
        
        # Hash the token before storing (additional security)
        token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
        
        # Store hashed token and expiry in database
        user.reset_token = token_hash
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        # Send the unhashed token in the email
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
        
        message = Mail(
            from_email=os.getenv('SENDER_EMAIL'),
            to_emails=request.email,
            subject='Reset Password',
            html_content=html_content,
            plain_text_content=text_content
        )
        
        sg.send(message)
        
        return PasswordResetResponse(message="Password reset email sent successfully")
        
    except Exception as e:
        print(f"SendGrid error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send reset email. Please try again.")

@app.post("/auth/confirm-reset-password")
def confirm_reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Confirm password reset and update user's password."""
    try:
        token_hash = hashlib.sha256(request.token.encode()).hexdigest()
        
        user = db.query(User).filter(
            User.reset_token == token_hash,
            User.reset_token_expiry > datetime.utcnow()
        ).first()
        
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        user.hashed_password = get_password_hash(request.new_password)
        
        user.reset_token = None
        user.reset_token_expiry = None
        
        db.commit()
        
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
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