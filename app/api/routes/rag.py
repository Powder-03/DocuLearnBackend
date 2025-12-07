import httpx
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Any, Dict, Optional

from app.core.config import settings
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Proxy endpoint to the RAG Service's upload endpoint.
    
    Flow:
    1. Authenticate user via cookie
    2. Accept file upload
    3. Inject user_id into form data
    4. Forward multipart request to internal RAG Service
    5. Return response from AI service
    
    Args:
        file: Uploaded file
        metadata: Optional metadata about the file
        current_user: Authenticated user from dependency
        
    Returns:
        Response from the RAG Service
    """
    # Prepare file and form data
    file_content = await file.read()
    
    # Forward to RAG Service with user_id
    service_url = f"{settings.RAG_SERVICE_URL}/upload-and-plan"
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            # Prepare multipart form data
            files = {
                "file": (file.filename, file_content, file.content_type)
            }
            data = {
                "user_id": str(current_user.id)
            }
            
            if metadata:
                data["metadata"] = metadata
            
            response = await client.post(
                service_url,
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"RAG service error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to communicate with RAG service: {str(e)}"
        )


@router.post("/query")
async def query_rag(
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Proxy endpoint to the RAG Service's query endpoint.
    
    Flow:
    1. Authenticate user via cookie
    2. Extract request body
    3. Inject user_id into payload
    4. Forward request to internal RAG Service
    5. Return response from AI service
    
    Args:
        request_data: Query parameters
        current_user: Authenticated user from dependency
        
    Returns:
        Response from the RAG Service
    """
    # Inject user_id into the payload
    request_data["user_id"] = str(current_user.id)
    
    # Forward to RAG Service
    service_url = f"{settings.RAG_SERVICE_URL}/query"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                service_url,
                json=request_data
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"RAG service error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to communicate with RAG service: {str(e)}"
        )
