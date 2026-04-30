"""
API Key Management Endpoints
Create, list, revoke API keys for external integrations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.deps import get_current_superuser
from app.models.user import User
from app.models.api_key import APIKey

router = APIRouter()


# Pydantic Schemas
class APIKeyCreate(BaseModel):
    """Request to create new API key"""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    role: str = Field(default="viewer", pattern="^(admin|researcher|viewer)$")
    scopes: Optional[List[str]] = None  # ["read:patients", "write:predictions"]
    rate_limit: int = Field(default=1000, ge=100, le=10000)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """Response for created API key (includes raw key ONCE)"""
    id: int
    name: str
    key: str  # RAW KEY - shown ONLY once
    key_prefix: str
    role: str
    scopes: List[str]
    rate_limit: int
    expires_at: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


class APIKeyInfo(BaseModel):
    """Info about existing API key (NO raw key)"""
    id: int
    name: str
    key_prefix: str
    role: str
    scopes: List[str]
    is_active: bool
    is_revoked: bool
    rate_limit: int
    last_used_at: Optional[str]
    usage_count: int
    expires_at: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("/keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Create a new API key (admin only)
    
    ⚠️ WARNING: The raw API key is shown ONLY ONCE!
    Store it securely - it cannot be retrieved later.
    """
    # Generate key
    raw_key, key_hash, key_prefix = APIKey.generate_key()
    
    # Calculate expiration
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
    
    # Create API key record
    api_key = APIKey(
        name=key_data.name,
        description=key_data.description,
        key_hash=key_hash,
        key_prefix=key_prefix,
        created_by=current_user.id,
        role=key_data.role,
        scopes=",".join(key_data.scopes) if key_data.scopes else "",
        rate_limit=key_data.rate_limit,
        expires_at=expires_at
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key=raw_key,  # ⚠️ SHOWN ONLY ONCE
        key_prefix=api_key.key_prefix,
        role=api_key.role,
        scopes=api_key.scopes.split(",") if api_key.scopes else [],
        rate_limit=api_key.rate_limit,
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
        created_at=api_key.created_at.isoformat()
    )


@router.get("/keys", response_model=List[APIKeyInfo])
async def list_api_keys(
    skip: int = 0,
    limit: int = 100,
    include_revoked: bool = False,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    List all API keys (admin only)
    """
    query = db.query(APIKey)
    
    if not include_revoked:
        query = query.filter(APIKey.is_revoked == False)
    
    keys = query.offset(skip).limit(limit).all()
    
    return [
        APIKeyInfo(
            id=key.id,
            name=key.name,
            key_prefix=key.key_prefix,
            role=key.role,
            scopes=key.scopes.split(",") if key.scopes else [],
            is_active=key.is_active,
            is_revoked=key.is_revoked,
            rate_limit=key.rate_limit,
            last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
            usage_count=key.usage_count,
            expires_at=key.expires_at.isoformat() if key.expires_at else None,
            created_at=key.created_at.isoformat()
        )
        for key in keys
    ]


@router.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Revoke an API key (admin only)
    Revoked keys cannot be reactivated
    """
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    if api_key.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key already revoked"
        )
    
    # Revoke
    api_key.is_revoked = True
    api_key.is_active = False
    api_key.revoked_at = datetime.utcnow()
    api_key.revoked_by = current_user.id
    api_key.revocation_reason = reason or "Revoked by admin"
    
    db.commit()
    
    return {
        "message": f"API key '{api_key.name}' ({api_key.key_prefix}...) has been revoked",
        "revoked_at": api_key.revoked_at.isoformat()
    }


@router.get("/keys/{key_id}/usage")
async def get_api_key_usage(
    key_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Get usage statistics for an API key
    """
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Get audit logs for this API key (would need to implement)
    # For now, return basic stats
    
    return {
        "key_id": api_key.id,
        "name": api_key.name,
        "total_requests": api_key.usage_count,
        "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        "created_at": api_key.created_at.isoformat(),
        "is_active": api_key.is_active,
        "rate_limit": api_key.rate_limit
    }
