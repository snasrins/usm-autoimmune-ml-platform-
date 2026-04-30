"""
Training Job Model
Persistent storage for ML training jobs to survive restarts
"""
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class JobType(str, enum.Enum):
    """Training job types"""
    DATASET_GENERATION = "dataset_generation"
    FEATURE_SELECTION = "feature_selection"
    BASE_MODEL = "base_model"
    ENSEMBLE = "ensemble"
    FULL_PIPELINE = "full_pipeline"


class JobStatus(str, enum.Enum):
    """Training job statuses"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TrainingJob(Base):
    """
    Persistent training job metadata
    
    This stores training job information in PostgreSQL so jobs survive backend restarts.
    Large artifacts (models, predictions) are stored in MinIO and referenced by path.
    """
    __tablename__ = "training_jobs"
    
    # Primary key
    job_id = Column(String(36), primary_key=True, index=True)  # UUID
    
    # Job metadata
    job_type = Column(SQLEnum(JobType), nullable=False, index=True)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)
    
    # User tracking
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user = relationship("User", backref="training_jobs")
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Job configuration (JSON)
    params = Column(JSON, nullable=False)  # Training parameters
    
    # Results (JSON - small results only, large artifacts in MinIO)
    result = Column(JSON, nullable=True)  # Metrics, params, etc.
    error = Column(Text, nullable=True)  # Error message if failed
    
    # MinIO artifact paths (JSON array of strings)
    artifact_paths = Column(JSON, nullable=True)  # Paths to models in MinIO
    oof_predictions_path = Column(String(500), nullable=True)  # Path to OOF predictions in MinIO
    
    # Training metadata
    model_name = Column(String(100), nullable=True, index=True)  # e.g., 'xgboost', 'ensemble'
    dataset_id = Column(String(36), nullable=True, index=True)  # Reference to dataset job
    
    # Performance metrics (denormalized for quick queries)
    oof_auc = Column(Float, nullable=True)
    test_auc = Column(Float, nullable=True)
    test_f1 = Column(Float, nullable=True)
    training_time_seconds = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<TrainingJob {self.job_id} - {self.job_type} - {self.status}>"
