"""
Patient Model - SQLAlchemy ORM (Updated for Flexible Schema)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Patient(Base):
    """Patient database model - core demographics only"""
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Anonymous identifiers (PII protection)
    anonymous_id = Column(String(50), unique=True, nullable=False, index=True)
    # Format: USMA-2026-0001, USMA-2026-0002, etc.
    
    # Original identifier (hashed for security)
    original_id_hash = Column(String(64), unique=True, index=True)  # SHA-256 hash
    
    # Demographics (common to all diseases)
    age = Column(Integer)  # Actual age at time of data collection
    age_range = Column(String(20))  # 20-29, 30-39, etc. (for anonymization)
    gender = Column(String(10))  # Male, Female, Other
    ethnicity = Column(String(50))  # Malay, Chinese, Indian, Other
    
    # Contact information (encrypted)
    contact_encrypted = Column(Text)  # Encrypted JSON containing phone, email, address
    
    # Data source tracking
    data_source = Column(String(100))  # "AAM-SLE-E Dataset", "Sjogren Dataset", "Manual Entry"
    import_batch_id = Column(UUID(as_uuid=True), default=uuid.uuid4, index=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_anonymized = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Additional metadata as JSONB (flexible)
    additional_data = Column(JSONB)
    # Example: {"hospital": "USM", "department": "Rheumatology", "consent_date": "2026-01-15"}
    
    # Indexes
    __table_args__ = (
        Index('idx_anonymous_id', 'anonymous_id'),
        Index('idx_import_batch', 'import_batch_id'),
        Index('idx_age_gender', 'age', 'gender'),
    )
    
    def __repr__(self):
        return f"<Patient {self.anonymous_id}>"
