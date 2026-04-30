"""
ML Utilities API Endpoints
Endpoints for schema validation, provenance tracking, and bridge service
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import logging
import uuid

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.ml_schema_validator import MLSchemaValidator
from app.services.data_provenance_service import DataProvenanceService
from app.services.ml_bridge_service import MLBridgeService

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== SCHEMA VALIDATION ENDPOINTS ==========

@router.post("/ml-utils/validate-schema/{session_id}")
async def validate_schema_for_ml(
    session_id: str,
    import_batch_id: Optional[str] = Query(None, description="Specific batch ID to validate"),
    dataset_type: Optional[str] = Query(None, description="Dataset type filter"),
    min_records: int = Query(50, description="Minimum required records"),
    target_column: str = Query("labels_disease_classification", description="Target column name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Validate data schema before ML training
    
    Performs comprehensive checks:
    - Minimum records
    - Target column exists
    - Feature count
    - Missing values
    - Data types
    - Class balance
    - JSONB structure
    
    Returns validation report with issues and recommendations
    """
    try:
        validator = MLSchemaValidator(db)
        
        batch_uuid = uuid.UUID(import_batch_id) if import_batch_id else None
        
        validation_report = validator.validate_for_ml_training(
            import_batch_id=batch_uuid,
            dataset_type=dataset_type,
            min_records=min_records,
            target_column=target_column
        )
        
        return validation_report
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid batch ID: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Schema validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


# ========== PROVENANCE TRACKING ENDPOINTS ==========

@router.get("/ml-utils/provenance/upload/{batch_id}")
async def get_upload_provenance(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get complete data provenance chain for a batch
    
    Returns transformation history from upload to ML training:
    - Upload metadata
    - Layer 5 preprocessing
    - Structured tests transformation
    - Labeling operations
    - Feature engineering
    - ML training
    """
    try:
        provenance_service = DataProvenanceService(db)
        
        batch_uuid = uuid.UUID(import_batch_id)
        
        provenance_chain = provenance_service.get_complete_provenance_chain(batch_uuid)
        
        return provenance_chain
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid batch ID format"
        )
    except Exception as e:
        logger.error(f"Provenance retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve provenance: {str(e)}"
        )


@router.get("/ml-utils/provenance/preprocessing/{session_id}")
async def get_preprocessing_provenance(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Validate that provenance chain is complete
    
    Checks for all required transformation stages and reports missing steps
    """
    try:
        provenance_service = DataProvenanceService(db)
        
        session_uuid = uuid.UUID(session_id)
        
        validation_result = provenance_service.validate_provenance_completeness(session_uuid)
        
        return validation_result
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid batch ID format"
        )
    except Exception as e:
        logger.error(f"Provenance validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@router.get("/ml-utils/provenance/chain/{batch_id}")
async def get_complete_provenance_chain(
    batch_id: str,
    format: str = Query("json", description="Report format: json or markdown"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export provenance chain as formatted report
    
    Formats:
    - json: Structured JSON report
    - markdown: Human-readable markdown report
    """
    try:
        provenance_service = DataProvenanceService(db)
        
        batch_uuid = uuid.UUID(batch_id)
        
        report = provenance_service.export_provenance_report(batch_uuid, format=format)
        
        if format == 'markdown':
            return {"report": report, "format": "markdown"}
        else:
            return report
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Report export error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


# ========== BRIDGE SERVICE ENDPOINTS ==========

@router.post("/ml-utils/prepare-data/{session_id}")
async def prepare_ml_data(
    session_id: str,
    dataset_type: Optional[str] = Query(None, description="Dataset type filter"),
    target_column: str = Query("labels_disease_classification", description="Target column"),
    validate: bool = Query(True, description="Validate before preparation"),
    drop_unlabeled: bool = Query(False, description="Drop records without labels"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Prepare data from flexible_dataset_wide for ML training
    
    Performs:
    1. Schema validation (if requested)
    2. Load from flexible_dataset_wide
    3. Flatten JSONB to DataFrame
    4. Clean data for ML requirements
    5. Handle unlabeled records
    6. Track provenance
    
    Returns ML-ready dataset statistics and metadata
    """
    try:
        bridge_service = MLBridgeService(db)
        
        session_uuid = uuid.UUID(session_id)
        
        result = bridge_service.prepare_data_for_ml(
            import_batch_id=session_uuid,
            dataset_type=dataset_type,
            target_column=target_column,
            validate=validate,
            drop_unlabeled=drop_unlabeled
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Data preparation failed')
            )
        
        # Don't return DataFrame (not JSON serializable), only metadata
        return {
            'success': True,
            'metadata': result['metadata'],
            'validation_report': result.get('validation_report'),
            'provenance': result.get('provenance')
        }
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid batch ID format"
        )
    except Exception as e:
        logger.error(f"Data preparation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preparation failed: {str(e)}"
        )


@router.get("/ml-utils/statistics/{batch_id}")
async def get_ml_statistics(
    batch_id: str,
    dataset_type: Optional[str] = Query(None, description="Dataset type filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get statistics about ML-ready data
    
    Returns:
    - Record counts
    - Column counts (numeric/categorical)
    - Missing value statistics
    - Data quality metrics
    """
    try:
        bridge_service = MLBridgeService(db)
        
        batch_uuid = uuid.UUID(batch_id)
        
        stats = bridge_service.get_ml_ready_statistics(
            import_batch_id=batch_uuid,
            dataset_type=dataset_type
        )
        
        return stats
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid batch ID format"
        )
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


# ========== HEALTH CHECK ==========

@router.get("/ml-utils/health")
async def ml_health_check(
    db: Session = Depends(get_db)
):
    """
    Check ML pipeline health and readiness
    
    Returns:
    - Service availability
    - Database connectivity
    - Component status
    """
    try:
        # Test database connectivity
        db.execute(text("SELECT 1"))
        
        # Test services
        validator = MLSchemaValidator(db)
        provenance = DataProvenanceService(db)
        bridge = MLBridgeService(db)
        
        return {
            'status': 'healthy',
            'services': {
                'schema_validator': 'available',
                'provenance_tracker': 'available',
                'bridge_service': 'available'
            },
            'database': 'connected'
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML pipeline unhealthy"
        )
