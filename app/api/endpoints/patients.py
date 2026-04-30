"""
Patient API Endpoints
Query and retrieve patient data with lab results
"""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models import User
from app.services.query_service import QueryService


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class PatientSearchRequest(BaseModel):
    """Request model for patient search"""
    disease_name: Optional[str] = None
    disease_code: Optional[str] = None
    age_min: Optional[int] = Field(None, ge=0, le=120)
    age_max: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = None
    test_code: Optional[str] = None
    test_abnormal: Optional[bool] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get(
    "/{patient_id}",
    summary="Get Patient Details",
    description="Get complete patient record with all lab results and diagnoses"
)
async def get_patient(
    patient_id: int,
    include_inactive: bool = Query(False, description="Include inactive records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get complete patient record including:
    - Demographics
    - All diagnoses
    - All lab results with test definitions
    """
    service = QueryService(db)
    patient = service.get_patient_with_labs(
        patient_id=patient_id,
        include_inactive=include_inactive
    )
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient ID {patient_id} not found"
        )
    
    return patient


@router.get(
    "/",
    summary="Search Patients",
    description="Search patients with multiple filters"
)
async def search_patients(
    disease_name: Optional[str] = Query(None, description="Disease name (partial match)"),
    disease_code: Optional[str] = Query(None, description="ICD-10 disease code"),
    age_min: Optional[int] = Query(None, ge=0, le=120, description="Minimum age"),
    age_max: Optional[int] = Query(None, ge=0, le=120, description="Maximum age"),
    gender: Optional[str] = Query(None, description="Gender (Male/Female/Other)"),
    test_code: Optional[str] = Query(None, description="Filter by test code"),
    test_abnormal: Optional[bool] = Query(None, description="Filter by abnormal results"),
    batch_id: Optional[str] = Query(None, description="Filter by import batch ID"),
    limit: int = Query(50, ge=1, le=500, description="Results per page"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search patients with flexible filters.
    
    Examples:
    - Find all SLE patients: `disease_name=lupus`
    - Find women aged 30-50: `gender=Female&age_min=30&age_max=50`
    - Find patients with abnormal ANA: `test_code=ana&test_abnormal=true`
    - Find patients from specific import: `batch_id=77601e57-01ad-43bc-adb6-b5f794b96eda`
    """
    service = QueryService(db)
    return service.search_patients(
        disease_name=disease_name,
        disease_code=disease_code,
        batch_id=batch_id,
        age_min=age_min,
        age_max=age_max,
        gender=gender,
        test_code=test_code,
        test_abnormal=test_abnormal,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{patient_id}/summary",
    summary="Get Patient Summary",
    description="Get patient summary with statistics"
)
async def get_patient_summary(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get patient summary including:
    - Total diagnoses
    - Total lab results
    - Abnormal result rate
    - Date range of tests
    - Unique test count
    """
    service = QueryService(db)
    summary = service.get_patient_summary(patient_id)
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient ID {patient_id} not found"
        )
    
    return summary


@router.get(
    "/{patient_id}/labs",
    summary="Get Patient Lab Results",
    description="Get all lab results for a patient with optional filters"
)
async def get_patient_labs(
    patient_id: int,
    test_code: Optional[str] = Query(None, description="Filter by test code"),
    test_category: Optional[str] = Query(None, description="Filter by test category"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get lab results for a patient with filters.
    
    Examples:
    - All ANA results: `test_code=ana`
    - All autoantibody tests: `test_category=Autoantibody`
    - Results from 2024: `date_from=2024-01-01&date_to=2024-12-31`
    """
    service = QueryService(db)
    results = service.get_lab_trends(
        patient_id=patient_id,
        test_code=test_code,
        test_category=test_category,
        date_from=date_from,
        date_to=date_to,
        limit=limit
    )
    
    return {
        'patient_id': patient_id,
        'total_results': len(results),
        'results': results
    }


@router.get(
    "/{patient_id}/labs/trends",
    summary="Get Lab Result Trends",
    description="Get time-series lab result trends for a patient"
)
async def get_lab_trends(
    patient_id: int,
    test_code: str = Query(..., description="Test code to track"),
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get time-series trends for a specific test.
    
    Useful for tracking disease progression or treatment response.
    Example: Track CRP levels over time for inflammation monitoring.
    """
    service = QueryService(db)
    results = service.get_lab_trends(
        patient_id=patient_id,
        test_code=test_code,
        date_from=date_from,
        date_to=date_to
    )
    
    return {
        'patient_id': patient_id,
        'test_code': test_code,
        'data_points': len(results),
        'trends': results
    }


@router.get(
    "/{patient_id}/labs/abnormal",
    summary="Get Abnormal Lab Results",
    description="Get all abnormal lab results for a patient"
)
async def get_abnormal_results(
    patient_id: int,
    severity: Optional[str] = Query(None, description="Severity flag (H/L/HH/LL)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all abnormal lab results.
    
    Severity flags:
    - H: High
    - HH: Critically high
    - L: Low
    - LL: Critically low
    """
    service = QueryService(db)
    results = service.get_abnormal_results(
        patient_id=patient_id,
        severity=severity
    )
    
    return {
        'patient_id': patient_id,
        'abnormal_count': len(results),
        'results': results
    }


@router.post(
    "/compare",
    summary="Compare Test Results",
    description="Compare test results across multiple patients"
)
async def compare_test_results(
    patient_ids: List[int] = Query(..., description="List of patient IDs"),
    test_code: str = Query(..., description="Test code to compare"),
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Compare test results across multiple patients.
    
    Useful for cohort analysis or treatment comparison studies.
    """
    service = QueryService(db)
    comparison = service.compare_test_results(
        patient_ids=patient_ids,
        test_code=test_code,
        date_from=date_from,
        date_to=date_to
    )
    
    return {
        'test_code': test_code,
        'patient_count': len(comparison),
        'comparison': comparison
    }


@router.get(
    "/tests/{test_code}/statistics",
    summary="Get Test Statistics",
    description="Get statistics for a test across all patients"
)
async def get_test_statistics(
    test_code: str,
    disease_name: Optional[str] = Query(None, description="Filter by disease"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get aggregated statistics for a specific test.
    
    Returns:
    - Mean, median, std, min, max
    - Total result count
    - Abnormal result rate
    
    Optionally filter by disease for disease-specific reference ranges.
    """
    service = QueryService(db)
    stats = service.get_test_statistics(
        test_code=test_code,
        disease_name=disease_name
    )
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No numeric results found for test '{test_code}'"
        )
    
    return stats


@router.get(
    "/disease-data",
    summary="Query Disease-Specific Data",
    description="Query JSONB disease-specific data"
)
async def query_disease_data(
    disease_name: str = Query(..., description="Disease name"),
    data_category: Optional[str] = Query(None, description="Data category"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Query disease-specific JSONB data.
    
    Examples:
    - All SLE data: `disease_name=Lupus`
    - SLE symptom data: `disease_name=Lupus&data_category=symptoms`
    """
    service = QueryService(db)
    results = service.query_disease_data(
        disease_name=disease_name,
        data_category=data_category,
        limit=limit
    )
    
    return {
        'disease_name': disease_name,
        'total_records': len(results),
        'data': results
    }
