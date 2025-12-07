import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Any, Dict

from app.core.config import settings
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/generation", tags=["generation"])


@router.post("/create-plan")
async def create_plan(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Proxy endpoint to the Generation Service's create-plan endpoint.
    
    Flow:
    1. Authenticate user via cookie
    2. Extract request body
    3. Inject user_id into payload
    4. Forward request to internal Generation Service
    5. Return response from AI service
    
    Args:
        request: FastAPI request object
        current_user: Authenticated user from dependency
        
    Returns:
        Response from the Generation Service
    """
    # Extract request body
    try:
        body = await request.json()
    except Exception:
        body = {}
    
    # Inject user_id into the payload
    body["user_id"] = str(current_user.id)
    
    # Forward to Generation Service
    service_url = f"{settings.GENERATION_SERVICE_URL}/create_plan"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                service_url,
                json=body
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Generation service error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to communicate with generation service: {str(e)}"
        )


@router.post("/chat")
async def chat(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Proxy endpoint to the Generation Service's chat endpoint.
    
    Flow:
    1. Authenticate user via cookie
    2. Extract request body
    3. Inject user_id into payload
    4. Forward request to internal Generation Service
    5. Return response from AI service
    
    Args:
        request: FastAPI request object
        current_user: Authenticated user from dependency
        
    Returns:
        Response from the Generation Service
    """
    # Extract request body
    try:
        body = await request.json()
    except Exception:
        body = {}
    
    # Inject user_id into the payload
    body["user_id"] = str(current_user.id)
    
    # Forward to Generation Service
    service_url = f"{settings.GENERATION_SERVICE_URL}/learn/generation"
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                service_url,
                json=body
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Generation service error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to communicate with generation service: {str(e)}"
        )
