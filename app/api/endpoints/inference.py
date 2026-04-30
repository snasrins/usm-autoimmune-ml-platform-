"""
ML Inference API Endpoints
FastAPI routes for making predictions with trained models
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.api.deps import get_current_active_user, require_researcher_or_admin
from app.models.user import User
from app.schemas.training import (
    PredictionRequest, PredictionResponse,
    BatchPredictionRequest, BatchPredictionResponse,
    ModelInfoResponse, AvailableModelsResponse
)
from app.services.ml_inference_service import MLInferenceService
from app.services.minio_service import get_minio_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict_single_patient(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Make prediction for a single patient using a trained model
    
    Example request:
    ```json
    {
        "model_name": "xgboost",
        "version": "v1",
        "patient_data": {
            "demographics_age": 34,
            "demographics_gender": "Female",
            "lab_results_ANA": 1.5,
            "lab_results_Anti_dsDNA": 0.8,
            ...
        },
        "return_probability": true
    }
    ```
    """
    try:
        inference_service = MLInferenceService(db)
        
        result = inference_service.predict_single(
            model_name=request.model_name,
            version=request.version,
            patient_data=request.patient_data,
            return_probability=request.return_probability
        )
        
        return PredictionResponse(**result)
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model not found: {request.model_name}/{request.version}"
        )
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch_patients(
    request: BatchPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_researcher_or_admin)
):
    """
    Make predictions for multiple patients (batch processing)
    
    Example request:
    ```json
    {
        "model_name": "ensemble",
        "version": "v1",
        "patients_data": [
            {"demographics_age": 34, "lab_results_ANA": 1.5, ...},
            {"demographics_age": 45, "lab_results_ANA": 2.1, ...}
        ]
    }
    ```
    """
    try:
        inference_service = MLInferenceService(db)
        
        results = inference_service.predict_batch(
            model_name=request.model_name,
            version=request.version,
            patient_data_list=request.patients_data
        )
        
        predictions = [PredictionResponse(**r) for r in results]
        
        # ========================================
        # SAVE BATCH PREDICTIONS TO MINIO
        # ========================================
        try:
            import pandas as pd
            from datetime import datetime
            import uuid
            
            # Convert predictions to DataFrame
            predictions_data = []
            for i, pred in enumerate(predictions):
                pred_dict = pred.dict()
                pred_dict['patient_index'] = i
                predictions_data.append(pred_dict)
            
            df = pd.DataFrame(predictions_data)
            
            # Convert to CSV
            csv_buffer = df.to_csv(index=False)
            csv_bytes = csv_buffer.encode('utf-8')
            
            # Save to MinIO
            minio_service = get_minio_service()
            batch_id = str(uuid.uuid4())
            minio_path = minio_service.save_prediction_results(
                predictions_csv=csv_bytes,
                batch_id=batch_id,
                model_name=request.model_name,
                metadata={
                    'model_version': request.version,
                    'total_predictions': len(predictions),
                    'predicted_at': datetime.now().isoformat(),
                    'predicted_by': current_user.username
                }
            )
            
            logger.info(f"✓ Batch predictions saved to MinIO: {minio_path}")
            
            return BatchPredictionResponse(
                predictions=predictions,
                total_processed=len(request.patients_data),
                success_count=len(predictions),
                failure_count=len(request.patients_data) - len(predictions),
                minio_path=minio_path  # Add MinIO path to response
            )
        
        except Exception as minio_error:
            logger.warning(f"⚠️  Failed to save predictions to MinIO: {minio_error}")
            # Return predictions anyway
            return BatchPredictionResponse(
                predictions=predictions,
                total_processed=len(request.patients_data),
                success_count=len(predictions),
                failure_count=len(request.patients_data) - len(predictions)
            )
    
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}"
        )


@router.post("/predict/ensemble", response_model=PredictionResponse)
async def predict_with_ensemble(
    patient_data: dict,
    version: str = "v1",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Make prediction using the stacking ensemble (most accurate model)
    
    This is a convenience endpoint that uses the ensemble model by default.
    """
    try:
        inference_service = MLInferenceService(db)
        
        result = inference_service.predict_ensemble(
            patient_data=patient_data,
            ensemble_version=version
        )
        
        return PredictionResponse(**result)
    
    except Exception as e:
        logger.error(f"Ensemble prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ensemble prediction failed: {str(e)}"
        )


@router.get("/models/{model_name}/info", response_model=ModelInfoResponse)
async def get_model_info(
    model_name: str,
    version: str = "v1",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get information about a specific model version
    
    Returns:
    - Model metadata (training date, features, hyperparameters)
    - Available versions
    - Performance metrics
    """
    try:
        inference_service = MLInferenceService(db)
        
        info = inference_service.get_model_info(model_name, version)
        
        return ModelInfoResponse(**info)
    
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model not found: {model_name}/{version}"
        )


@router.get("/models/available", response_model=AvailableModelsResponse)
async def list_available_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all available trained models across all versions
    
    Returns summary of:
    - Model name and version
    - Training date
    - Performance metrics (AUC, F1, etc.)
    - Number of features
    """
    try:
        inference_service = MLInferenceService(db)
        
        models = inference_service.list_available_models()
        
        return AvailableModelsResponse(
            models=models,
            total_count=len(models)
        )
    
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )


@router.get("/models/{model_name}/versions")
async def list_model_versions(
    model_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all available versions of a specific model
    """
    try:
        from app.services.minio_service import get_minio_service
        minio = get_minio_service()
        
        versions = minio.list_model_versions(model_name)
        
        return {
            "model_name": model_name,
            "versions": versions,
            "total_versions": len(versions)
        }
    
    except Exception as e:
        logger.error(f"Error listing model versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list versions: {str(e)}"
        )


@router.get("/predictions/history")
async def list_prediction_history(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all batch predictions from MinIO
    
    Returns:
    - Prediction batch ID
    - Model name and version
    - Timestamp
    - Number of predictions
    - MinIO path for download
    """
    try:
        from app.services.minio_service import get_minio_service
        import json
        from datetime import datetime
        
        minio = get_minio_service()
        bucket_name = "predictions"
        
        # Check if predictions bucket exists
        if not minio.client.bucket_exists(bucket_name):
            return {
                "predictions": [],
                "total_count": 0
            }
        
        # List all objects in predictions bucket
        objects = minio.client.list_objects(bucket_name, recursive=True)
        
        predictions_list = []
        for obj in objects:
            # Skip metadata files, only process CSV files
            if not obj.object_name.endswith('.csv'):
                continue
                
            # Extract batch_id and model_name from path
            # Format: batch_{batch_id}/predictions_{model_name}_{timestamp}.csv
            parts = obj.object_name.split('/')
            if len(parts) >= 2:
                batch_id = parts[0].replace('batch_', '')
                filename = parts[1]
                
                # Try to get metadata
                metadata_path = obj.object_name.replace('.csv', '_metadata.json')
                metadata = {}
                try:
                    metadata_obj = minio.client.get_object(bucket_name, metadata_path)
                    metadata = json.loads(metadata_obj.read().decode('utf-8'))
                except:
                    pass  # Metadata file doesn't exist or failed to read
                
                predictions_list.append({
                    "batch_id": batch_id,
                    "filename": filename,
                    "model_name": metadata.get('model_name', 'unknown'),
                    "model_version": metadata.get('model_version', 'unknown'),
                    "total_predictions": metadata.get('total_predictions', 0),
                    "predicted_at": metadata.get('predicted_at', obj.last_modified.isoformat()),
                    "predicted_by": metadata.get('predicted_by', 'unknown'),
                    "minio_path": obj.object_name,
                    "size_bytes": obj.size,
                    "last_modified": obj.last_modified.isoformat()
                })
        
        # Sort by predicted_at descending
        predictions_list.sort(key=lambda x: x.get('predicted_at', ''), reverse=True)
        
        # Apply limit
        predictions_list = predictions_list[:limit]
        
        return {
            "predictions": predictions_list,
            "total_count": len(predictions_list)
        }
    
    except Exception as e:
        logger.error(f"Error listing prediction history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list predictions: {str(e)}"
        )


@router.get("/predictions/{batch_id}/download")
async def download_prediction_results(
    batch_id: str,
    minio_path: str = Query(..., description="MinIO object path"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Download prediction results CSV from MinIO
    """
    try:
        from app.services.minio_service import get_minio_service
        from fastapi.responses import StreamingResponse
        import io
        
        minio = get_minio_service()
        bucket_name = "predictions"
        
        # Get object from MinIO
        response = minio.client.get_object(bucket_name, minio_path)
        
        # Read content
        content = response.read()
        
        # Return as downloadable file
        return StreamingResponse(
            io.BytesIO(content),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=predictions_{batch_id}.csv"
            }
        )
    
    except Exception as e:
        logger.error(f"Error downloading predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction file not found: {str(e)}"
        )

