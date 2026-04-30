"""
Scorecard & Model Comparison API Endpoints
USMA-47: Clinical Scorecard System
USMA-43: Model Comparison Dashboard
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging

from app.core.database import get_db
from app.api.deps import get_current_active_user, require_researcher_or_admin
from app.models.user import User
from app.services.scorecard_service import ClinicalScorecardService
from app.services.minio_service import get_minio_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# Pydantic Schemas
# ============================================

class ScorecardRequest(BaseModel):
    """Request for clinical scorecard generation"""
    model_name: str = Field(..., description="Model name")
    version: str = Field(default="v1", description="Model version")
    patient_data: Dict[str, Any] = Field(..., description="Patient features")
    include_feature_scores: bool = Field(default=True, description="Include feature-level scores")


class ScorecardResponse(BaseModel):
    """Clinical scorecard response"""
    model_name: str
    version: str
    predicted_class: str
    confidence: float
    risk_score: float
    risk_group: str
    risk_level: int
    risk_description: str
    clinical_recommendation: str
    probability_distribution: Dict[str, float]
    feature_scores: Optional[List[Dict]] = None
    top_contributing_features: Optional[List[Dict]] = None


class ModelComparisonRequest(BaseModel):
    """Request for model comparison"""
    model_names: List[str] = Field(..., description="List of model names to compare")
    version: str = Field(default="v1", description="Model version")
    metric: str = Field(default="test_auc", description="Metric to compare (test_auc, test_f1, etc.)")


class ModelComparisonResponse(BaseModel):
    """Model comparison results"""
    models: List[Dict[str, Any]]
    best_model: str
    comparison_metric: str
    ranking: List[str]


# ============================================
# Scorecard Endpoints (USMA-47)
# ============================================

@router.post("/scorecard", response_model=ScorecardResponse)
async def generate_clinical_scorecard(
    request: ScorecardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate clinical risk scorecard for a patient
    
    Converts ML prediction to transparent clinical risk score (0-100)
    with risk groups and clinical recommendations
    
    Example request:
    ```json
    {
        "model_name": "xgboost",
        "version": "v1",
        "patient_data": {
            "demographics_age": 35,
            "lab_results_ESR": 45,
            "disease_activity_SLEDAI_score": 8
        },
        "include_feature_scores": true
    }
    ```
    
    Response includes:
    - Risk Score (0-100)
    - Risk Group (Low/Moderate/High/Very High)
    - Clinical Recommendations
    - Feature contributions
    """
    try:
        scorecard_service = ClinicalScorecardService(db)
        
        result = scorecard_service.generate_scorecard(
            model_name=request.model_name,
            version=request.version,
            patient_data=request.patient_data,
            include_feature_scores=request.include_feature_scores
        )
        
        return ScorecardResponse(**result)
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model not found: {request.model_name}/{request.version}"
        )
    except Exception as e:
        logger.error(f"Scorecard generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate scorecard: {str(e)}"
        )


@router.post("/scorecard/batch")
async def generate_batch_scorecards(
    model_name: str,
    version: str,
    patients_data: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_researcher_or_admin)
):
    """
    Generate scorecards for multiple patients (batch processing)
    
    Useful for risk stratification of patient cohorts
    """
    try:
        scorecard_service = ClinicalScorecardService(db)
        
        scorecards = []
        for patient_data in patients_data:
            scorecard = scorecard_service.generate_scorecard(
                model_name=model_name,
                version=version,
                patient_data=patient_data,
                include_feature_scores=False  # Skip for batch to save time
            )
            scorecards.append(scorecard)
        
        # Calculate summary statistics
        risk_groups = {}
        for sc in scorecards:
            group = sc['risk_group']
            risk_groups[group] = risk_groups.get(group, 0) + 1
        
        # ========================================
        # SAVE SCORECARD BATCH TO MINIO
        # ========================================
        try:
            import pandas as pd
            from datetime import datetime
            import json
            
            # Convert scorecards to DataFrame
            df = pd.DataFrame(scorecards)
            
            # Generate CSV files
            artifacts = {}
            
            # 1. Main scorecard results
            csv_buffer = df.to_csv(index=False)
            artifacts['batch_scorecards.csv'] = csv_buffer.encode('utf-8')
            
            # 2. Risk group summary
            summary_df = pd.DataFrame({
                'risk_group': list(risk_groups.keys()),
                'count': list(risk_groups.values()),
                'percentage': [count/len(scorecards)*100 for count in risk_groups.values()]
            })
            artifacts['risk_group_summary.csv'] = summary_df.to_csv(index=False).encode('utf-8')
            
            # 3. Comprehensive JSON report
            comprehensive_report = {
                'model_name': model_name,
                'model_version': version,
                'total_patients': len(scorecards),
                'risk_group_distribution': risk_groups,
                'generated_at': datetime.now().isoformat(),
                'generated_by': current_user.username,
                'scorecards': scorecards
            }
            artifacts['comprehensive_report.json'] = json.dumps(comprehensive_report, indent=2).encode('utf-8')
            
            # Save to MinIO
            minio_service = get_minio_service()
            scorecard_id = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            minio_paths = minio_service.save_scorecard_artifacts(
                scorecard_id=scorecard_id,
                artifacts=artifacts,
                metadata={
                    'model_name': model_name,
                    'model_version': version,
                    'total_patients': len(scorecards),
                    'risk_groups': risk_groups,
                    'generated_at': datetime.now().isoformat(),
                    'generated_by': current_user.username
                }
            )
            
            logger.info(f"✓ Saved {len(artifacts)} scorecard artifacts to MinIO")
            
            return {
                'scorecards': scorecards,
                'total_processed': len(scorecards),
                'risk_group_distribution': risk_groups,
                'minio_paths': minio_paths
            }
        
        except Exception as minio_error:
            logger.warning(f"⚠️  Failed to save scorecards to MinIO: {minio_error}")
            # Return results anyway
            return {
                'scorecards': scorecards,
                'total_processed': len(scorecards),
                'risk_group_distribution': risk_groups
            }
    
    except Exception as e:
        logger.error(f"Batch scorecard generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch scorecard generation failed: {str(e)}"
        )


# ============================================
# Model Comparison Endpoints (USMA-43)
# ============================================

@router.post("/compare", response_model=ModelComparisonResponse)
async def compare_models(
    request: ModelComparisonRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Compare multiple trained models side-by-side
    
    Helps clinicians select the best model for their use case
    
    Example request:
    ```json
    {
        "model_names": ["xgboost", "lightgbm", "random_forest", "ensemble"],
        "version": "v1",
        "metric": "test_auc"
    }
    ```
    
    Returns ranked list with all metrics for comparison
    """
    try:
        minio = get_minio_service()
        
        models_data = []
        
        for model_name in request.model_names:
            try:
                # Load model metadata
                metadata = minio.load_metadata(model_name, request.version)
                
                # Extract relevant metrics
                model_info = {
                    'model_name': model_name,
                    'version': request.version,
                    'test_auc': metadata.get('test_auc', 0.0),
                    'test_precision': metadata.get('test_precision', 0.0),
                    'test_recall': metadata.get('test_recall', 0.0),
                    'test_f1': metadata.get('test_f1', 0.0),
                    'test_brier_score': metadata.get('test_brier_score', 1.0),
                    'cv_auc': metadata.get('cv_auc', 0.0),
                    'training_time_seconds': metadata.get('training_time_seconds', 0.0),
                    'n_features': len(metadata.get('feature_names', [])),
                    'n_folds': metadata.get('n_folds', 5)
                }
                
                models_data.append(model_info)
            
            except FileNotFoundError:
                logger.warning(f"Model not found: {model_name}/{request.version}")
                continue
        
        if not models_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No models found for comparison"
            )
        
        # Sort by requested metric (descending for most metrics, ascending for brier)
        reverse = request.metric != 'test_brier_score'
        models_data.sort(key=lambda x: x.get(request.metric, 0.0), reverse=reverse)
        
        # Identify best model
        best_model = models_data[0]['model_name']
        ranking = [m['model_name'] for m in models_data]
        
        return ModelComparisonResponse(
            models=models_data,
            best_model=best_model,
            comparison_metric=request.metric,
            ranking=ranking
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model comparison error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model comparison failed: {str(e)}"
        )


@router.get("/compare/detailed/{model_name}")
async def get_detailed_model_metrics(
    model_name: str,
    version: str = "v1",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed metrics and information for a specific model
    
    Includes:
    - All performance metrics
    - Hyperparameters
    - Feature names
    - Training configuration
    - Calibration info (if available)
    """
    try:
        minio = get_minio_service()
        metadata = minio.load_metadata(model_name, version)
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model not found: {model_name}/{version}"
            )
        
        # Build detailed response
        detailed_info = {
            'model_name': model_name,
            'version': version,
            'metrics': {
                'cross_validation': {
                    'cv_auc': metadata.get('cv_auc', 0.0),
                    'oof_auc': metadata.get('oof_auc', 0.0),
                },
                'test_set': {
                    'test_auc': metadata.get('test_auc', 0.0),
                    'test_precision': metadata.get('test_precision', 0.0),
                    'test_recall': metadata.get('test_recall', 0.0),
                    'test_f1': metadata.get('test_f1', 0.0),
                    'test_brier_score': metadata.get('test_brier_score', 0.0)
                }
            },
            'configuration': {
                'n_folds': metadata.get('n_folds', 5),
                'n_features': len(metadata.get('feature_names', [])),
                'feature_names': metadata.get('feature_names', []),
                'class_mapping': metadata.get('class_mapping', {}),
                'requires_scaling': metadata.get('requires_scaling', False),
                'training_time_seconds': metadata.get('training_time_seconds', 0.0)
            },
            'hyperparameters': metadata.get('best_params', {}),
            'calibration': {
                'method': metadata.get('calibration_method', None),
                'thresholds': metadata.get('calibrated_thresholds', None)
            }
        }
        
        return detailed_info
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving model details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve model details: {str(e)}"
        )


@router.get("/models/available")
async def list_available_models(
    version: str = "v1",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all available trained models in MinIO
    
    Returns list of models with basic information
    """
    try:
        minio = get_minio_service()
        
        # List all objects in ml-models bucket
        objects = minio.client.list_objects('ml-models', recursive=True)
        
        # Extract unique model names
        models = set()
        for obj in objects:
            # Object name format: model_name/version/...
            parts = obj.object_name.split('/')
            if len(parts) >= 2:
                models.add(parts[0])
        
        # Get basic info for each model
        models_info = []
        for model_name in sorted(models):
            try:
                metadata = minio.load_metadata(model_name, version)
                models_info.append({
                    'model_name': model_name,
                    'version': version,
                    'test_auc': metadata.get('test_auc', 0.0),
                    'cv_auc': metadata.get('cv_auc', 0.0),
                    'available': True
                })
            except:
                models_info.append({
                    'model_name': model_name,
                    'version': version,
                    'available': False
                })
        
        return {
            'total_models': len(models_info),
            'models': models_info
        }
    
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )
