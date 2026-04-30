"""
Enhanced Multi-Format Upload API Endpoint
Supports: CSV, Excel, JSON, XML, Parquet, PDF, Images, Word, TXT
Integrates: Qwen-VL for OCR, validation queue, audit trail
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import shutil
from datetime import datetime
import tempfile
from pathlib import Path

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.file_parser import FileParser
from app.services.qwen_ocr_service import QwenOCRService

router = APIRouter()

# Initialize Qwen OCR service (lazy loading)
_qwen_service = None

def get_qwen_service():
    global _qwen_service
    if _qwen_service is None:
        try:
            _qwen_service = QwenOCRService(use_vision=True, use_embeddings=True)
        except Exception as e:
            print(f"Warning: Qwen OCR not available: {e}")
    return _qwen_service


@router.post("/upload/multi-format")
async def upload_multi_format_file(
    file: UploadFile = File(...),
    dataset_type: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process any supported file format
    
    Supported Formats:
    - Structured: CSV, Excel (.xlsx, .xls), JSON, XML, Parquet
    - Unstructured: PDF, Word (.docx), Images (.png, .jpg, .tiff), TXT
    
    Returns:
        Upload result with preview, metadata, and processing status
    """
    # Create upload directory
    upload_dir = "/data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = Path(file.filename).suffix
    temp_filename = f"upload_{timestamp}_{current_user.username}{file_extension}"
    temp_path = os.path.join(upload_dir, temp_filename)
    
    try:
        # Save file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse file
        parser = FileParser(temp_path)
        
        # Validate
        validation = parser.validate_file()
        if not validation['valid']:
            os.remove(temp_path)
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "File validation failed",
                    "errors": validation['errors'],
                    "warnings": validation.get('warnings', [])
                }
            )
        
        # Parse based on format
        is_structured = parser.is_structured
        
        if is_structured:
            # Structured data → DataFrame
            df = parser.parse()
            preview = parser.get_preview(rows=10)
            
            result = {
                "file_id": temp_filename,
                "original_filename": file.filename,
                "file_type": "structured",
                "format": file_extension,
                "uploaded_by": current_user.username,
                "uploaded_at": datetime.now().isoformat(),
                "validation": validation,
                "metadata": parser.metadata,
                "preview": preview,
                "requires_validation": True,
                "next_step": "column_mapping"
            }
            
        else:
            # Unstructured data → Raw text + OCR
            raw_text = parser.parse()
            
            # Try Qwen OCR if available (for PDF/images)
            qwen_analysis = None
            if file_extension in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff']:
                qwen_service = get_qwen_service()
                if qwen_service:
                    try:
                        if file_extension == '.pdf':
                            qwen_result = qwen_service.process_pdf(temp_path)
                            qwen_analysis = {
                                "extracted_text": qwen_result.extracted_text,
                                "medical_entities": qwen_result.medical_entities,
                                "ocr_results": [
                                    {
                                        "page": r.page,
                                        "text": r.text[:500],  # Preview
                                        "confidence": r.confidence,
                                        "method": r.method
                                    }
                                    for r in qwen_result.ocr_results
                                ],
                                "total_pages": qwen_result.total_pages
                            }
                        else:  # Image
                            qwen_result = qwen_service.process_image(temp_path)
                            qwen_analysis = {
                                "extracted_text": qwen_result.text,
                                "confidence": qwen_result.confidence,
                                "medical_entities": qwen_result.metadata.get('medical_entities', []),
                                "document_type": qwen_result.metadata.get('document_type', 'unknown')
                            }
                    except Exception as e:
                        print(f"Qwen OCR failed: {e}")
            
            result = {
                "file_id": temp_filename,
                "original_filename": file.filename,
                "file_type": "unstructured",
                "format": file_extension,
                "uploaded_by": current_user.username,
                "uploaded_at": datetime.now().isoformat(),
                "validation": validation,
                "metadata": parser.metadata,
                "raw_text_preview": raw_text[:1000] if raw_text else None,
                "qwen_analysis": qwen_analysis,
                "requires_validation": True,
                "next_step": "ocr_review"
            }
        
        # Store in database (metadata_datasets table)
        from app.models.upload import MetadataDataset
        
        dataset = MetadataDataset(
            dataset_name=file.filename,
            file_type=file_extension.lstrip('.'),
            uploaded_by=current_user.username,
            version=1,
            row_count=len(df) if is_structured else None,
            column_count=len(df.columns) if is_structured else None,
            file_size_mb=validation['file_size'] / (1024 * 1024),
            file_hash=validation['file_hash'],
            status='Uploaded',
            metadata={
                "parser_metadata": parser.metadata,
                "qwen_analysis": qwen_analysis
            }
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        result['dataset_id'] = str(dataset.dataset_id)
        
        # Audit trail
        from app.models.upload import AuditTrail
        audit = AuditTrail(
            user_id=current_user.username,
            action="file_upload",
            target_entity="dataset",
            target_id=dataset.dataset_id,
            changes={
                "filename": file.filename,
                "format": file_extension,
                "is_structured": is_structured
            }
        )
        db.add(audit)
        db.commit()
        
        return result
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/upload/preview")
async def preview_file_contents(
    file: UploadFile = File(...),
    rows: int = 10,
    current_user: User = Depends(get_current_active_user)
):
    """
    Preview file contents without saving (any format)
    """
    # Create temp file
    file_extension = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    
    try:
        parser = FileParser(tmp_path)
        
        # Validate
        validation = parser.validate_file()
        if not validation['valid']:
            raise HTTPException(status_code=400, detail={
                "message": "Validation failed",
                "errors": validation['errors']
            })
        
        # Parse
        if parser.is_structured:
            data = parser.parse()
            preview = parser.get_preview(rows=rows)
            
            response = {
                "file_type": "structured",
                "format": file_extension,
                "validation": validation,
                "metadata": parser.metadata,
                "preview": preview
            }
        else:
            raw_text = parser.parse()
            
            response = {
                "file_type": "unstructured",
                "format": file_extension,
                "validation": validation,
                "metadata": parser.metadata,
                "text_preview": raw_text[:2000] if raw_text else None,
                "word_count": len(raw_text.split()) if raw_text else 0
            }
        
        return response
        
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.get("/upload/supported-formats")
async def get_supported_formats():
    """
    List all supported file formats
    """
    return {
        "structured_formats": {
            "csv": {"description": "Comma-separated values", "max_size_mb": 100},
            "xlsx": {"description": "Excel spreadsheet (new format)", "max_size_mb": 100},
            "xls": {"description": "Excel spreadsheet (old format)", "max_size_mb": 100},
            "parquet": {"description": "Apache Parquet columnar format", "max_size_mb": 100},
            "json": {"description": "JSON data (array or object)", "max_size_mb": 100},
            "xml": {"description": "XML data", "max_size_mb": 100}
        },
        "unstructured_formats": {
            "pdf": {"description": "PDF documents (with OCR)", "max_size_mb": 200},
            "docx": {"description": "Word documents", "max_size_mb": 200},
            "png": {"description": "PNG images (with OCR)", "max_size_mb": 200},
            "jpg": {"description": "JPEG images (with OCR)", "max_size_mb": 200},
            "jpeg": {"description": "JPEG images (with OCR)", "max_size_mb": 200},
            "tiff": {"description": "TIFF images (with OCR)", "max_size_mb": 200},
            "txt": {"description": "Plain text files", "max_size_mb": 200}
        },
        "ocr_enabled": get_qwen_service() is not None,
        "total_formats": 13
    }


@router.post("/upload/batch")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    dataset_type: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload multiple files at once (batch processing)
    """
    results = []
    
    for file in files:
        try:
            # Process each file
            result = await upload_multi_format_file(
                file=file,
                dataset_type=dataset_type,
                current_user=current_user,
                db=db
            )
            results.append({
                "filename": file.filename,
                "status": "success",
                "result": result
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "total_files": len(files),
        "successful": sum(1 for r in results if r['status'] == 'success'),
        "failed": sum(1 for r in results if r['status'] == 'failed'),
        "results": results
    }
