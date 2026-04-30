"""
Data Import API Endpoints
Handles file upload and data ingestion with full import pipeline
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services import BatchImporter

router = APIRouter()


@router.post("/import")
async def import_data_file(
    file: UploadFile = File(...),
    disease_name: str = Form(...),
    disease_code: Optional[str] = Form(None),
    dataset_type: str = Form(...),
    auto_approve_tests: bool = Form(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Import patient data from Excel/CSV file
    
    Args:
        file: Excel or CSV file
        disease_name: Disease name (e.g., 'Systemic Lupus Erythematosus')
        disease_code: ICD-10 code (e.g., 'M32.1')
        dataset_type: Dataset identifier (e.g., 'SLE', 'SJOGREN')
        auto_approve_tests: Auto-create new test definitions for unmapped columns
    
    Returns:
        Import results and statistics
    """
    # Validate file extension
    filename = file.filename
    if not filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only Excel (.xlsx, .xls) and CSV files are supported."
        )
    
    # Create upload directory if not exists
    upload_dir = "/data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save uploaded file temporarily
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_filename = f"temp_{timestamp}_{filename}"
    temp_path = os.path.join(upload_dir, temp_filename)
    
    try:
        # Save file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Import data
        importer = BatchImporter(db, user_id=current_user.id)
        result = importer.import_file(
            file_path=temp_path,
            disease_name=disease_name,
            dataset_type=dataset_type,
            disease_code=disease_code,
            auto_approve_tests=auto_approve_tests
        )
        
        # Clean up temp file if import successful
        if result['success']:
            os.remove(temp_path)
        
        return result
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )


@router.get("/files")
async def list_uploaded_files(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all uploaded files
    """
    from app.models import UploadedFile
    
    files = db.query(UploadedFile).order_by(UploadedFile.uploaded_at.desc()).all()
    
    return {
        "files": [
            {
                "file_id": f.file_id,
                "original_filename": f.original_filename,
                "dataset_type": f.dataset_type,
                "upload_status": f.upload_status,
                "row_count": f.row_count,
                "column_count": f.column_count,
                "uploaded_at": f.uploaded_at,
                "import_stats": f.import_stats
            }
            for f in files
        ]
    }


@router.get("/files/{file_id}")
async def get_file_details(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about an uploaded file
    """
    from app.models import UploadedFile, DataIngestionAudit
    
    file = db.query(UploadedFile).filter(UploadedFile.file_id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get audit logs
    audits = db.query(DataIngestionAudit).filter(
        DataIngestionAudit.file_id == file_id
    ).order_by(DataIngestionAudit.performed_at.desc()).all()
    
    return {
        "file": {
            "file_id": file.file_id,
            "original_filename": file.original_filename,
            "dataset_type": file.dataset_type,
            "upload_status": file.upload_status,
            "file_size_bytes": file.file_size_bytes,
            "row_count": file.row_count,
            "column_count": file.column_count,
            "column_mapping": file.column_mapping,
            "validation_errors": file.validation_errors,
            "import_stats": file.import_stats,
            "uploaded_at": file.uploaded_at
        },
        "audits": [
            {
                "action_type": a.action_type,
                "action_status": a.action_status,
                "records_affected": a.records_affected,
                "execution_time_ms": a.execution_time_ms,
                "error_message": a.error_message,
                "performed_at": a.performed_at
            }
            for a in audits
        ]
    }


@router.post("/preview")
async def preview_file(
    file: UploadFile = File(...),
    rows: int = 10,
    current_user: User = Depends(get_current_active_user)
):
    """
    Preview file contents without importing
    """
    from app.services import FileParser
    import tempfile
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    
    try:
        parser = FileParser(tmp_path)
        
        # Validate
        validation = parser.validate_file()
        if not validation['valid']:
            raise HTTPException(status_code=400, detail=validation['error'])
        
        # Parse and preview
        df = parser.parse()
        preview = parser.get_preview(rows=rows)
        stats = parser.get_column_stats()
        metadata = parser.get_metadata()
        
        return {
            "filename": file.filename,
            "metadata": metadata,
            "preview": preview,
            "column_stats": stats
        }
        
    finally:
        os.remove(tmp_path)
