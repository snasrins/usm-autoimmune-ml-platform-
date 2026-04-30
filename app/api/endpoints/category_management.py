"""
Category Management Admin Endpoints
Allows admins to manage disease categories dynamically - NO hardcoding
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from pydantic import BaseModel, Field
import json
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_superuser, get_current_active_user
from app.models.user import User
from app.models.disease_category import DiseaseCategory, DiagnosisCategoryMapping, CategoryAuditLog

router = APIRouter()


# ===================================================
# SCHEMAS
# ===================================================

class DiseaseCategoryCreate(BaseModel):
    category_name: str = Field(..., max_length=100, description="Unique category name (e.g., 'SLE_with_LN')")
    category_code: str = Field(..., max_length=50, description="API-friendly code (e.g., 'sle_ln')")
    category_label: Optional[str] = Field(None, description="Display name (e.g., 'SLE with Lupus Nephritis')")
    description: Optional[str] = None
    is_active: bool = True


class DiseaseCategoryUpdate(BaseModel):
    category_name: Optional[str] = Field(None, max_length=100)
    category_code: Optional[str] = Field(None, max_length=50)
    category_label: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DiseaseCategoryResponse(BaseModel):
    category_id: int
    category_name: str
    category_code: str
    category_label: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    mapping_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class DiagnosisMappingCreate(BaseModel):
    category_id: int
    diagnosis_pattern: str = Field(..., max_length=200, description="Pattern to match in diagnosis field")
    match_type: str = Field(default='exact', description="'exact', 'contains', 'starts_with', 'regex'")
    priority: int = Field(default=0, description="Higher priority wins on conflicts")
    condition_field: Optional[str] = Field(None, max_length=100)
    condition_value: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class DiagnosisMappingUpdate(BaseModel):
    category_id: Optional[int] = None
    diagnosis_pattern: Optional[str] = Field(None, max_length=200)
    match_type: Optional[str] = None
    priority: Optional[int] = None
    condition_field: Optional[str] = None
    condition_value: Optional[str] = None
    is_active: Optional[bool] = None


class DiagnosisMappingResponse(BaseModel):
    mapping_id: int
    category_id: int
    category_name: str
    diagnosis_pattern: str
    match_type: str
    priority: int
    condition_field: Optional[str]
    condition_value: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===================================================
# CATEGORY CRUD ENDPOINTS
# ===================================================

@router.get("/categories", response_model=List[DiseaseCategoryResponse])
async def list_disease_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    active_only: bool = Query(True, description="Filter to active categories only"),
    search: Optional[str] = Query(None, description="Search in category name/label"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all disease categories
    """
    query = db.query(
        DiseaseCategory,
        func.count(DiagnosisCategoryMapping.mapping_id).label('mapping_count')
    ).outerjoin(DiagnosisCategoryMapping)
    
    if active_only:
        query = query.filter(DiseaseCategory.is_active == True)
    
    if search:
        query = query.filter(
            or_(
                DiseaseCategory.category_name.ilike(f'%{search}%'),
                DiseaseCategory.category_label.ilike(f'%{search}%'),
                DiseaseCategory.category_code.ilike(f'%{search}%')
            )
        )
    
    query = query.group_by(DiseaseCategory.category_id)
    results = query.offset(skip).limit(limit).all()
    
    return [
        DiseaseCategoryResponse(
            **cat.__dict__,
            mapping_count=count
        )
        for cat, count in results
    ]


@router.get("/categories/{category_id}", response_model=DiseaseCategoryResponse)
async def get_disease_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific disease category by ID
    """
    category = db.query(DiseaseCategory).filter(DiseaseCategory.category_id == category_id).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    mapping_count = db.query(func.count(DiagnosisCategoryMapping.mapping_id)).filter(
        DiagnosisCategoryMapping.category_id == category_id
    ).scalar()
    
    return DiseaseCategoryResponse(
        **category.__dict__,
        mapping_count=mapping_count
    )


@router.post("/categories", response_model=DiseaseCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_disease_category(
    category: DiseaseCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    Create a new disease category (admin only)
    """
    # Check for duplicates
    existing = db.query(DiseaseCategory).filter(
        or_(
            DiseaseCategory.category_name == category.category_name,
            DiseaseCategory.category_code == category.category_code
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Category with name '{category.category_name}' or code '{category.category_code}' already exists"
        )
    
    # Create category
    new_category = DiseaseCategory(
        **category.dict(),
        created_by=current_user.id
    )
    
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    # Audit log
    audit = CategoryAuditLog(
        table_name='dim_disease_categories',
        record_id=new_category.category_id,
        action='INSERT',
        new_data=json.dumps(category.dict()),
        changed_by=current_user.id
    )
    db.add(audit)
    db.commit()
    
    return DiseaseCategoryResponse(
        **new_category.__dict__,
        mapping_count=0
    )


@router.patch("/categories/{category_id}", response_model=DiseaseCategoryResponse)
async def update_disease_category(
    category_id: int,
    updates: DiseaseCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    Update a disease category (admin only)
    """
    category = db.query(DiseaseCategory).filter(DiseaseCategory.category_id == category_id).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Store old data for audit
    old_data = {
        'category_name': category.category_name,
        'category_code': category.category_code,
        'category_label': category.category_label,
        'description': category.description,
        'is_active': category.is_active
    }
    
    # Update fields
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    
    # Audit log
    audit = CategoryAuditLog(
        table_name='dim_disease_categories',
        record_id=category_id,
        action='UPDATE',
        old_data=json.dumps(old_data),
        new_data=json.dumps(update_data),
        changed_by=current_user.id
    )
    db.add(audit)
    db.commit()
    
    mapping_count = db.query(func.count(DiagnosisCategoryMapping.mapping_id)).filter(
        DiagnosisCategoryMapping.category_id == category_id
    ).scalar()
    
    return DiseaseCategoryResponse(
        **category.__dict__,
        mapping_count=mapping_count
    )


@router.delete("/categories/{category_id}")
async def delete_disease_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    Delete a disease category (admin only)
    WARNING: This will cascade delete all associated mappings
    """
    category = db.query(DiseaseCategory).filter(DiseaseCategory.category_id == category_id).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Store for audit
    old_data = {
        'category_name': category.category_name,
        'category_code': category.category_code
    }
    
    # Delete (cascades to mappings)
    db.delete(category)
    db.commit()
    
    # Audit log
    audit = CategoryAuditLog(
        table_name='dim_disease_categories',
        record_id=category_id,
        action='DELETE',
        old_data=json.dumps(old_data),
        changed_by=current_user.id
    )
    db.add(audit)
    db.commit()
    
    return {"message": f"Category '{old_data['category_name']}' deleted successfully"}


# ===================================================
# MAPPING CRUD ENDPOINTS
# ===================================================

@router.get("/mappings", response_model=List[DiagnosisMappingResponse])
async def list_diagnosis_mappings(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List diagnosis→category mappings
    """
    query = db.query(
        DiagnosisCategoryMapping,
        DiseaseCategory.category_name
    ).join(DiseaseCategory)
    
    if category_id:
        query = query.filter(DiagnosisCategoryMapping.category_id == category_id)
    
    if active_only:
        query = query.filter(DiagnosisCategoryMapping.is_active == True)
    
    query = query.order_by(DiagnosisCategoryMapping.priority.desc())
    results = query.offset(skip).limit(limit).all()
    
    return [
        DiagnosisMappingResponse(
            **mapping.__dict__,
            category_name=cat_name
        )
        for mapping, cat_name in results
    ]


@router.post("/mappings", response_model=DiagnosisMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_diagnosis_mapping(
    mapping: DiagnosisMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    Create a new diagnosis→category mapping (admin only)
    """
    # Validate category exists
    category = db.query(DiseaseCategory).filter(DiseaseCategory.category_id == mapping.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Validate match_type
    if mapping.match_type not in ['exact', 'contains', 'starts_with', 'regex']:
        raise HTTPException(status_code=400, detail="Invalid match_type. Must be: exact, contains, starts_with, regex")
    
    # Create mapping
    new_mapping = DiagnosisCategoryMapping(
        **mapping.dict(),
        created_by=current_user.id
    )
    
    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)
    
    # Audit log
    audit = CategoryAuditLog(
        table_name='diagnosis_category_mappings',
        record_id=new_mapping.mapping_id,
        action='INSERT',
        new_data=json.dumps(mapping.dict()),
        changed_by=current_user.id
    )
    db.add(audit)
    db.commit()
    
    return DiagnosisMappingResponse(
        **new_mapping.__dict__,
        category_name=category.category_name
    )


@router.patch("/mappings/{mapping_id}", response_model=DiagnosisMappingResponse)
async def update_diagnosis_mapping(
    mapping_id: int,
    updates: DiagnosisMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    Update a diagnosis mapping (admin only)
    """
    mapping = db.query(DiagnosisCategoryMapping).filter(DiagnosisCategoryMapping.mapping_id == mapping_id).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    # Store old data for audit
    old_data = {k: v for k, v in mapping.__dict__.items() if not k.startswith('_')}
    
    # Update fields
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mapping, field, value)
    
    db.commit()
    db.refresh(mapping)
    
    # Audit log
    audit = CategoryAuditLog(
        table_name='diagnosis_category_mappings',
        record_id=mapping_id,
        action='UPDATE',
        old_data=json.dumps(old_data, default=str),
        new_data=json.dumps(update_data),
        changed_by=current_user.id
    )
    db.add(audit)
    db.commit()
    
    category = db.query(DiseaseCategory).filter(DiseaseCategory.category_id == mapping.category_id).first()
    
    return DiagnosisMappingResponse(
        **mapping.__dict__,
        category_name=category.category_name
    )


@router.delete("/mappings/{mapping_id}")
async def delete_diagnosis_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    Delete a diagnosis mapping (admin only)
    """
    mapping = db.query(DiagnosisCategoryMapping).filter(DiagnosisCategoryMapping.mapping_id == mapping_id).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    # Store for audit
    old_data = {
        'diagnosis_pattern': mapping.diagnosis_pattern,
        'match_type': mapping.match_type,
        'priority': mapping.priority
    }
    
    db.delete(mapping)
    db.commit()
    
    # Audit log
    audit = CategoryAuditLog(
        table_name='diagnosis_category_mappings',
        record_id=mapping_id,
        action='DELETE',
        old_data=json.dumps(old_data),
        changed_by=current_user.id
    )
    db.add(audit)
    db.commit()
    
    return {"message": "Mapping deleted successfully"}


# ===================================================
# UTILITY ENDPOINTS
# ===================================================

@router.post("/test-categorization")
async def test_diagnosis_categorization(
    diagnosis_text: str = Query(..., description="Diagnosis text to test"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Test which category a diagnosis text would map to
    Useful for validating mapping rules
    """
    # Execute the PostgreSQL function
    result = db.execute(
        "SELECT get_diagnosis_category(:diagnosis)",
        {"diagnosis": diagnosis_text}
    ).scalar()
    
    # Find the matching mapping details
    matched_mappings = db.query(
        DiagnosisCategoryMapping,
        DiseaseCategory.category_name
    ).join(DiseaseCategory).filter(
        DiagnosisCategoryMapping.is_active == True,
        DiseaseCategory.is_active == True
    ).order_by(DiagnosisCategoryMapping.priority.desc()).all()
    
    matched_details = None
    for mapping, cat_name in matched_mappings:
        diagnosis_lower = diagnosis_text.lower()
        pattern_lower = mapping.diagnosis_pattern.lower()
        
        if (
            (mapping.match_type == 'exact' and diagnosis_lower == pattern_lower) or
            (mapping.match_type == 'contains' and pattern_lower in diagnosis_lower) or
            (mapping.match_type == 'starts_with' and diagnosis_lower.startswith(pattern_lower))
        ):
            matched_details = {
                'mapping_id': mapping.mapping_id,
                'pattern': mapping.diagnosis_pattern,
                'match_type': mapping.match_type,
                'priority': mapping.priority
            }
            break
    
    return {
        'diagnosis_text': diagnosis_text,
        'matched_category': result,
        'mapping_details': matched_details
    }


@router.get("/audit-log")
async def get_category_audit_log(
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    Get audit log for category management changes (admin only)
    """
    query = db.query(CategoryAuditLog)
    
    if table_name:
        query = query.filter(CategoryAuditLog.table_name == table_name)
    
    query = query.order_by(CategoryAuditLog.changed_at.desc())
    logs = query.offset(skip).limit(limit).all()
    
    return {
        'total': query.count(),
        'logs': [
            {
                'audit_id': log.audit_id,
                'table_name': log.table_name,
                'record_id': log.record_id,
                'action': log.action,
                'old_data': json.loads(log.old_data) if log.old_data else None,
                'new_data': json.loads(log.new_data) if log.new_data else None,
                'changed_by': log.changed_by,
                'changed_at': log.changed_at
            }
            for log in logs
        ]
    }
