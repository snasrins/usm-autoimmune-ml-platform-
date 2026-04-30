"""
API Dependencies - Reusable dependency functions
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from typing import List, Callable
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.revoked_token import RevokedToken

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Role definitions for RBAC
class UserRole:
    """User role constants"""
    ADMIN = "admin"
    RESEARCHER = "researcher"
    VIEWER = "viewer"


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    Validates token_version to support token invalidation
    Checks token blacklist for revoked tokens
    Use as dependency: current_user: User = Depends(get_current_user)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        token_version: int = payload.get("token_version")
        jti: str = payload.get("jti")  # JWT ID for blacklist checking
        
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Check if token is blacklisted (revoked)
    if jti:
        revoked_token = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
        if revoked_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    # Validate token version (allows invalidating all tokens for a user)
    if token_version is not None and token_version != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (must be active)
    Use as dependency: user: User = Depends(get_current_active_user)
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current superuser (must be superuser)
    Use for admin-only endpoints
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )
    return current_user


def require_role(allowed_roles: List[str]) -> Callable:
    """
    RBAC Decorator - Require specific roles to access endpoint
    
    Usage:
        @router.post("/upload")
        async def upload(
            current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.RESEARCHER]))
        ):
            ...
    
    Args:
        allowed_roles: List of allowed role strings (e.g., ['admin', 'researcher'])
    
    Returns:
        Dependency function that validates user role
    
    Raises:
        HTTPException: 403 if user doesn't have required role
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}. Your role: {current_user.role}"
            )
        return current_user
    
    return role_checker


def require_admin(
    current_user: User = Depends(require_role([UserRole.ADMIN]))
) -> User:
    """Shorthand for admin-only access"""
    return current_user


def require_researcher_or_admin(
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.RESEARCHER]))
) -> User:
    """Shorthand for researcher or admin access"""
    return current_user
