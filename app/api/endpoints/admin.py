"""
Admin API Endpoints
System administration and monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import psutil

# Optional torch import
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

from app.core.database import get_db
from app.api.deps import get_current_superuser, get_current_active_user
from app.models.user import User
from app.models.patient import Patient
from app.models import LabTestDefinition
from app.schemas.user import UserResponse
from app.services.test_manager import TestManager

router = APIRouter()


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only)
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Delete a user (admin only)
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": f"User {user.username} deleted successfully"}


@router.get("/system/info")
async def get_system_info(
    current_user: User = Depends(get_current_superuser)
):
    """
    Get system information (admin only)
    """
    # CPU info
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    
    # Memory info
    memory = psutil.virtual_memory()
    
    # Disk info
    disk = psutil.disk_usage('/')
    
    # GPU info
    gpu_info = {}
    if TORCH_AVAILABLE and torch.cuda.is_available():
        gpu_info = {
            "gpu_available": True,
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_memory_total_gb": round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2),
            "gpu_memory_allocated_gb": round(torch.cuda.memory_allocated(0) / 1024**3, 2),
            "gpu_memory_reserved_gb": round(torch.cuda.memory_reserved(0) / 1024**3, 2),
            "cuda_version": torch.version.cuda
        }
    else:
        gpu_info = {"gpu_available": False}
    
    return {
        "cpu": {
            "usage_percent": cpu_percent,
            "cores": cpu_count
        },
        "memory": {
            "total_gb": round(memory.total / 1024**3, 2),
            "available_gb": round(memory.available / 1024**3, 2),
            "used_gb": round(memory.used / 1024**3, 2),
            "percent": memory.percent
        },
        "disk": {
            "total_gb": round(disk.total / 1024**3, 2),
            "used_gb": round(disk.used / 1024**3, 2),
            "free_gb": round(disk.free / 1024**3, 2),
            "percent": disk.percent
        },
        "gpu": gpu_info
    }


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Get platform statistics (admin only)
    """
    try:
        # Count users
        total_users = db.query(func.count(User.id)).scalar() or 0
        active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
        
        # Count patients
        total_patients = db.query(func.count(Patient.id)).scalar() or 0
        # Note: Prediction tracking not yet implemented
        patients_with_predictions = 0  # TODO: Add when prediction service is ready
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "inactive": total_users - active_users
            },
            "patients": {
                "total": total_patients,
                "with_predictions": patients_with_predictions,
                "without_predictions": total_patients - patients_with_predictions
            }
        }
    except Exception as e:
        # Return empty stats if database query fails
        return {
            "users": {
                "total": 0,
                "active": 0,
                "inactive": 0
            },
            "patients": {
                "total": 0,
                "with_predictions": 0,
                "without_predictions": 0
            },
            "error": str(e)
        }


# ============================================================================
# Lab Test Management Endpoints
# ============================================================================

# Pydantic Models
class TestCreateRequest(BaseModel):
    """Request model for creating new test"""
    test_code: str = Field(..., min_length=1, max_length=50)
    test_name: str = Field(..., min_length=1, max_length=200)
    test_category: str
    data_type: str = Field(default="mixed")
    unit: Optional[str] = Field(None, max_length=50)
    default_reference_range: Optional[Dict] = None
    description: Optional[str] = None


class TestUpdateRequest(BaseModel):
    """Request model for updating test"""
    test_name: Optional[str] = Field(None, min_length=1, max_length=200)
    test_category: Optional[str] = None
    data_type: Optional[str] = None
    unit: Optional[str] = Field(None, max_length=50)
    default_reference_range: Optional[Dict] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/tests/pending")
async def get_pending_tests(
    file_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get unmapped test columns that need approval"""
    manager = TestManager(db)
    return manager.get_pending_tests(file_id=file_id, limit=limit)


@router.post("/tests", status_code=status.HTTP_201_CREATED)
async def create_test(
    test: TestCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new lab test definition"""
    manager = TestManager(db)
    
    try:
        created_test = manager.create_test(
            test_code=test.test_code,
            test_name=test.test_name,
            test_category=test.test_category,
            data_type=test.data_type,
            unit=test.unit,
            default_reference_range=test.default_reference_range,
            description=test.description,
            created_by=current_user.id
        )
        
        return {
            "test_id": created_test.test_id,
            "test_code": created_test.test_code,
            "test_name": created_test.test_name,
            "test_category": created_test.test_category,
            "message": "Test created successfully"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/tests")
async def list_tests(
    test_category: Optional[str] = Query(None),
    data_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get paginated list of lab tests"""
    manager = TestManager(db)
    result = manager.get_tests(
        test_category=test_category,
        data_type=data_type,
        is_active=is_active,
        search=search,
        limit=limit,
        offset=offset
    )
    
    # Convert to dict
    result['tests'] = [
        {
            'test_id': t.test_id,
            'test_code': t.test_code,
            'test_name': t.test_name,
            'test_category': t.test_category,
            'data_type': t.data_type,
            'unit': t.unit,
            'is_active': t.is_active,
        }
        for t in result['tests']
    ]
    
    return result


@router.get("/tests/{test_id}")
async def get_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get single test by ID"""
    manager = TestManager(db)
    test = manager.get_test_by_id(test_id)
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test ID {test_id} not found"
        )
    
    return {
        'test_id': test.test_id,
        'test_code': test.test_code,
        'test_name': test.test_name,
        'test_category': test.test_category,
        'data_type': test.data_type,
        'unit': test.unit,
        'default_reference_range': test.default_reference_range,
        'description': test.description,
        'is_active': test.is_active,
        'created_at': test.created_at.isoformat()
    }


@router.put("/tests/{test_id}")
async def update_test(
    test_id: int,
    updates: TestUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update lab test definition"""
    manager = TestManager(db)
    
    # Filter out None values
    update_dict = {k: v for k, v in updates.dict().items() if v is not None}
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    try:
        updated_test = manager.update_test(
            test_id=test_id,
            updates=update_dict,
            updated_by=current_user.id
        )
        
        return {
            'test_id': updated_test.test_id,
            'test_code': updated_test.test_code,
            'test_name': updated_test.test_name,
            'message': 'Test updated successfully'
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/tests/{test_id}")
async def deactivate_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deactivate lab test (soft delete)"""
    manager = TestManager(db)
    
    try:
        deactivated_test = manager.deactivate_test(
            test_id=test_id,
            updated_by=current_user.id
        )
        
        return {
            'test_id': deactivated_test.test_id,
            'test_code': deactivated_test.test_code,
            'is_active': deactivated_test.is_active,
            'message': 'Test deactivated successfully'
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/tests/meta/categories")
async def get_test_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of all test categories"""
    manager = TestManager(db)
    return {"categories": manager.get_categories()}


@router.get("/tests/meta/stats")
async def get_test_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get test catalog statistics"""
    manager = TestManager(db)
    return manager.get_test_stats()
