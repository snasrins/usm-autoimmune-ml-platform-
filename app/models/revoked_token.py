"""
Revoked Token Model - SQLAlchemy ORM
Stores revoked access tokens for blacklist checking
"""
from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from app.core.database import Base


class RevokedToken(Base):
    """Revoked Token database model for JWT token blacklisting"""
    __tablename__ = "revoked_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(255), unique=True, nullable=False, index=True)  # JWT ID (unique token identifier)
    token_type = Column(String(20), nullable=False)  # 'access' or 'refresh'
    user_id = Column(Integer, nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)  # Original token expiry
    reason = Column(String(100), nullable=True)  # logout, security, admin_action, etc.
    
    __table_args__ = (
        Index('idx_revoked_jti_expires', 'jti', 'expires_at'),  # Composite index for fast lookup
    )
    
    def __repr__(self):
        return f"<RevokedToken jti={self.jti[:20]}... type={self.token_type}>"
