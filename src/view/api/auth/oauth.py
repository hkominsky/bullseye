import os
import httpx
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from config.database import get_db, User
from auth.security import create_access_token
from config.types import OAuthUserInfo

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"

GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
GITHUB_REDIRECT_URI = "http://localhost:8000/auth/github/callback"

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

router = APIRouter()

def get_or_create_oauth_user(user_info: OAuthUserInfo, db: Session):
    """Get existing user or create new one from OAuth provider."""
    user = db.query(User).filter(User.email == user_info.email).first()
    
    if not user:
        user = User(
            email=user_info.email,
            first_name=user_info.first_name,
            last_name=user_info.last_name,
            hashed_password="",
            oauth_provider=user_info.provider,
            oauth_provider_id=user_info.provider_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not user.oauth_provider:
            user.oauth_provider = user_info.provider
            user.oauth_provider_id = user_info.provider_id
            db.commit()
    
    return user

async def exchange_code_for_token(client: httpx.AsyncClient, token_url: str, token_data: dict) -> str:
    """Exchange authorization code for access token."""
    response = await client.post(token_url, data=token_data)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get access token")
    return response.json().get("access_token")

async def fetch_user_data(client: httpx.AsyncClient, user_url: str, token: str, token_type: str = "Bearer") -> dict:
    """Fetch user data from OAuth provider."""
    headers = {"Authorization": f"{token_type} {token}"}
    response = await client.get(user_url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get user info")
    return response.json()

def create_jwt_and_redirect(user: User, provider: str) -> RedirectResponse:
    """Create JWT token and return redirect response."""
    access_token_expires = timedelta(minutes=30)
    jwt_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return RedirectResponse(
        url=f"{FRONTEND_URL}/auth/callback?token={jwt_token}&provider={provider}"
    )

def handle_oauth_error(error: Exception, provider: str) -> RedirectResponse:
    """Handle OAuth errors with consistent error response."""
    print(f"{provider.title()} OAuth error: {error}")
    return RedirectResponse(url=f"{FRONTEND_URL}/login?error=oauth_failed")

@router.get("/google")
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

@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback."""
    try:
        async with httpx.AsyncClient() as client:
            token_data = {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
            }
            access_token = await exchange_code_for_token(
                client, "https://oauth2.googleapis.com/token", token_data
            )
            
            user_data = await fetch_user_data(
                client, "https://www.googleapis.com/oauth2/v2/userinfo", access_token
            )
            
            user_info = OAuthUserInfo(
                email=user_data["email"],
                first_name=user_data.get("given_name", ""),
                last_name=user_data.get("family_name", ""),
                provider="google",
                provider_id=user_data["id"]
            )
            
            user = get_or_create_oauth_user(user_info, db)
            return create_jwt_and_redirect(user, "google")
            
    except Exception as e:
        return handle_oauth_error(e, "google")

@router.get("/github")
def github_auth():
    """Initiate GitHub OAuth flow."""
    github_auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={GITHUB_CLIENT_ID}&"
        f"redirect_uri={GITHUB_REDIRECT_URI}&"
        f"scope=user:email"
    )
    return RedirectResponse(url=github_auth_url)

async def get_github_primary_email(client: httpx.AsyncClient, token: str) -> str:
    """Get primary email from GitHub API."""
    email_response = await client.get(
        "https://api.github.com/user/emails",
        headers={"Authorization": f"token {token}"}
    )
    
    if email_response.status_code == 200:
        emails = email_response.json()
        primary_email = next((email["email"] for email in emails if email["primary"]), None)
        if primary_email:
            return primary_email
    
    raise HTTPException(status_code=400, detail="No email found in GitHub profile")

def parse_github_name(full_name: str) -> tuple[str, str]:
    """Parse GitHub full name into first and last name."""
    if not full_name:
        return "", ""
    
    name_parts = full_name.split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    return first_name, last_name

@router.get("/github/callback")
async def github_callback(code: str, db: Session = Depends(get_db)):
    """Handle GitHub OAuth callback."""
    try:
        async with httpx.AsyncClient() as client:
            token_data = {
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            }
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data=token_data,
                headers={"Accept": "application/json"}
            )
            
            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            access_token = token_response.json().get("access_token")
            
            user_data = await fetch_user_data(
                client, "https://api.github.com/user", access_token, "token"
            )
            
            primary_email = await get_github_primary_email(client, access_token)
            
            first_name, last_name = parse_github_name(user_data.get("name", ""))
            
            user_info = OAuthUserInfo(
                email=primary_email,
                first_name=first_name,
                last_name=last_name,
                provider="github",
                provider_id=str(user_data["id"])
            )
            
            user = get_or_create_oauth_user(user_info, db)
            return create_jwt_and_redirect(user, "github")
            
    except Exception as e:
        return handle_oauth_error(e, "github")