"""
Dataset Model - Track uploaded datasets for EDA and ML
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Dataset(Base):
    """Uploaded dataset for analysis"""
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # File information
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size_bytes = Column(Integer)
    file_hash = Column(String(64), index=True)  # SHA-256
    
    # Dataset shape
    row_count = Column(Integer)
    column_count = Column(Integer)
    
    # Column information
    columns = Column(JSONB)  # List of column names with data types
    # Example: [{"name": "age", "dtype": "int64", "nullable": true}, ...]
    
    # Dataset statistics (cached for performance)
    dataset_stats = Column(JSONB)
    # Example: {"numeric_cols": 5, "categorical_cols": 3, "missing_values": 120, ...}
    
    # Data quality metrics
    missing_percentage = Column(Float)
    duplicate_rows = Column(Integer)
    
    # Preprocessing status
    preprocessing_status = Column(String(20), default='raw')  # raw, preprocessed, ready
    preprocessing_config = Column(JSONB)  # Store preprocessing steps applied
    
    # Processing errors
    validation_errors = Column(JSONB)
    
    # Upload tracking
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    last_modified = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Status
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_dataset_user', 'uploaded_by'),
        Index('idx_dataset_status', 'preprocessing_status'),
        Index('idx_dataset_active', 'is_active', 'is_deleted'),
    )
    
    def __repr__(self):
        return f"<Dataset {self.name} ({self.row_count}x{self.column_count})>"


class EDAReport(Base):
    """Store EDA analysis results"""
    __tablename__ = "eda_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    
    # Report metadata
    report_type = Column(String(50), nullable=False)  # summary, univariate, bivariate, outliers
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    generated_by = Column(Integer, ForeignKey("users.id"))
    
    # Analysis results
    analysis_results = Column(JSONB, nullable=False)
    # Structure depends on report_type:
    # - summary: {"total_rows": 100, "total_cols": 10, "missing_cells": 5, ...}
    # - univariate: {"column_name": "age", "mean": 45.2, "std": 12.3, ...}
    # - bivariate: {"correlation_matrix": [[...]], "top_correlations": [...]}
    # - outliers: {"outlier_count": 15, "outlier_rows": [1, 5, 10], ...}
    
    # Visualization data (for charts)
    visualizations = Column(JSONB)
    # Example: {"histogram": {"bins": [...], "counts": [...]}, "boxplot": {...}}
    
    # Status
    is_active = Column(Boolean, default=True)
    
    __table_args__ = (
        Index('idx_eda_dataset', 'dataset_id'),
        Index('idx_eda_type', 'report_type'),
    )
    
    def __repr__(self):
        return f"<EDAReport {self.report_type} for Dataset#{self.dataset_id}>"
