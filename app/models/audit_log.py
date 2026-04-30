"""
Audit Logging Model
Comprehensive tracking of all data access and modifications
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    """
    Comprehensive audit trail for compliance and security
    Tracks WHO did WHAT, WHEN, WHERE, and WHY
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # WHO (User identification)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    username = Column(String(100), index=True)  # Denormalized for query performance
    user_role = Column(String(20))  # admin, researcher, viewer
    
    # WHAT (Action details)
    action = Column(String(50), nullable=False, index=True)
    # Examples: "DATA_ACCESS", "DATA_MODIFY", "MODEL_TRAIN", "MODEL_DEPLOY", 
    #           "PREDICTION_CREATE", "USER_LOGIN", "USER_LOGOUT", "API_KEY_CREATE"
    
    resource_type = Column(String(50), index=True)
    # Examples: "patient", "prediction", "model", "dataset", "api_key", "training_job"
    
    resource_id = Column(String(100), index=True)
    # ID of the resource accessed/modified
    
    endpoint = Column(String(200))  # API endpoint called
    http_method = Column(String(10))  # GET, POST, PUT, DELETE
    
    # WHEN
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # WHERE (Network context)
    ip_address = Column(INET)
    user_agent = Column(Text)
    request_id = Column(String(100), index=True)  # For tracing requests across services
    
    # WHY / Context
    description = Column(Text)  # Human-readable description
    
    # HOW (Technical details)
    request_payload = Column(JSONB)  # Sanitized request body (NO PII)
    response_status = Column(Integer)  # HTTP status code
    response_time_ms = Column(Integer)  # Response time in milliseconds
    
    # Changes (for UPDATE/DELETE operations)
    changes = Column(JSONB)
    # Example: {"old": {"status": "active"}, "new": {"status": "inactive"}}
    
    # Data access tracking (CRITICAL for PDPA/GDPR compliance)
    data_accessed = Column(JSONB)
    # Example: {"patient_ids": [1, 2, 3], "fields": ["age", "gender", "lab_results"]}
    
    # Security flags
    is_sensitive = Column(Boolean, default=False)  # Flag for sensitive operations
    is_suspicious = Column(Boolean, default=False)  # Flag for anomaly detection
    
    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text)  # If failed
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_action_timestamp', 'action', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_ip_timestamp', 'ip_address', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user={self.username}, action={self.action}, resource={self.resource_type}:{self.resource_id})>"


class DataAccessLog(Base):
    """
    Specialized audit log for patient data access (PDPA/GDPR compliance)
    More detailed tracking for sensitive medical data
    """
    __tablename__ = "data_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # WHO accessed
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    username = Column(String(100), nullable=False)
    user_role = Column(String(20))
    
    # WHAT data was accessed
    patient_id = Column(Integer, ForeignKey("patients.id"), index=True)
    patient_anonymous_id = Column(String(50), index=True)  # e.g., "USMA-2026-0001"
    
    # Data fields accessed
    fields_accessed = Column(JSONB)
    # Example: ["age", "gender", "diagnosis", "lab_results.CRP", "lab_results.ESR"]
    
    # Purpose of access
    access_purpose = Column(String(100))
    # Examples: "clinical_review", "ml_training", "research_analysis", "prediction"
    
    # WHEN
    accessed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # WHERE
    ip_address = Column(INET)
    endpoint = Column(String(200))
    
    # Context
    justification = Column(Text)  # Why was this data accessed?
    
    # Compliance flags
    consent_verified = Column(Boolean, default=False)  # Was patient consent verified?
    ethics_clearance_id = Column(String(50))  # Reference to ethics approval
    
    # Indexes
    __table_args__ = (
        Index('idx_data_access_patient_time', 'patient_id', 'accessed_at'),
        Index('idx_data_access_user_time', 'user_id', 'accessed_at'),
    )
