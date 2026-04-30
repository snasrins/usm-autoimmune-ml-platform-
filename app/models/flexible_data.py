"""
Flexible Data Models - 100% JSONB-based, No Hardcoded Schema
Supports any dataset structure without schema changes
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class ImportPreviewStaging(Base):
    """
    Temporary staging for CSV preview & editing
    Stores ANY CSV structure as JSONB
    Auto-expires after 24 hours
    """
    __tablename__ = "import_preview_staging"
    
    staging_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Dataset metadata
    dataset_type = Column(String(50))  # 'SLE', 'Sjogren', 'Custom1', etc.
    dataset_name = Column(String(100))  # User-defined name
    
    # FLEXIBLE: Store entire CSV row as JSONB
    row_data = Column(JSONB, nullable=False)
    # Example:
    # {
    #   "patient_id": "M98929",
    #   "age": 34,
    #   "gender": "Male",
    #   "ANA": 1.2,
    #   "Anti-dsDNA": 5.3,
    #   ... ANY columns from CSV
    # }
    
    row_number = Column(Integer)  # Original CSV row number
    
    # User editing
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)  # Soft delete
    edit_history = Column(JSONB)  # Track what changed
    # Example:
    # [
    #   {"field": "age", "old_value": 34, "new_value": 35, "edited_at": "2026-04-06T10:30:00"},
    #   {"field": "ANA", "old_value": 1.2, "new_value": 1.5, "edited_at": "2026-04-06T10:31:00"}
    # ]
    
    # Validation
    validation_status = Column(String(20), default='pending')  # 'pending', 'valid', 'invalid'
    validation_errors = Column(JSONB)
    # Example:
    # {
    #   "age": "Must be between 0 and 120",
    #   "patient_id": "Duplicate ID found"
    # }
    
    # Auto-cleanup
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))  # Set to created_at + 24 hours
    
    # Indexes
    __table_args__ = (
        Index('idx_staging_session', 'session_id'),
        Index('idx_staging_deleted', 'is_deleted'),
        Index('idx_staging_expires', 'expires_at'),
    )


class FlexibleDatasetWide(Base):
    """
    UNIVERSAL flexible wide table - ONE table for ALL datasets
    No hardcoded columns - everything in JSONB
    Replace ALL disease-specific tables
    """
    __tablename__ = "flexible_dataset_wide"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Patient/Record identifier
    record_id = Column(String(100), nullable=False)  # Could be patient_id, sample_id, etc.
    
    # Dataset classification
    dataset_type = Column(String(50), nullable=False, index=True)  # 'SLE', 'Sjogren', 'RA', 'Custom1'
    dataset_name = Column(String(100))  # User-defined descriptive name
    dataset_version = Column(String(20))  # For dataset versioning
    
    # FLEXIBLE: ALL data as JSONB (NO HARDCODED COLUMNS!)
    data = Column(JSONB, nullable=False)
    # Example for SLE:
    # {
    #   "demographics": {
    #     "age": 34,
    #     "gender": "Male",
    #     "ethnicity": "Malay"
    #   },
    #   "lab_results": {
    #     "ANA": 1.2,
    #     "Anti-dsDNA": 5.3,
    #     "C3": 0.9,
    #     "C4": 0.7,
    #     "ESR": 45,
    #     "CRP": 8.2,
    #     "IL-6": 12.3,
    #     "IL-10": 80
    #   },
    #   "clinical": {
    #     "diagnosis_date": "2023-05-15",
    #     "disease_duration_years": 5,
    #     "SLEDAI_score": 12,
    #     "medications": ["Prednisone", "Hydroxychloroquine"]
    #   },
    #   "labels": {
    #     "disease_classification": "SLE",
    #     "severity": "Moderate",
    #     "meets_criteria": true
    #   }
    # }
    
    # Schema metadata (auto-detected from CSV)
    schema_definition = Column(JSONB)
    # Example:
    # {
    #   "columns": [
    #     {"name": "patient_id", "type": "string", "category": "identifier"},
    #     {"name": "age", "type": "integer", "category": "demographics"},
    #     {"name": "ANA", "type": "numeric", "category": "lab_results", "unit": "IU/mL"},
    #     ...
    #   ]
    # }
    
    # Import source tracking
    dataset_source = Column(String(100))  # "Hospital USM", "Manual Entry"
    import_batch_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    import_method = Column(String(50))  # 'csv_upload', 'ocr_processed', 'api_import'
    
    # Normalization tracking (optional feature)
    is_normalized = Column(Boolean, default=False)
    normalized_at = Column(DateTime(timezone=True))
    normalized_by = Column(Integer, ForeignKey("users.id"))
    
    # Quality metrics
    data_quality_score = Column(Integer)  # 0-100
    missing_fields_count = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_flexible_record', 'record_id'),
        Index('idx_flexible_dataset_type', 'dataset_type'),
        Index('idx_flexible_batch', 'import_batch_id'),
        Index('idx_flexible_normalized', 'is_normalized'),
        Index('idx_flexible_created', 'created_at'),
        # GIN index on JSONB for fast queries
        Index('idx_flexible_data', 'data', postgresql_using='gin'),
        Index('idx_flexible_schema', 'schema_definition', postgresql_using='gin'),
        # Unique constraint on record_id + dataset_type (prevent duplicates within dataset)
        Index('idx_unique_record_dataset', 'record_id', 'dataset_type', unique=True),
    )


class UnstructuredDocumentProcessed(Base):
    """
    OCR/NER results from unstructured documents
    Stores extracted data in flexible JSONB format
    """
    __tablename__ = "unstructured_document_processed"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Link to original document
    document_id = Column(Integer, index=True)  # References unstructured_documents
    document_filename = Column(String(255))
    
    # Extracted record identifier (if found)
    extracted_record_id = Column(String(100))
    
    # FLEXIBLE: OCR extracted data as JSONB
    extracted_data = Column(JSONB, nullable=False)
    # Example:
    # {
    #   "demographics": {"age": 45, "gender": "Female"},
    #   "diagnoses": ["SLE", "Lupus Nephritis"],
    #   "symptoms": ["fatigue", "joint pain", "malar rash"],
    #   "lab_results": {"ANA": "1:320 (Positive)", "Anti-dsDNA": "High"},
    #   "medications": ["Prednisone 20mg daily", "Hydroxychloroquine 200mg"],
    #   "visit_date": "2024-01-15"
    # }
    
    # Confidence scores per field
    confidence_scores = Column(JSONB)
    # Example:
    # {
    #   "demographics.age": 0.95,
    #   "diagnoses": 0.88,
    #   "lab_results.ANA": 0.72
    # }
    
    # Processing metadata
    ocr_engine = Column(String(50))  # 'tesseract', 'paddleocr', 'aws_textract'
    ner_model = Column(String(50))  # 'spacy_medical', 'bioBERT'
    processing_version = Column(String(20))
    
    # User verification
    is_verified = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey("users.id"))
    verification_date = Column(DateTime(timezone=True))
    verification_notes = Column(Text)
    
    # Dataset classification
    dataset_type = Column(String(50))  # Classified as 'SLE', 'Sjogren', etc.
    classification_confidence = Column(Integer)  # 0-100
    
    # Normalization tracking
    is_normalized = Column(Boolean, default=False)
    is_saved_to_wide_table = Column(Boolean, default=False)
    saved_wide_table_id = Column(Integer)  # FK to flexible_dataset_wide
    
    # Import tracking
    import_batch_id = Column(UUID(as_uuid=True), default=uuid.uuid4, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_unstructured_proc_batch', 'import_batch_id'),
        Index('idx_unstructured_proc_verified', 'is_verified'),
        Index('idx_unstructured_proc_saved', 'is_saved_to_wide_table'),
        Index('idx_unstructured_proc_data', 'extracted_data', postgresql_using='gin'),
    )


class DatasetSchema(Base):
    """
    Registry of dataset schemas (dynamically created)
    Tracks what columns/fields exist in each dataset type
    """
    __tablename__ = "dataset_schemas"
    
    schema_id = Column(Integer, primary_key=True, index=True)
    
    # Dataset identification
    dataset_type = Column(String(50), nullable=False, unique=True, index=True)
    dataset_name = Column(String(100))
    dataset_description = Column(Text)
    
    # Schema definition (auto-detected from first import)
    schema_definition = Column(JSONB, nullable=False)
    # Example:
    # {
    #   "version": "1.0",
    #   "columns": [
    #     {
    #       "name": "patient_id",
    #       "type": "string",
    #       "category": "identifier",
    #       "required": true,
    #       "unique": true
    #     },
    #     {
    #       "name": "age",
    #       "type": "integer",
    #       "category": "demographics",
    #       "required": true,
    #       "min": 0,
    #       "max": 120
    #     },
    #     {
    #       "name": "ANA",
    #       "type": "numeric",
    #       "category": "lab_results",
    #       "unit": "IU/mL",
    #       "reference_range": {"min": 0, "max": 1.0}
    #     }
    #   ],
    #   "categories": {
    #     "demographics": ["age", "gender", "ethnicity"],
    #     "lab_results": ["ANA", "Anti-dsDNA", "C3", "C4"],
    #     "clinical": ["diagnosis_date", "medications"]
    #   }
    # }
    
    # Example data (for reference)
    example_record = Column(JSONB)
    
    # Statistics
    record_count = Column(Integer, default=0)
    last_import_date = Column(DateTime(timezone=True))
    
    # Version control
    schema_version = Column(String(20), default='1.0')
    parent_schema_id = Column(Integer, ForeignKey('dataset_schemas.schema_id'))  # For schema evolution
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    is_active = Column(Boolean, default=True)


class MLFeatureStore(Base):
    """
    Versioned feature store for ML training
    Stores preprocessed features with full lineage tracking
    """
    __tablename__ = "ml_feature_store"
    
    feature_id = Column(Integer, primary_key=True, index=True)
    
    # Source record link
    source_table = Column(String(100))  # 'flexible_dataset_wide'
    source_record_id = Column(Integer)  # FK to source table
    patient_id = Column(String(100))  # Original patient/record ID
    
    # Dataset classification
    dataset_type = Column(String(50), nullable=False, index=True)
    
    # FLEXIBLE: Raw features (before preprocessing)
    raw_features = Column(JSONB)
    
    # FLEXIBLE: Engineered features (after preprocessing pipeline)
    processed_features = Column(JSONB, nullable=False)
    # Example:
    # {
    #   "age_normalized": 0.45,
    #   "gender_encoded": 1,
    #   "ana_log": 2.31,
    #   "cytokine_ratio_il6_il10": 1.83,
    #   "complement_product_c3_c4": 0.56,
    #   "has_high_esr": 1
    # }
    
    # Feature metadata
    feature_names = Column(JSONB)  # Ordered list: ["age_normalized", "gender_encoded", ...]
    feature_vector = Column(JSONB)  # Numeric array: [0.45, 1, 2.31, 1.83, ...]
    
    # Labels (for supervised learning)
    label_name = Column(String(100))  # 'disease_classification', 'severity', etc.
    label_value = Column(String(100))  # 'SLE', 'Moderate', etc.
    label_encoded = Column(Integer)  # Numeric: 1, 0, etc.
    
    # Versioning (CRITICAL for ML reproducibility)
    feature_version = Column(String(20), nullable=False, index=True)  # 'v1.0', 'v1.1'
    preprocessing_pipeline = Column(JSONB)  # Pipeline configuration
    # Example:
    # {
    #   "steps": [
    #     {"name": "missing_values", "strategy": "median"},
    #     {"name": "scaling", "method": "StandardScaler"},
    #     {"name": "encoding", "categorical": "OneHot"}
    #   ]
    # }
    
    feature_selection_method = Column(String(100))
    
    # Train/Test split
    dataset_split = Column(String(20), index=True)  # 'train', 'validation', 'test'
    split_strategy = Column(String(50))  # 'stratified_80_20', 'time_series'
    split_seed = Column(Integer)  # Random seed for reproducibility
    
    # Quality metrics
    data_quality_score = Column(Integer)
    missing_feature_count = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_ml_patient', 'patient_id'),
        Index('idx_ml_dataset', 'dataset_type', 'dataset_split'),
        Index('idx_ml_version', 'feature_version'),
        Index('idx_ml_label', 'label_value'),
        Index('idx_ml_split', 'dataset_split'),
        Index('idx_ml_features', 'processed_features', postgresql_using='gin'),
    )


class ModelPrediction(Base):
    """
    Store model predictions and probabilities
    Supports model versioning and ensemble predictions
    """
    __tablename__ = "model_predictions"
    
    prediction_id = Column(Integer, primary_key=True, index=True)
    
    # Record identification
    record_id = Column(String(100), nullable=False)
    dataset_type = Column(String(50), index=True)
    
    # Model information
    model_name = Column(String(100), nullable=False, index=True)
    model_version = Column(String(20), nullable=False)
    model_type = Column(String(50))  # 'RandomForest', 'XGBoost', 'StackedEnsemble'
    
    # For ensemble models
    base_models = Column(JSONB)  # ['RF_v1', 'XGB_v2', 'SVM_v1']
    base_model_predictions = Column(JSONB)  # Individual predictions from base models
    
    # Predictions
    predicted_class = Column(String(50), nullable=False)
    probability_score = Column(Integer, nullable=False)  # 0-100 (percentage)
    
    # All class probabilities
    all_class_probabilities = Column(JSONB)
    # Example:
    # {
    #   "SLE": 85.23,
    #   "Sjogren": 9.81,
    #   "RA": 3.42,
    #   "Normal": 1.54
    # }
    
    # Input features snapshot
    input_features = Column(JSONB)
    feature_version = Column(String(20))  # Links to ml_feature_store
    
    # Explainability
    feature_importance = Column(JSONB)  # SHAP values or feature importances
    prediction_explanation = Column(Text)
    
    # Confidence level
    prediction_confidence = Column(String(20))  # 'High' (>80%), 'Medium' (60-80%), 'Low' (<60%)
    
    # Ground truth (if available)
    actual_class = Column(String(50))
    is_correct = Column(Boolean)
    
    # Performance metrics
    inference_time_ms = Column(Integer)
    
    # User feedback
    feedback_score = Column(Integer)  # 1-5
    feedback_notes = Column(Text)
    corrected_by = Column(Integer, ForeignKey("users.id"))
    
    # Timestamps
    prediction_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    predicted_by = Column(Integer, ForeignKey("users.id"))  # User or system ID
    
    # Indexes
    __table_args__ = (
        Index('idx_pred_record', 'record_id'),
        Index('idx_pred_model', 'model_name', 'model_version'),
        Index('idx_pred_class', 'predicted_class'),
        Index('idx_pred_timestamp', 'prediction_timestamp'),
    )
