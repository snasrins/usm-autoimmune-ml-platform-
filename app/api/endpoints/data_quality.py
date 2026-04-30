"""
Data Quality API Endpoints
Platform-wide data quality metrics and monitoring
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
import logging

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary")
async def get_data_quality_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get platform-wide data quality summary
    
    Returns:
        - Total datasets count
        - Average data quality score
        - Missing values percentage
        - Class imbalance stats
        - Outliers detected
        - Data source breakdown
    """
    try:
        # Import models here to avoid circular imports
        from app.models.flexible_schema import FlexibleDatasetWide
        
        # Get all datasets for current user
        datasets = db.query(FlexibleDatasetWide).filter(
            FlexibleDatasetWide.uploaded_by == current_user.id
        ).all()
        
        total_datasets = len(datasets)
        
        if total_datasets == 0:
            return {
                "total_datasets": 0,
                "average_quality_score": 0,
                "missing_values_percentage": 0,
                "class_imbalance_ratio": None,
                "outliers_detected": 0,
                "data_sources": {},
                "datasets_by_status": {
                    "ready": 0,
                    "processing": 0,
                    "error": 0
                },
                "recommendations": [
                    "Upload your first dataset to begin data quality analysis"
                ]
            }
        
        # Calculate average quality score
        quality_scores = [d.data_quality_score for d in datasets if d.data_quality_score is not None]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Count missing values across all datasets
        total_missing = 0
        total_records = 0
        for dataset in datasets:
            if hasattr(dataset, 'data') and dataset.data:
                # Estimate missing values from data structure
                records = len(dataset.data.get('records', []))
                total_records += records
                # Placeholder: would need actual column analysis
                
        missing_percentage = 0  # Placeholder - would calculate from actual data
        
        # Get class distribution for labeled data
        from app.models.flexible_schema import FlexibleLabeledData
        labeled_records = db.query(FlexibleLabeledData).filter(
            FlexibleLabeledData.uploaded_by == current_user.id
        ).all()
        
        class_distribution = {}
        for record in labeled_records:
            if hasattr(record, 'labels') and record.labels:
                for label_type, label_value in record.labels.items():
                    if label_type not in class_distribution:
                        class_distribution[label_type] = {}
                    if label_value not in class_distribution[label_type]:
                        class_distribution[label_type][label_value] = 0
                    class_distribution[label_type][label_value] += 1
        
        # Calculate class imbalance ratio
        class_imbalance_ratio = None
        if class_distribution:
            # Get the most common label type
            for label_type, distribution in class_distribution.items():
                if len(distribution) > 1:
                    counts = list(distribution.values())
                    max_count = max(counts)
                    min_count = min(counts)
                    class_imbalance_ratio = max_count / min_count if min_count > 0 else None
                    break
        
        # Count datasets by status
        datasets_by_status = {
            "ready": sum(1 for d in datasets if d.is_ready),
            "processing": sum(1 for d in datasets if not d.is_ready and not d.is_deleted),
            "error": sum(1 for d in datasets if d.is_deleted)
        }
        
        # Data source breakdown (by dataset type)
        data_sources = {}
        for dataset in datasets:
            source = dataset.dataset_type or "Unknown"
            data_sources[source] = data_sources.get(source, 0) + 1
        
        # Generate recommendations based on quality metrics
        recommendations = []
        
        if avg_quality < 70:
            recommendations.append("⚠️ Average data quality is below 70%. Consider data cleaning.")
        
        if missing_percentage > 20:
            recommendations.append(f"⚠️ High missing values detected ({missing_percentage:.1f}%). Apply imputation strategies.")
        
        if class_imbalance_ratio and class_imbalance_ratio > 3:
            recommendations.append(f"⚖️ Significant class imbalance detected (ratio: {class_imbalance_ratio:.1f}:1). Consider SMOTE or oversampling.")
        
        if datasets_by_status["error"] > 0:
            recommendations.append(f"❌ {datasets_by_status['error']} datasets have errors. Check upload logs.")
        
        if not recommendations:
            recommendations.append("✅ Data quality looks good. Ready for model training.")
        
        return {
            "total_datasets": total_datasets,
            "average_quality_score": round(avg_quality, 2),
            "missing_values_percentage": round(missing_percentage, 2),
            "class_imbalance_ratio": round(class_imbalance_ratio, 2) if class_imbalance_ratio else None,
            "outliers_detected": 0,  # Placeholder - would need statistical analysis
            "data_sources": data_sources,
            "datasets_by_status": datasets_by_status,
            "class_distribution": class_distribution,
            "recommendations": recommendations,
            "last_updated": datasets[-1].uploaded_at.isoformat() if datasets else None
        }
        
    except Exception as e:
        logger.error(f"Error getting data quality summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get data quality summary: {str(e)}"
        )


@router.get("/datasets/{dataset_id}/quality")
async def get_dataset_quality(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get detailed quality metrics for a specific dataset
    """
    from app.models.flexible_schema import FlexibleDatasetWide
    
    dataset = db.query(FlexibleDatasetWide).filter(
        FlexibleDatasetWide.session_id == dataset_id,
        FlexibleDatasetWide.uploaded_by == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return {
        "dataset_id": dataset.session_id,
        "dataset_name": dataset.dataset_name,
        "quality_score": dataset.data_quality_score,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count,
        "missing_values": 0,  # Would calculate from actual data
        "outliers": 0,
        "duplicate_rows": 0,
        "data_types": {},
        "recommendations": []
    }
