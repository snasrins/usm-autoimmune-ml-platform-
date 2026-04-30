"""
Unstructured Data Pipeline API Endpoints
=========================================
Flow: Upload → MinIO [usm-raw] → OCR [Qwen3-VL-2B-Instruct] → NER → Preview

Author: Syarifah Fajriyah
Date: April 3, 2026
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.unstructured_pipeline_service import UnstructuredPipelineService

router = APIRouter()


# ═══════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_and_process_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload unstructured file (PDF/TXT/Image) and process:
    1. Upload to MinIO [usm-raw]
    2. OCR with Qwen3-VL-2B-Instruct
    3. NER extraction
    4. Save to validation_queue
    
    Returns:
        {
            "success": true,
            "validation_id": 123,
            "filename": "lab_report.pdf",
            "minio_path": "usm-raw/2026/04/03/lab_report.pdf",
            "extracted_text": "...",
            "medical_entities": [...],
            "status": "success",
            "processing_time": 45.2,
            "page_count": 7,
            "confidence": 0.85
        }
    """
    try:
        # Read file
        file_data = await file.read()
        filename = file.filename
        
        # Detect file type
        ext = filename.split('.')[-1].lower()
        if ext not in ['pdf', 'txt', 'png', 'jpg', 'jpeg']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {ext}. Supported: PDF, TXT, PNG, JPG"
            )
        
        # Initialize pipeline
        pipeline = UnstructuredPipelineService(db)
        
        # Process
        result = pipeline.upload_and_process(
            file_data=file_data,
            filename=filename,
            file_type=ext,
            user_id=current_user.id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


@router.get("/preview/{validation_id}")
async def get_preview(
    validation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get preview of processed unstructured data
    
    Returns:
        {
            "validation_id": 123,
            "stage": "ocr_complete",
            "status": "pending_review",
            "data": {
                "document": {...},
                "metadata": {...},
                "extracted_text": "...",
                "medical_entities": [...]
            },
            "created_at": "2026-04-03T10:30:00"
        }
    """
    try:
        pipeline = UnstructuredPipelineService(db)
        result = pipeline.get_preview(validation_id)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preview not found: {str(e)}"
        )


@router.get("/list")
async def list_processed_files(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all processed unstructured files
    
    Returns:
        [
            {
                "validation_id": 123,
                "filename": "lab_report.pdf",
                "status": "pending_review",
                "created_at": "2026-04-03T10:30:00",
                "page_count": 7,
                "entity_count": 45
            },
            ...
        ]
    """
    try:
        from sqlalchemy import text
        
        query = text("""
            SELECT 
                id,
                validation_data->>'document'->>'filename' as filename,
                status,
                created_at,
                validation_data->'document'->>'page_count' as page_count,
                jsonb_array_length(validation_data->'medical_entities') as entity_count
            FROM validation_queue
            WHERE stage = 'ocr_complete'
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        results = db.execute(query, {"limit": limit}).fetchall()
        
        return [
            {
                "validation_id": row[0],
                "filename": row[1],
                "status": row[2],
                "created_at": row[3].isoformat(),
                "page_count": int(row[4]) if row[4] else 0,
                "entity_count": row[5] if row[5] else 0
            }
            for row in results
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )


@router.post("/approve/{validation_id}")
async def approve_validation(
    validation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve processed data and move to next stage
    
    Returns:
        {
            "success": true,
            "message": "Validation approved",
            "validation_id": 123
        }
    """
    try:
        from sqlalchemy import text
        
        query = text("""
            UPDATE validation_queue
            SET status = 'approved',
                reviewed_by = :user_id,
                reviewed_at = NOW()
            WHERE id = :validation_id
            RETURNING id
        """)
        
        result = db.execute(
            query,
            {
                "validation_id": validation_id,
                "user_id": current_user.id
            }
        )
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation ID {validation_id} not found"
            )
        
        db.commit()
        
        return {
            "success": True,
            "message": "Validation approved",
            "validation_id": validation_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Approval failed: {str(e)}"
        )


@router.post("/reject/{validation_id}")
async def reject_validation(
    validation_id: int,
    reason: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reject processed data and request corrections
    
    Returns:
        {
            "success": true,
            "message": "Validation rejected",
            "validation_id": 123
        }
    """
    try:
        from sqlalchemy import text
        
        query = text("""
            UPDATE validation_queue
            SET status = 'rejected',
                reviewed_by = :user_id,
                reviewed_at = NOW(),
                rejection_reason = :reason
            WHERE id = :validation_id
            RETURNING id
        """)
        
        result = db.execute(
            query,
            {
                "validation_id": validation_id,
                "user_id": current_user.id,
                "reason": reason
            }
        )
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation ID {validation_id} not found"
            )
        
        db.commit()
        
        return {
            "success": True,
            "message": "Validation rejected",
            "validation_id": validation_id,
            "reason": reason
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rejection failed: {str(e)}"
        )
