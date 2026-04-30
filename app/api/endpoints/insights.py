"""
ML Insights API Endpoints
AI-driven recommendations and system insights
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/insights")
async def get_ml_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get AI-driven insights and recommendations
    
    Returns:
        - System health status
        - Data quality warnings
        - Model performance insights
        - Next best actions
        - Training recommendations
    """
    try:
        from app.models.flexible_schema import FlexibleDatasetWide
        from app.core.ml_training import training_jobs
        
        insights = []
        warnings = []
        next_actions = []
        
        # Get user's datasets
        datasets = db.query(FlexibleDatasetWide).filter(
            FlexibleDatasetWide.uploaded_by == current_user.id
        ).all()
        
        total_datasets = len(datasets)
        ready_datasets = sum(1 for d in datasets if d.is_ready)
        
        # Check data quality
        if total_datasets > 0:
            avg_quality = sum(d.data_quality_score or 0 for d in datasets) / total_datasets
            
            if avg_quality < 60:
                warnings.append({
                    "severity": "critical",
                    "message": f"Average data quality is {avg_quality:.1f}%",
                    "recommendation": "Run data cleaning before training models"
                })
                next_actions.append({
                    "action": "Clean Data",
                    "route": "/data-preparation",
                    "priority": "high"
                })
            elif avg_quality < 80:
                warnings.append({
                    "severity": "warning",
                    "message": f"Data quality could be improved ({avg_quality:.1f}%)",
                    "recommendation": "Consider additional preprocessing"
                })
        
        # Check labeled data
        from app.models.flexible_schema import FlexibleLabeledData
        labeled_count = db.query(FlexibleLabeledData).filter(
            FlexibleLabeledData.uploaded_by == current_user.id
        ).count()
        
        if labeled_count == 0 and ready_datasets > 0:
            insights.append({
                "type": "info",
                "message": f"You have {ready_datasets} datasets ready for labeling",
                "recommendation": "Start labeling data to train ML models"
            })
            next_actions.append({
                "action": "Label Data",
                "route": "/labeling",
                "priority": "high"
            })
        elif labeled_count < 100:
            warnings.append({
                "severity": "warning",
                "message": f"Only {labeled_count} labeled records available",
                "recommendation": "Label at least 100 records for better model performance"
            })
        else:
            insights.append({
                "type": "success",
                "message": f"{labeled_count} records labeled and ready for training",
                "recommendation": None
            })
        
        # Check training jobs
        user_jobs = [job for job in training_jobs.values() if job.get('user_id') == current_user.id]
        recent_jobs = [job for job in user_jobs if job.get('created_at', datetime.min) > datetime.now() - timedelta(days=7)]
        
        completed_jobs = [job for job in recent_jobs if job.get('status') == 'completed']
        failed_jobs = [job for job in recent_jobs if job.get('status') == 'failed']
        
        if failed_jobs:
            warnings.append({
                "severity": "error", 
                "message": f"{len(failed_jobs)} training jobs failed in the last 7 days",
                "recommendation": "Check validation errors and data quality"
            })
        
        if completed_jobs:
            # Check model performance
            best_auc = max((job.get('result', {}).get('oof_auc', 0) for job in completed_jobs), default=0)
            
            if best_auc < 0.7:
                warnings.append({
                    "severity": "warning",
                    "message": f"Best model AUC is {best_auc:.3f}",
                    "recommendation": "Try feature engineering or hyperparameter tuning"
                })
                next_actions.append({
                    "action": "Feature Engineering",
                    "route": "/data-preparation",
                    "priority": "medium"
                })
            elif best_auc > 0.85:
                insights.append({
                    "type": "success",
                    "message": f"Excellent model performance! Best AUC: {best_auc:.3f}",
                    "recommendation": "Consider building ensemble models"
                })
                next_actions.append({
                    "action": "Train Ensemble",
                    "route": "/training",
                    "priority": "low"
                })
        
        # Recommend next actions if none exist
        if not next_actions:
            if total_datasets == 0:
                next_actions.append({
                    "action": "Upload Dataset",
                    "route": "/data-preparation",
                    "priority": "high"
                })
            elif labeled_count > 30:
                next_actions.append({
                    "action": "Train First Model",
                    "route": "/training",
                    "priority": "high"
                })
        
        # System health
        system_health = "healthy"
        if len([w for w in warnings if w.get('severity') == 'critical']) > 0:
            system_health = "critical"
        elif len([w for w in warnings if w.get('severity') in ['error', 'warning']]) > 0:
            system_health = "warning"
        
        return {
            "system_health": system_health,
            "insights": insights,
            "warnings": warnings,
            "next_actions": next_actions,
            "summary": {
                "total_datasets": total_datasets,
                "ready_datasets": ready_datasets,
                "labeled_records": labeled_count,
                "completed_trainings": len(completed_jobs),
                "failed_trainings": len(failed_jobs)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting ML insights: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get insights: {str(e)}"
        )


@router.get("/recommendations")
async def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get personalized recommendations for the user
    """
    try:
        recommendations = []
        
        # Check if user has uploaded data
        from app.models.flexible_schema import FlexibleDatasetWide
        dataset_count = db.query(FlexibleDatasetWide).filter(
            FlexibleDatasetWide.uploaded_by == current_user.id
        ).count()
        
        if dataset_count == 0:
            recommendations.append({
                "title": "Start by uploading your first dataset",
                "description": "Upload clinical data, lab results, or patient records to begin analysis",
                "action": "Upload Data",
                "route": "/data-preparation",
                "icon": "upload"
            })
        
        # Check labeling progress
        from app.models.flexible_schema import FlexibleLabeledData
        labeled_count = db.query(FlexibleLabeledData).filter(
            FlexibleLabeledData.uploaded_by == current_user.id
        ).count()
        
        if dataset_count > 0 and labeled_count < 30:
            recommendations.append({
                "title": "Label your data for supervised learning",
                "description": f"You have {labeled_count} labeled records. Aim for at least 100 for better models.",
                "action": "Go to Labeling",
                "route": "/labeling",
                "icon": "tag"
            })
        
        # Check training status
        from app.core.ml_training import training_jobs
        user_jobs = [job for job in training_jobs.values() if job.get('user_id') == current_user.id]
        
        if labeled_count >= 30 and not user_jobs:
            recommendations.append({
                "title": "Train your first ML model",
                "description": "You have enough labeled data to start training predictive models",
                "action": "Start Training",
                "route": "/training",
                "icon": "zap"
            })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return []
