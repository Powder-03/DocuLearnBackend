import requests
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import urlencode

from app.core.config import settings
from app.core.security import decode_id_token
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.get("/login")
async def login():
    """
    Redirect user to the Cognito Hosted UI for authentication.
    
    This initiates the OAuth2 Authorization Code Flow.
    """
    params = {
        "client_id": settings.COGNITO_CLIENT_ID,
        "response_type": "code",
        "scope": "email openid profile",
        "redirect_uri": settings.REDIRECT_URI,
    }
    
    cognito_login_url = f"https://{settings.COGNITO_DOMAIN}/oauth2/authorize?{urlencode(params)}"
    
    return RedirectResponse(url=cognito_login_url)


@router.get("/callback")
async def callback(code: str, db: Session = Depends(get_db)):
    """
    OAuth2 callback endpoint that receives the authorization code from Cognito.
    
    Flow:
    1. Exchange the authorization code for tokens
    2. Decode the ID token to get user information
    3. Implement JIT (Just-In-Time) provisioning - create user if doesn't exist
    4. Set access token in HTTP-only cookie
    5. Redirect to frontend dashboard
    
    Args:
        code: Authorization code from Cognito
        db: Database session
        
    Returns:
        RedirectResponse to frontend with access token set in cookie
    """
    # Step 1: Exchange code for tokens
    token_url = f"https://{settings.COGNITO_DOMAIN}/oauth2/token"
    
    token_data = {
        "grant_type": "authorization_code",
        "client_id": settings.COGNITO_CLIENT_ID,
        "client_secret": settings.COGNITO_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.REDIRECT_URI,
    }
    
    try:
        token_response = requests.post(
            token_url,
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        token_response.raise_for_status()
        tokens = token_response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange code for tokens: {str(e)}"
        )
    
    # Step 2: Extract tokens
    access_token = tokens.get("access_token")
    id_token = tokens.get("id_token")
    
    if not access_token or not id_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing tokens in response"
        )
    
    # Step 3: Decode ID token to get user info
    try:
        user_info = decode_id_token(id_token)
        cognito_sub = user_info.get("sub")
        email = user_info.get("email")
        full_name = user_info.get("name", email.split("@")[0])  # Fallback to email username
        
        if not cognito_sub or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required user information in ID token"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to decode ID token: {str(e)}"
        )
    
    # Step 4: JIT Provisioning - Check if user exists, create if not
    user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
    
    if not user:
        # Create new user
        user = User(
            cognito_sub=cognito_sub,
            email=email,
            full_name=full_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Step 5: Create response with redirect to frontend
    response = RedirectResponse(
        url=f"{settings.FRONTEND_URL}/dashboard",
        status_code=status.HTTP_302_FOUND
    )
    
    # Step 6: Set access token in secure HTTP-only cookie
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=access_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=3600,  # 1 hour (match Cognito token expiration)
    )
    
    return response


@router.post("/logout")
async def logout(response: Response):
    """
    Log out the user by clearing the access token cookie.
    
    Returns:
        Success message with cookie cleared
    """
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )
    
    return {"message": "Successfully logged out"}


@router.get("/status")
async def auth_status(request: Request):
    """
    Check if user is authenticated by verifying cookie presence.
    Does not validate the token - just checks if it exists.
    
    Returns:
        Authentication status
    """
    token = request.cookies.get(settings.COOKIE_NAME)
    
    return {
        "authenticated": token is not None,
        "cookie_name": settings.COOKIE_NAME
    }
