"""
Prediction Schemas - Pydantic models for ML predictions
"""
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime


class PredictionInput(BaseModel):
    """Input data for ML prediction"""
    patient_id: str
    features: Dict[str, float]
    model_type: str = "autoimmune_classifier"


class PredictionOutput(BaseModel):
    """ML Prediction result"""
    patient_id: str
    prediction: str
    confidence: float
    risk_score: float
    probabilities: Dict[str, float]
    model_version: str
    predicted_at: datetime
    gpu_used: bool
    inference_time_ms: float


class BatchPredictionRequest(BaseModel):
    """Batch prediction request"""
    predictions: List[PredictionInput]


class BatchPredictionResponse(BaseModel):
    """Batch prediction response"""
    results: List[PredictionOutput]
    total_processed: int
    total_time_ms: float
