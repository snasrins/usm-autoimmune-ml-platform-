"""
Database Models - Flexible Schema for Autoimmune Disease Registry
"""
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.revoked_token import RevokedToken

# Legacy normalized models (kept for optional normalization)
from app.models.patient import Patient
from app.models.diagnosis import Diagnosis
from app.models.lab_test import LabTestDefinition, LabResultFlexible, LabResultBatch
from app.models.disease_data import DiseaseSpecificData

# Upload tracking
from app.models.upload import UploadedFile, DataIngestionAudit
from app.models.dataset import Dataset, EDAReport

# ML Training Jobs (persistent storage)
from app.models.training_job import TrainingJob, JobType, JobStatus

# NEW: Flexible JSONB-based models (NO HARDCODED SCHEMA)
from app.models.flexible_data import (
    ImportPreviewStaging,
    FlexibleDatasetWide,
    UnstructuredDocumentProcessed,
    DatasetSchema,
    MLFeatureStore,
    ModelPrediction
)

# NEW: Dynamic Category Management (NO HARDCODING)
from app.models.disease_category import (
    DiseaseCategory,
    DiagnosisCategoryMapping,
    CategoryAuditLog
)

# Security & Compliance (Sprint 3 - Production Readiness)
from app.models.api_key import APIKey
from app.models.audit_log import AuditLog, DataAccessLog

__all__ = [
    # Core
    "User",
    "RefreshToken",
    "RevokedToken",
    
    # Security & Compliance
    "APIKey",
    "AuditLog",
    "DataAccessLog",
    
    # Legacy normalized (optional)
    "Patient",
    "Diagnosis",
    "LabTestDefinition",
    "LabResultFlexible",
    "LabResultBatch",
    "DiseaseSpecificData",
    
    # Upload tracking
    "UploadedFile",
    "DataIngestionAudit",
    "Dataset",
    "EDAReport",
    
    # ML Training Jobs
    "TrainingJob",
    "JobType",
    "JobStatus",
    
    # Flexible models (PRIMARY)
    "ImportPreviewStaging",
    "FlexibleDatasetWide",
    "UnstructuredDocumentProcessed",
    "DatasetSchema",
    "MLFeatureStore",
    "ModelPrediction",
    
    # Dynamic Category Management (NO HARDCODING)
    "DiseaseCategory",
    "DiagnosisCategoryMapping",
    "CategoryAuditLog",
]
