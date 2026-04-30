"""
Authentication API Endpoints
Handles user registration, login, token management with refresh tokens
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import secrets

from app.core.database import get_db
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    decode_token
)
from app.core.config import settings
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.revoked_token import RevokedToken
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin
from app.api.deps import get_current_active_user, get_current_superuser

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    """
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        role=user_data.role,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    user_agent: Optional[str] = Header(None)
):
    """
    Login with username and password
    Returns JWT access and refresh tokens
    Stores refresh token in database for tracking and revocation
    """
    # Find user
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token with token_version and jti for blacklist checking
    access_token_data = {
        "sub": user.username,
        "user_id": user.id,
        "token_version": user.token_version,
        "jti": secrets.token_urlsafe(32)  # Unique token ID for blacklist
    }
    access_token = create_access_token(data=access_token_data)
    
    # Create refresh token
    refresh_token_data = {
        "sub": user.username,
        "user_id": user.id,
        "token_version": user.token_version,
        "jti": secrets.token_urlsafe(32)  # Unique token ID
    }
    refresh_token = create_refresh_token(data=refresh_token_data)
    
    # Store refresh token in database
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at,
        device_info=user_agent[:255] if user_agent else None
    )
    db.add(db_refresh_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information
    Requires valid JWT token
    """
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db),
    user_agent: Optional[str] = Header(None)
):
    """
    Get new access token using refresh token
    Validates refresh token and generates new token pair
    """
    # Decode refresh token
    try:
        payload = decode_token(refresh_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    username = payload.get("sub")
    user_id = payload.get("user_id")
    token_version = payload.get("token_version")
    
    if not username or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Check token version (for invalidation)
    if token_version != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated"
        )
    
    # Check if refresh token exists and is not revoked
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token,
        RefreshToken.user_id == user_id
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    if db_token.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )
    
    # Check if token expired
    if db_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    
    # Create new access token with jti for blacklist checking
    access_token_data = {
        "sub": user.username,
        "user_id": user.id,
        "token_version": user.token_version,
        "jti": secrets.token_urlsafe(32)  # Unique token ID for blacklist
    }
    new_access_token = create_access_token(data=access_token_data)
    
    # Optionally rotate refresh token (recommended for security)
    # Revoke old refresh token
    db_token.is_revoked = True
    db_token.revoked_at = datetime.now(timezone.utc)
    
    # Create new refresh token
    new_refresh_token_data = {
        "sub": user.username,
        "user_id": user.id,
        "token_version": user.token_version,
        "jti": secrets.token_urlsafe(32)
    }
    new_refresh_token = create_refresh_token(data=new_refresh_token_data)
    
    # Store new refresh token
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_db_refresh_token = RefreshToken(
        user_id=user.id,
        token=new_refresh_token,
        expires_at=expires_at,
        device_info=user_agent[:255] if user_agent else None
    )
    db.add(new_db_refresh_token)
    db.commit()
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    refresh_token: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Logout current user
    Revokes both access token (blacklist) and refresh token
    """
    # Blacklist the current access token
    if authorization and authorization.startswith("Bearer "):
        access_token = authorization.replace("Bearer ", "")
        try:
            payload = decode_token(access_token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if jti:
                # Add access token to blacklist
                revoked_access = RevokedToken(
                    jti=jti,
                    token_type="access",
                    user_id=current_user.id,
                    expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
                    reason="logout"
                )
                db.add(revoked_access)
        except HTTPException:
            pass  # Token already invalid, skip blacklisting
    
    # Revoke specific refresh token if provided
    if refresh_token:
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.user_id == current_user.id
        ).first()
        
        if db_token and not db_token.is_revoked:
            db_token.is_revoked = True
            db_token.revoked_at = datetime.now(timezone.utc)
    
    db.commit()
    
    return {
        "message": "Successfully logged out",
        "username": current_user.username
    }


@router.post("/logout-all")
async def logout_all_devices(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout from all devices
    Revokes all refresh tokens for the current user by incrementing token_version
    """
    # Increment token_version to invalidate all existing tokens
    current_user.token_version += 1
    db.commit()
    
    # Also revoke all refresh tokens in database
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_revoked == False
    ).update({
        "is_revoked": True,
        "revoked_at": datetime.now(timezone.utc)
    })
    db.commit()
    
    return {
        "message": "Successfully logged out from all devices",
        "username": current_user.username
    }


# ============================================================================
# JWT TOKEN EXPIRY MONITORING ENDPOINTS (USMA-91)
# ============================================================================

@router.get("/sessions")
async def get_my_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all active sessions (refresh tokens) for current user
    Shows when each session expires and device info
    """
    now = datetime.now(timezone.utc)
    
    # Get all refresh tokens for this user
    tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id
    ).order_by(RefreshToken.created_at.desc()).all()
    
    sessions = []
    for token in tokens:
        time_until_expiry = (token.expires_at - now).total_seconds()
        sessions.append({
            "id": token.id,
            "created_at": token.created_at.isoformat(),
            "expires_at": token.expires_at.isoformat(),
            "is_revoked": token.is_revoked,
            "revoked_at": token.revoked_at.isoformat() if token.revoked_at else None,
            "device_info": token.device_info,
            "is_expired": token.expires_at < now,
            "time_until_expiry_hours": round(time_until_expiry / 3600, 2) if time_until_expiry > 0 else 0,
            "status": "expired" if token.expires_at < now else ("revoked" if token.is_revoked else "active")
        })
    
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "token_version": current_user.token_version,
        "total_sessions": len(sessions),
        "active_sessions": len([s for s in sessions if s["status"] == "active"]),
        "sessions": sessions
    }


@router.get("/admin/token-stats")
async def get_token_statistics(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get global JWT token statistics (admin only)
    Shows overview of all tokens across all users
    """
    now = datetime.now(timezone.utc)
    
    # Refresh token stats
    total_refresh_tokens = db.query(RefreshToken).count()
    active_refresh_tokens = db.query(RefreshToken).filter(
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > now
    ).count()
    revoked_refresh_tokens = db.query(RefreshToken).filter(
        RefreshToken.is_revoked == True
    ).count()
    expired_refresh_tokens = db.query(RefreshToken).filter(
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at <= now
    ).count()
    
    # Revoked (blacklisted) token stats
    total_blacklisted = db.query(RevokedToken).count()
    blacklisted_not_expired = db.query(RevokedToken).filter(
        RevokedToken.expires_at > now
    ).count()
    blacklisted_expired = db.query(RevokedToken).filter(
        RevokedToken.expires_at <= now
    ).count()
    
    # User stats
    total_users = db.query(User).count()
    users_with_sessions = db.query(RefreshToken.user_id).filter(
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > now
    ).distinct().count()
    
    # Revocation reasons breakdown
    revocation_reasons = db.query(
        RevokedToken.reason,
        func.count(RevokedToken.id).label('count')
    ).group_by(RevokedToken.reason).all()
    
    return {
        "timestamp": now.isoformat(),
        "refresh_tokens": {
            "total": total_refresh_tokens,
            "active": active_refresh_tokens,
            "revoked": revoked_refresh_tokens,
            "expired": expired_refresh_tokens
        },
        "blacklist": {
            "total": total_blacklisted,
            "still_valid": blacklisted_not_expired,
            "expired": blacklisted_expired
        },
        "users": {
            "total": total_users,
            "with_active_sessions": users_with_sessions
        },
        "revocation_reasons": {reason: count for reason, count in revocation_reasons}
    }


@router.get("/admin/sessions")
async def get_all_sessions(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
    user_id: Optional[int] = None,
    active_only: bool = False
) -> Dict[str, Any]:
    """
    Get all sessions across all users (admin only)
    Optionally filter by user_id or active_only
    """
    now = datetime.now(timezone.utc)
    
    # Build query
    query = db.query(RefreshToken).join(User)
    
    if user_id:
        query = query.filter(RefreshToken.user_id == user_id)
    
    if active_only:
        query = query.filter(
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > now
        )
    
    tokens = query.order_by(RefreshToken.created_at.desc()).all()
    
    sessions = []
    for token in tokens:
        time_until_expiry = (token.expires_at - now).total_seconds()
        sessions.append({
            "id": token.id,
            "user_id": token.user_id,
            "username": token.user.username,
            "email": token.user.email,
            "created_at": token.created_at.isoformat(),
            "expires_at": token.expires_at.isoformat(),
            "is_revoked": token.is_revoked,
            "revoked_at": token.revoked_at.isoformat() if token.revoked_at else None,
            "device_info": token.device_info,
            "is_expired": token.expires_at < now,
            "time_until_expiry_hours": round(time_until_expiry / 3600, 2) if time_until_expiry > 0 else 0,
            "status": "expired" if token.expires_at < now else ("revoked" if token.is_revoked else "active")
        })
    
    return {
        "total_sessions": len(sessions),
        "filters": {
            "user_id": user_id,
            "active_only": active_only
        },
        "sessions": sessions
    }


@router.delete("/admin/sessions/{token_id}")
async def revoke_session(
    token_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Revoke a specific refresh token session (admin only)
    Immediately invalidates the session
    """
    token = db.query(RefreshToken).filter(RefreshToken.id == token_id).first()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {token_id} not found"
        )
    
    if token.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session {token_id} is already revoked"
        )
    
    # Revoke the token
    token.is_revoked = True
    token.revoked_at = datetime.now(timezone.utc)
    db.commit()
    
    return {
        "message": f"Session {token_id} revoked successfully",
        "token_id": token_id,
        "user_id": token.user_id,
        "username": token.user.username
    }
