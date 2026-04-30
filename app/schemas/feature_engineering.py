"""
Feature Engineering Schemas
Request/Response models for feature engineering API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class FeatureEngineeringRequest(BaseModel):
    """Request to apply feature engineering to dataset"""
    import_batch_id: str = Field(..., description="Batch ID to engineer features for")
    target_column: str = Field(default="labels_disease_classification", description="Target column to preserve")
    
    # Ratio features
    enable_ratios: bool = Field(default=True, description="Enable biomarker ratio features")
    crp_esr_ratio: bool = Field(default=True, description="CRP/ESR inflammatory ratio")
    nlr_ratio: bool = Field(default=True, description="Neutrophil-Lymphocyte Ratio (NLR)")
    plr_ratio: bool = Field(default=True, description="Platelet-Lymphocyte Ratio (PLR)")
    
    # Temporal features
    enable_temporal: bool = Field(default=True, description="Enable temporal features")
    disease_duration: bool = Field(default=True, description="Calculate disease duration from diagnosis date")
    
    # Derived features
    enable_derived: bool = Field(default=True, description="Enable derived features")
    inflammation_score: bool = Field(default=True, description="Combined inflammation index (mean of CRP, ESR)")
    organ_involvement: bool = Field(default=False, description="Count of affected organ systems")


class FeatureInfo(BaseModel):
    """Information about an engineered feature"""
    name: str
    type: str  # 'ratio', 'temporal', 'derived', 'categorical'
    description: str
    source_columns: List[str]


class FeatureEngineeringResponse(BaseModel):
    """Response from feature engineering"""
    success: bool
    message: str
    import_batch_id: str
    original_feature_count: int
    engineered_feature_count: int
    new_features: List[FeatureInfo]
    features_added: int
    skipped_features: Optional[List[Dict[str, str]]] = Field(default=[], description="Features that couldn't be created")
    available_columns: Optional[List[str]] = Field(default=[], description="Columns available in dataset")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FeatureEngineeringStatus(BaseModel):
    """Status of feature engineering for a dataset"""
    import_batch_id: str
    is_engineered: bool
    features_count: int
    engineered_features: List[str] = []
    timestamp: Optional[datetime] = None
