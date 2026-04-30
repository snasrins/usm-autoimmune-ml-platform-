"""
Uploaded Files Model - Track all data file uploads
"""
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class UploadedFile(Base):
    """Track uploaded data files with metadata and processing status"""
    __tablename__ = "uploaded_files"
    
    file_id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)  # UUID-based name for security
    file_path = Column(Text, nullable=False)  # Full path where file is stored
    file_size_bytes = Column(BigInteger, nullable=False)
    file_type = Column(String(50), nullable=False)  # CSV, XLSX, XLS, PDF, DICOM
    mime_type = Column(String(100))
    
    # Encryption (files stored encrypted at rest)
    is_encrypted = Column(Boolean, default=True)
    encryption_key_id = Column(String(100))  # Reference to key management service
    
    # File metadata
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash for integrity
    row_count = Column(Integer)  # For CSV/Excel files
    column_count = Column(Integer)
    
    # Column mapping (important for flexibility!)
    column_mapping = Column(JSONB)
    # Example:
    # {
    #   "source_columns": ["IL-12 p70", "TNF-alpha", "IFN-gamma"],
    #   "mapped_to": {"IL-12 p70": "il12_p70", "TNF-alpha": "tnf_alpha", "IFN-gamma": "ifn_gamma"},
    #   "unmapped": ["some_unknown_test"],
    #   "detected_tests": 61,
    #   "new_tests": 3
    # }
    
    # Processing status
    upload_status = Column(String(20), default='pending', index=True)
    # Status flow: pending → validating → validated → processing → processed → failed
    validation_errors = Column(JSONB)  # Store validation errors as JSON
    processing_errors = Column(JSONB)  # Store processing errors as JSON
    
    # Import statistics
    import_stats = Column(JSONB)
    # Example:
    # {
    #   "patients_imported": 110,
    #   "new_patients": 15,
    #   "updated_patients": 95,
    #   "lab_results_imported": 6710,
    #   "errors": 0,
    #   "warnings": 5
    # }
    
    # Disease/dataset type
    dataset_type = Column(String(100))  # SLE, Sjogren, RA, Mixed, etc.
    
    # Audit fields
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    uploader = relationship("User", backref="uploaded_files")
    
    # Indexes
    __table_args__ = (
        Index('idx_upload_status', 'upload_status'),
        Index('idx_uploaded_by', 'uploaded_by'),
        Index('idx_uploaded_at', 'uploaded_at'),
        Index('idx_file_hash', 'file_hash'),  # Prevent duplicate uploads
    )
    
    def __repr__(self):
        return f"<UploadedFile {self.original_filename} status={self.upload_status}>"


class DataIngestionAudit(Base):
    """Audit trail for all data ingestion operations"""
    __tablename__ = "data_ingestion_audit"
    
    audit_id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("uploaded_files.file_id", ondelete="SET NULL"))
    batch_id = Column(String(36), nullable=False, index=True)  # UUID for grouping related operations
    
    # Action details
    action_type = Column(String(50), nullable=False, index=True)
    # upload, validate, transform, load, anonymize, delete, update, export
    action_status = Column(String(20), nullable=False, index=True)  # success, failed, warning
    
    # Data affected
    table_name = Column(String(100))
    records_affected = Column(Integer, default=0)
    patients_affected = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text)
    error_details = Column(JSONB)
    
    # Performance metrics
    execution_time_ms = Column(Integer)
    
    # User context
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    performed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    
    # Relationships
    file = relationship("UploadedFile", backref="audit_logs")
    user = relationship("User", backref="audit_actions")
    
    # Indexes
    __table_args__ = (
        Index('idx_batch_id', 'batch_id'),
        Index('idx_action_type_status', 'action_type', 'action_status'),
        Index('idx_performed_at', 'performed_at'),
    )
    
    def __repr__(self):
        return f"<Audit {self.action_type} {self.action_status} by user_id={self.performed_by}>"
