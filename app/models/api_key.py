"""
API Key Management Model
For external integrations and programmatic access
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.core.database import Base
import secrets
import hashlib


class APIKey(Base):
    """
    API Keys for external integrations
    Allows programmatic access without JWT tokens
    """
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Key identification
    name = Column(String(100), nullable=False)  # e.g., "Mobile App Integration", "External Analytics"
    description = Column(Text)
    
    # Key hash (NEVER store raw key after initial generation)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 hash
    key_prefix = Column(String(12), nullable=False)  # First 8 chars for identification (e.g., "usm_key_abc123...")
    
    # Ownership
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Permissions
    role = Column(String(20), default="viewer")  # admin, researcher, viewer
    scopes = Column(Text)  # Comma-separated: "read:patients,write:predictions,read:models"
    
    # Rate limiting (separate from user limits)
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    
    # Status
    is_active = Column(Boolean, default=True)
    is_revoked = Column(Boolean, default=False)
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True))  # None = never expires
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True))
    revoked_by = Column(Integer, ForeignKey("users.id"))
    revocation_reason = Column(Text)
    
    @staticmethod
    def generate_key() -> tuple[str, str, str]:
        """
        Generate a new API key
        Returns: (raw_key, key_hash, key_prefix)
        
        Format: usm_key_<32_random_chars>
        Example: usm_key_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
        """
        random_part = secrets.token_urlsafe(32)[:32]  # 32 chars
        raw_key = f"usm_key_{random_part}"
        
        # Hash for storage
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Prefix for identification
        key_prefix = raw_key[:12]  # "usm_key_a1b2"
        
        return raw_key, key_hash, key_prefix
    
    @staticmethod
    def hash_key(raw_key: str) -> str:
        """Hash an API key for comparison"""
        return hashlib.sha256(raw_key.encode()).hexdigest()
    
    def to_dict(self, include_prefix=True):
        """Convert to dictionary (NEVER include raw key)"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "key_prefix": self.key_prefix if include_prefix else "***",
            "role": self.role,
            "scopes": self.scopes.split(",") if self.scopes else [],
            "is_active": self.is_active,
            "is_revoked": self.is_revoked,
            "rate_limit": self.rate_limit,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "usage_count": self.usage_count,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None
        }
