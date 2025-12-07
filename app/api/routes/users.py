from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    cognito_sub: str
    full_name: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's information.
    
    Returns:
        User information including id, email, cognito_sub, full_name, and created_at
    """
    return current_user
