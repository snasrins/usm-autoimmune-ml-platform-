"""
ML Explainability & Conversational AI API Endpoints
USMA-50: SHAP explanations + Gemma-4-E4B smart interface
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.training_job import TrainingJob, JobStatus, JobType
from app.services.shap_explainer_service import SHAPExplainerService
from app.services.gemma_conversational_service import GemmaConversationalService

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# Pydantic Schemas
# ============================================

class SHAPExplanationRequest(BaseModel):
    """Request for SHAP explanation"""
    model_name: str = Field(..., description="Model name (e.g., 'xgboost', 'ensemble')")
    version: str = Field(default="v1", description="Model version")
    patient_data: Dict[str, Any] = Field(..., description="Patient features")
    top_k: int = Field(default=10, description="Number of top features to return")
    generate_plot: bool = Field(default=True, description="Generate waterfall plot")


class SHAPExplanationResponse(BaseModel):
    """Response with SHAP explanation"""
    model_name: str
    version: str
    predicted_class: Optional[str]
    base_value: float
    top_features: List[Dict[str, Any]]
    explanation_text: str
    waterfall_plot: Optional[str] = None  # Base64 encoded image


class ConversationMessage(BaseModel):
    """Single conversation message"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request for conversational AI"""
    message: str = Field(..., description="User's message/question")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context (prediction, SHAP, patient data)")
    conversation_history: Optional[List[ConversationMessage]] = Field(default=None, description="Previous conversation")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Sampling temperature")


class ChatResponse(BaseModel):
    """Response from conversational AI"""
    response: str
    model: str
    device: str
    tokens_generated: int


class PredictionExplanationRequest(BaseModel):
    """Request to explain a prediction in natural language"""
    prediction_result: Dict[str, Any] = Field(..., description="Prediction output from inference API")
    shap_explanation: Optional[Dict[str, Any]] = Field(default=None, description="Optional SHAP explanation")


class ClinicalQuestionRequest(BaseModel):
    """Request for clinical question answering"""
    question: str = Field(..., description="Clinical question about SLE")
    patient_context: Optional[Dict[str, Any]] = Field(default=None, description="Optional patient data for context")


# ============================================
# SHAP Explainability Endpoints
# ============================================

@router.post("/explain", response_model=SHAPExplanationResponse)
async def explain_prediction(
    request: SHAPExplanationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get SHAP explanation for a prediction
    
    Returns feature importance values showing which features most influenced
    the model's prediction for a specific patient.
    
    Example request:
    ```json
    {
        "model_name": "xgboost",
        "version": "v1",
        "patient_data": {
            "demographics_age": 35,
            "lab_results_ESR": 45,
            "disease_activity_SLEDAI_score": 8,
            ...
        },
        "top_k": 10,
        "generate_plot": true
    }
    ```
    """
    try:
        shap_service = SHAPExplainerService(db)
        
        result = shap_service.explain_prediction(
            model_name=request.model_name,
            version=request.version,
            patient_data=request.patient_data,
            top_k=request.top_k,
            generate_plot=request.generate_plot
        )
        
        return SHAPExplanationResponse(**result)
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model not found: {request.model_name}/{request.version}"
        )
    except Exception as e:
        logger.error(f"SHAP explanation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )


@router.post("/explain/ensemble", response_model=SHAPExplanationResponse)
async def explain_ensemble_prediction(
    patient_data: Dict[str, Any],
    version: str = "v1",
    top_k: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get SHAP explanation for ensemble model prediction
    
    Convenience endpoint that explains ensemble predictions.
    """
    try:
        shap_service = SHAPExplainerService(db)
        
        result = shap_service.explain_ensemble(
            patient_data=patient_data,
            ensemble_version=version,
            top_k=top_k
        )
        
        return SHAPExplanationResponse(**result)
    
    except Exception as e:
        logger.error(f"Ensemble explanation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explain ensemble: {str(e)}"
        )


class SHAPByJobRequest(BaseModel):
    """Request for SHAP explanation using a training job ID"""
    job_id: str = Field(..., description="Training job ID (model_id from models/list)")
    patient_data: Dict[str, Any] = Field(..., description="Patient features")
    top_k: int = Field(default=10, description="Number of top features to return")
    generate_plot: bool = Field(default=True, description="Generate waterfall plot")


@router.post("/explain/by-job", response_model=SHAPExplanationResponse)
async def explain_by_job_id(
    request: SHAPByJobRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get SHAP explanation for a trained model identified by its training job ID.

    Looks up the artifact path from the training job record, then runs SHAP.
    Use the `model_id` returned by GET /ml/models/list as the `job_id`.
    """
    try:
        # Load the training job from DB
        job = db.query(TrainingJob).filter(TrainingJob.job_id == request.job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Training job not found: {request.job_id}"
            )

        # Resolve the MinIO path: try artifact_paths (list) first, then result
        artifact_paths = job.artifact_paths or []
        if not artifact_paths:
            result_data = job.result or {}
            single_path = result_data.get("model_artifact_path", "")
            if single_path:
                artifact_paths = [single_path]

        if not artifact_paths:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No model artifacts found for job {request.job_id}. The model may not have been saved to MinIO."
            )

        # Parse model_name and version from path: "{model_name}/{version}/fold_N.pkl"
        first_path = artifact_paths[0]
        parts = first_path.split("/")
        if len(parts) < 2:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected artifact path format: {first_path}"
            )
        minio_model_name = parts[0]
        minio_version = parts[1]

        logger.info(f"SHAP by-job: job={request.job_id}, minio_model={minio_model_name}, version={minio_version}")

        shap_service = SHAPExplainerService(db)
        result = shap_service.explain_prediction(
            model_name=minio_model_name,
            version=minio_version,
            patient_data=request.patient_data,
            top_k=request.top_k,
            generate_plot=request.generate_plot
        )
        return SHAPExplanationResponse(**result)

    except HTTPException:
        raise
    except ValueError as e:
        # Friendly errors from _create_explainer (e.g. no artifacts in MinIO)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"SHAP by-job explanation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )


# ============================================
# Gemma-4-E4B Conversational AI Endpoints
# ============================================

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Chat with Gemma-4-E4B medical AI assistant
    
    Ask questions about SLE, get interpretations, or have conversational interactions.
    
    Example request:
    ```json
    {
        "message": "What does a SLEDAI score of 8 indicate?",
        "context": {
            "prediction": {
                "prediction": "Moderate",
                "confidence": 0.65
            }
        },
        "temperature": 0.7
    }
    ```
    """
    try:
        gemma_service = GemmaConversationalService(db)
        
        # Convert conversation history to dict format
        history = None
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]
        
        # ── Enrich context with live platform data from DB ──────────────
        enriched_context = dict(request.context or {})
        try:
            completed_jobs = (
                db.query(TrainingJob)
                .filter(
                    TrainingJob.status == JobStatus.COMPLETED,
                    TrainingJob.job_type.in_([JobType.BASE_MODEL, JobType.ENSEMBLE]),
                )
                .order_by(TrainingJob.completed_at.desc())
                .limit(20)
                .all()
            )
            models_summary = []
            for j in completed_jobs:
                models_summary.append({
                    "name": j.model_name or j.job_id[:8],
                    "type": j.job_type.value if j.job_type else "base_model",
                    "oof_auc": round(j.oof_auc, 4) if j.oof_auc else None,
                    "test_auc": round(j.test_auc, 4) if j.test_auc else None,
                    "test_f1": round(j.test_f1, 4) if j.test_f1 else None,
                    "trained_at": j.completed_at.isoformat() if j.completed_at else None,
                })
            if models_summary:
                enriched_context["platform_data"] = {
                    "trained_models": models_summary,
                    "total_models": len(models_summary),
                    "best_model": max(
                        models_summary,
                        key=lambda m: m.get("test_auc") or m.get("oof_auc") or 0,
                    ),
                }
        except Exception as ctx_err:
            logger.warning(f"Could not enrich chat context from DB: {ctx_err}")
        # ────────────────────────────────────────────────────────────────

        result = gemma_service.chat(
            user_message=request.message,
            context=enriched_context,
            conversation_history=history,
            temperature=request.temperature
        )
        
        return ChatResponse(**result)
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


@router.post("/explain-prediction-nl", response_model=ChatResponse)
async def explain_prediction_natural_language(
    request: PredictionExplanationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get natural language explanation of a prediction using Gemma-4-E4B
    
    Combines prediction results and SHAP values into a clinician-friendly explanation.
    
    Example request:
    ```json
    {
        "prediction_result": {
            "prediction": "Moderate",
            "confidence": 0.65,
            "probabilities": {"Mild": 0.25, "Moderate": 0.65, "Severe": 0.10}
        },
        "shap_explanation": {
            "top_features": [
                {"feature": "SLEDAI_score", "shap_value": 0.45, "feature_value": 8.0}
            ]
        }
    }
    ```
    """
    try:
        gemma_service = GemmaConversationalService(db)
        
        explanation = gemma_service.explain_prediction(
            prediction_result=request.prediction_result,
            shap_explanation=request.shap_explanation
        )
        
        return ChatResponse(
            response=explanation,
            model='gemma-4-E4B',
            device='auto',
            tokens_generated=0  # Not tracked for this endpoint
        )
    
    except Exception as e:
        logger.error(f"Prediction explanation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explain prediction: {str(e)}"
        )


@router.post("/ask-clinical", response_model=ChatResponse)
async def ask_clinical_question(
    request: ClinicalQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Ask clinical questions about SLE
    
    Get evidence-based answers about SLE manifestations, biomarkers, and disease activity.
    
    Example request:
    ```json
    {
        "question": "What is the significance of elevated Anti-dsDNA antibodies?",
        "patient_context": {
            "lab_results_Anti_dsDNA": 1.8,
            "disease_activity_SLEDAI_score": 10
        }
    }
    ```
    """
    try:
        gemma_service = GemmaConversationalService(db)
        
        answer = gemma_service.answer_clinical_question(
            question=request.question,
            patient_context=request.patient_context
        )
        
        return ChatResponse(
            response=answer,
            model='gemma-4-E4B',
            device='auto',
            tokens_generated=0
        )
    
    except Exception as e:
        logger.error(f"Clinical question error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}"
        )


@router.delete("/chat/clear-cache")
async def clear_explainer_cache(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Clear SHAP explainer cache
    
    Use this after model updates to ensure fresh explainers are created.
    """
    try:
        shap_service = SHAPExplainerService(db)
        shap_service.clear_cache()
        
        return {"message": "SHAP explainer cache cleared successfully"}
    
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )
