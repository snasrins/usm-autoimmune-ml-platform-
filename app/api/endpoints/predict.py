"""
ML Prediction API Endpoints
GPU-Accelerated inference for autoimmune disease classification
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import time

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.patient import Patient
from app.schemas.prediction import (
    PredictionInput, 
    PredictionOutput, 
    BatchPredictionRequest, 
    BatchPredictionResponse
)
from app.ml.inference import get_inference_engine

router = APIRouter()


@router.post("/predict", response_model=PredictionOutput)
async def predict(
    prediction_input: PredictionInput,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Make a single ML prediction
    GPU-accelerated inference
    """
    # Get inference engine
    engine = get_inference_engine()
    
    # Perform prediction
    predicted_class, confidence, probabilities, inference_time = engine.predict(
        prediction_input.features
    )
    
    # Calculate risk score (0-100)
    risk_score = confidence * 100
    
    # Update patient record if exists
    patient = db.query(Patient).filter(
        Patient.patient_id == prediction_input.patient_id
    ).first()
    
    if patient:
        patient.risk_score = risk_score
        patient.prediction_data = {
            "prediction": predicted_class,
            "confidence": confidence,
            "probabilities": probabilities
        }
        patient.last_prediction_at = datetime.utcnow()
        db.commit()
    
    return PredictionOutput(
        patient_id=prediction_input.patient_id,
        prediction=predicted_class,
        confidence=confidence,
        risk_score=risk_score,
        probabilities=probabilities,
        model_version=engine.model_version,
        predicted_at=datetime.utcnow(),
        gpu_used=engine.device.type == "cuda",
        inference_time_ms=inference_time
    )


@router.post("/predict/batch", response_model=BatchPredictionResponse)
async def batch_predict(
    batch_request: BatchPredictionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Make batch predictions
    Processes multiple predictions efficiently on GPU
    """
    start_time = time.time()
    engine = get_inference_engine()
    
    results = []
    for pred_input in batch_request.predictions:
        predicted_class, confidence, probabilities, inference_time = engine.predict(
            pred_input.features
        )
        
        risk_score = confidence * 100
        
        results.append(
            PredictionOutput(
                patient_id=pred_input.patient_id,
                prediction=predicted_class,
                confidence=confidence,
                risk_score=risk_score,
                probabilities=probabilities,
                model_version=engine.model_version,
                predicted_at=datetime.utcnow(),
                gpu_used=engine.device.type == "cuda",
                inference_time_ms=inference_time
            )
        )
    
    total_time = (time.time() - start_time) * 1000
    
    return BatchPredictionResponse(
        results=results,
        total_processed=len(results),
        total_time_ms=total_time
    )


@router.get("/gpu-info")
async def get_gpu_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get GPU information and status
    """
    engine = get_inference_engine()
    gpu_info = engine.get_gpu_info()
    
    return {
        "gpu_info": gpu_info,
        "model_version": engine.model_version,
        "device": str(engine.device),
        "model_classes": engine.class_names
    }


@router.get("/model-info")
async def get_model_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get ML model information and metadata
    """
    engine = get_inference_engine()
    
    return {
        "model_version": engine.model_version,
        "model_type": "AutoimmuneClassifier",
        "classes": engine.class_names,
        "num_classes": len(engine.class_names),
        "device": str(engine.device),
        "framework": "PyTorch"
    }
