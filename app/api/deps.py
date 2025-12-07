from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_token
from app.db.session import get_db
from app.models.user import User


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Flow:
    1. Extract access token from HTTP-only cookie
    2. Verify the token with Cognito's JWKS
    3. Extract cognito_sub from the token payload
    4. Query the database for the user
    5. Return the User object
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        User object for the authenticated user
        
    Raises:
        HTTPException: 401 if token is missing, invalid, or user not found
    """
    # Step 1: Extract token from cookie
    token = request.cookies.get(settings.COOKIE_NAME)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Missing access token cookie.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Step 2: Verify the token
    try:
        payload = verify_token(token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Step 3: Extract cognito_sub from payload
    cognito_sub = payload.get("sub")
    
    if not cognito_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing 'sub' claim",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Step 4: Query database for user
    user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in database",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Step 5: Return user
    return user


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User | None:
    """
    Optional dependency to get the current user if authenticated.
    Does not raise an exception if the user is not authenticated.
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None
