import requests
from jose import jwt, JWTError
from typing import Dict, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from app.core.config import settings

# Cache for JWKS keys (expires every hour)
_jwks_cache: Optional[Dict] = None
_jwks_cache_time: Optional[datetime] = None
_CACHE_DURATION = timedelta(hours=1)


def get_jwks_keys() -> Dict:
    """
    Fetch and cache the JWKS keys from Cognito.
    Keys are cached for 1 hour to reduce external API calls.
    """
    global _jwks_cache, _jwks_cache_time
    
    now = datetime.utcnow()
    
    # Return cached keys if still valid
    if _jwks_cache and _jwks_cache_time and (now - _jwks_cache_time) < _CACHE_DURATION:
        return _jwks_cache
    
    # Fetch new keys
    jwks_url = (
        f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
        f"{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    )
    
    try:
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_cache_time = now
        return _jwks_cache
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch JWKS keys: {str(e)}"
        )


def verify_token(token: str) -> Dict:
    """
    Verify and decode a JWT token from AWS Cognito.
    
    Args:
        token: The JWT access token or ID token
        
    Returns:
        Dict containing the decoded token payload with user information
        
    Raises:
        HTTPException: If token is invalid, expired, or verification fails
    """
    try:
        # Get the JWKS keys
        jwks = get_jwks_keys()
        
        # Get the kid from the token header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token header missing 'kid' field"
            )
        
        # Find the matching key
        key = None
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == kid:
                key = jwk
                break
        
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find matching key for token"
            )
        
        # Verify the token
        issuer = f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"
        
        payload = jwt.decode(
            token,
            key,
            algorithms=[settings.ALGORITHM],
            audience=settings.COGNITO_CLIENT_ID,
            issuer=issuer,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
                "verify_iss": True,
            }
        )
        
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )


def decode_id_token(id_token: str) -> Dict:
    """
    Decode an ID token from Cognito without full verification.
    Used during the OAuth callback to extract user information.
    
    Args:
        id_token: The JWT ID token from Cognito
        
    Returns:
        Dict containing user information (email, sub, etc.)
    """
    try:
        # Get the JWKS keys
        jwks = get_jwks_keys()
        
        # Get the kid from the token header
        unverified_header = jwt.get_unverified_header(id_token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ID token header missing 'kid' field"
            )
        
        # Find the matching key
        key = None
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == kid:
                key = jwk
                break
        
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find matching key for ID token"
            )
        
        # Verify the ID token
        issuer = f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"
        
        payload = jwt.decode(
            id_token,
            key,
            algorithms=[settings.ALGORITHM],
            audience=settings.COGNITO_CLIENT_ID,
            issuer=issuer,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
                "verify_iss": True,
            }
        )
        
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid ID token: {str(e)}"
        )
