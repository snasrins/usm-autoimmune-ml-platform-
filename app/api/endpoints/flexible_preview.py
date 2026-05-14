"""
Flexible Preview & Import API Endpoints
Supports 100% flexible schema - NO hardcoded database structure
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional, Any
import os
import shutil
import uuid
import io
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_active_user, require_researcher_or_admin, UserRole
from app.models.user import User
from app.services.flexible_preview_service import FlexiblePreviewService
from app.services.flexible_import_service import FlexibleImportService
from app.services.unstructured_to_tabular_service import UnstructuredToTabularService
from app.services.minio_service import get_minio_service

router = APIRouter()


@router.post("/preview/upload")
async def preview_csv_upload(
    file: UploadFile = File(...),
    dataset_type: str = Form(...),
    dataset_name: Optional[str] = Form(None),
    current_user: User = Depends(require_researcher_or_admin),
    db: Session = Depends(get_db)
):
    """
    Upload CSV for preview WITHOUT saving to database
    Returns editable preview for user review
    
    Flow: Upload → Preview → Edit → Save
    
    Args:
        file: CSV file
        dataset_type: Dataset classification (e.g., 'SLE', 'Sjogren', 'CustomDataset1')
        dataset_name: User-friendly dataset name (optional)
    
    Returns:
        session_id, schema, preview_url
    """
    # Validate file type
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Supported formats: CSV, Excel (.xlsx, .xls)"
        )
    
    # Create temp directory
    upload_dir = "/data/preview"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save uploaded file temporarily
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_filename = f"preview_{timestamp}_{file.filename}"
    temp_path = os.path.join(upload_dir, temp_filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create preview service
        preview_service = FlexiblePreviewService(db, user_id=current_user.id)
        
        # Create preview in staging
        result = preview_service.create_preview_from_csv(
            file_path=temp_path,
            dataset_type=dataset_type,
            dataset_name=dataset_name or file.filename
        )
        
        # ========================================
        # SAVE RAW FILE TO MINIO
        # ========================================
        minio_path = None
        try:
            # Read raw file bytes
            with open(temp_path, 'rb') as f:
                raw_bytes = f.read()
            
            # Save to MinIO usm-raw-data bucket
            minio_service = get_minio_service()
            minio_path = minio_service.client.put_object(
                bucket_name='usm-raw-data',
                object_name=f"session_{result['session_id']}/raw_{file.filename}",
                data=io.BytesIO(raw_bytes),
                length=len(raw_bytes),
                content_type='text/csv' if file.filename.endswith('.csv') else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                metadata={
                    'session_id': str(result['session_id']),
                    'dataset_type': dataset_type,
                    'dataset_name': dataset_name or file.filename,
                    'uploaded_by': current_user.username,
                    'uploaded_at': datetime.now().isoformat(),
                    'original_filename': file.filename
                }
            )
            
            print(f"✓ Raw data saved to MinIO: session_{result['session_id']}/raw_{file.filename}")
        
        except Exception as e:
            print(f"⚠️  Warning: Failed to save raw data to MinIO: {str(e)}")
            # Don't fail the request, just log the warning
        
        # Clean up temp file
        os.remove(temp_path)
        
        return {
            'success': True,
            **result,
            'message': 'Preview created successfully. Review and edit data before saving.',
            'minio_raw_path': f"session_{result['session_id']}/raw_{file.filename}" if minio_path else None
        }
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Preview creation failed: {str(e)}"
        )


@router.get("/preview/{session_id}")
async def get_preview(
    session_id: str,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get preview data for editing
    
    Args:
        session_id: Preview session UUID
        page: Page number (1-indexed)
        page_size: Records per page (default: 50)
    
    Returns:
        Paginated preview data with schema
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")
    
    preview_service = FlexiblePreviewService(db, user_id=current_user.id)
    
    try:
        result = preview_service.get_preview_data(
            session_id=session_uuid,
            page=page,
            page_size=page_size
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Preview session not found or expired: {str(e)}"
        )


@router.patch("/preview/{session_id}/row/{staging_id}")
async def edit_preview_row(
    session_id: str,
    staging_id: int,
    field_name: str = Body(...),
    new_value: Any = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Edit a single field in preview
    
    Args:
        session_id: Preview session UUID
        staging_id: Staging record ID
        field_name: Field to edit
        new_value: New value
    
    Returns:
        Updated row data
    """
    preview_service = FlexiblePreviewService(db, user_id=current_user.id)
    
    try:
        result = preview_service.edit_row(
            staging_id=staging_id,
            field_name=field_name,
            new_value=new_value
        )
        return {
            'success': True,
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/preview/{session_id}/row/{staging_id}")
async def delete_preview_row(
    session_id: str,
    staging_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a row from preview (soft delete)
    
    Args:
        session_id: Preview session UUID
        staging_id: Staging record ID
    
    Returns:
        Success confirmation
    """
    preview_service = FlexiblePreviewService(db, user_id=current_user.id)
    
    try:
        result = preview_service.delete_row(staging_id=staging_id)
        return {
            'success': True,
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/preview/{session_id}")
async def delete_upload_session(
    session_id: str,
    current_user: User = Depends(require_researcher_or_admin),
    db: Session = Depends(get_db)
):
    """
    Delete an entire upload session from database
    Soft deletes all staging records associated with this session
    
    Args:
        session_id: Preview session UUID to delete
    
    Returns:
        Success confirmation with number of records deleted
    """
    from app.models.flexible_data import ImportPreviewStaging
    from sqlalchemy import update
    import uuid
    
    try:
        # Validate session_id format
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        
        # Soft delete all records with this session_id (staging records)
        # Note: ImportPreviewStaging doesn't have user_id, so we just delete by session
        result = db.execute(
            update(ImportPreviewStaging)
            .where(ImportPreviewStaging.session_id == session_uuid)
            .values(is_deleted=True)
        )
        staging_deleted = result.rowcount
        
        # Also delete from saved datasets (FlexibleDatasetWide) if exists
        from app.models.flexible_data import FlexibleDatasetWide
        from sqlalchemy import delete
        
        saved_result = db.execute(
            delete(FlexibleDatasetWide)
            .where(FlexibleDatasetWide.import_batch_id == session_uuid)
        )
        saved_deleted = saved_result.rowcount
        
        db.commit()
        
        total_deleted = staging_deleted + saved_deleted
        
        # Return success even if no records found (idempotent delete)
        # Records may already be deleted or never existed
        return {
            'success': True,
            'message': f'Upload session deleted successfully',
            'deleted_rows': total_deleted,
            'staging_deleted': staging_deleted,
            'saved_deleted': saved_deleted,
            'session_id': session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@router.post("/preview/{session_id}/fill-missing")
async def auto_fill_missing(
    session_id: str,
    strategy: str = Body('median', embed=True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Auto-fill missing values in preview
    
    Args:
        session_id: Preview session UUID
        strategy: Fill strategy ('median', 'mean', 'mode', 'forward_fill')
    
    Returns:
        Fill summary
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")
    
    preview_service = FlexiblePreviewService(db, user_id=current_user.id)
    
    try:
        result = preview_service.auto_fill_missing(
            session_id=session_uuid,
            strategy=strategy
        )
        return {
            'success': True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview/{session_id}/save")
async def save_preview_to_database(
    session_id: str,
    dataset_source: Optional[str] = Body(None, embed=True),
    current_user: User = Depends(require_researcher_or_admin),
    db: Session = Depends(get_db)
):
    """
    Save previewed/edited data to permanent flexible_dataset_wide table
    This is where duplicate checking happens
    
    Args:
        session_id: Preview session UUID
        dataset_source: Source description (e.g., "Hospital USM")
    
    Returns:
        Import statistics including duplicates skipped
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")
    
    import_service = FlexibleImportService(db, user_id=current_user.id)
    
    try:
        result = import_service.import_from_staging(
            session_id=session_uuid,
            dataset_source=dataset_source
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        stats = result['statistics']
        
        # ========================================
        # SAVE TO MINIO
        # ========================================
        minio_path = None
        try:
            from app.models.flexible_data import FlexibleDatasetWide
            import pandas as pd
            
            # Get the saved data from database
            batch_uuid = uuid.UUID(result['batch_id'])
            records = db.query(FlexibleDatasetWide).filter(
                FlexibleDatasetWide.import_batch_id == batch_uuid
            ).all()
            
            if records:
                # Convert to DataFrame
                data_list = [record.data for record in records]
                df = pd.DataFrame(data_list)
                
                # Convert to CSV bytes
                csv_buffer = df.to_csv(index=False)
                csv_bytes = csv_buffer.encode('utf-8')
                
                # Save to MinIO
                minio_service = get_minio_service()
                minio_path = minio_service.save_preprocessed_data(
                    df_csv=csv_bytes,
                    batch_id=result['batch_id'],
                    stage='final_preprocessed',
                    metadata={
                        'row_count': len(df),
                        'column_count': len(df.columns),
                        'dataset_type': result['dataset_type'],
                        'dataset_source': dataset_source,
                        'saved_at': datetime.now().isoformat(),
                        'saved_by': current_user.username,
                        'records_imported': stats['imported'],
                        'duplicates_skipped': stats['duplicates_skipped']
                    }
                )
                
                print(f"✓ Preprocessed data saved to MinIO: {minio_path}")
        
        except Exception as e:
            print(f"⚠️  Warning: Failed to save to MinIO: {str(e)}")
            # Don't fail the request, just log the warning
        
        return {
            'success': True,
            'batch_id': result['batch_id'],
            'dataset_type': result['dataset_type'],
            'message': f"✅ Data saved to PostgreSQL! {stats['imported']} records imported.",
            'statistics': {
                'total_rows': stats['total_rows'],
                'imported': stats['imported'],
                'duplicates_skipped': stats['duplicates_skipped'],
                'errors': len(stats['errors'])
            },
            'errors': stats['errors'] if stats['errors'] else None,
            'minio_path': minio_path  # Add MinIO path to response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/import/direct")
async def direct_csv_import(
    file: UploadFile = File(...),
    dataset_type: str = Form(...),
    dataset_name: str = Form(...),
    dataset_source: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Direct CSV import WITHOUT preview (fast path)
    Use when data is already validated
    
    Args:
        file: CSV file
        dataset_type: Dataset classification
        dataset_name: User-friendly name
        dataset_source: Source description
    
    Returns:
        Import statistics
    """
    # Validate file type
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Supported formats: CSV, Excel (.xlsx, .xls)"
        )
    
    # Create temp directory
    upload_dir = "/data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save uploaded file temporarily
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_filename = f"import_{timestamp}_{file.filename}"
    temp_path = os.path.join(upload_dir, temp_filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Direct import
        import_service = FlexibleImportService(db, user_id=current_user.id)
        result = import_service.direct_import_csv(
            file_path=temp_path,
            dataset_type=dataset_type,
            dataset_name=dataset_name,
            dataset_source=dataset_source
        )
        
        # Clean up temp file
        if result['success']:
            os.remove(temp_path)
        
        return result
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Direct import failed: {str(e)}"
        )


@router.post("/unstructured/convert")
async def convert_unstructured_to_preview(
    validation_id: int = Body(...),
    dataset_type: str = Body(...),
    conversion_mode: str = Body("grouped"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Convert OCR-extracted entities from unstructured pipeline
    to tabular preview format
    
    Flow: Upload PDF/IMG → OCR (validation_queue) → Convert to tabular → Preview/Edit → Save
    
    Args:
        validation_id: ID from validation_queue (after OCR processing)
        dataset_type: Dataset classification (e.g., 'SLE_OCR', 'LabReport')
        conversion_mode: 'grouped' (one row with all entities) or 'individual' (one row per entity)
    
    Returns:
        {
            'session_id': uuid,
            'dataset_type': str,
            'row_count': int,
            'conversion_mode': str,
            'message': 'Ready for preview and editing'
        }
    """
    try:
        conversion_service = UnstructuredToTabularService(db, user_id=current_user.id)
        
        result = conversion_service.convert_from_validation_queue(
            validation_id=validation_id,
            dataset_type=dataset_type,
            conversion_mode=conversion_mode
        )
        
        return {
            'success': True,
            **result,
            'message': f'✅ Converted to tabular format! {result["row_count"]} rows ready for preview.',
            'next_step': f'GET /api/v1/flexible/preview/{result["session_id"]}'
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.get("/datasets/{dataset_type}")
async def get_dataset_records(
    dataset_type: str,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get records from flexible_dataset_wide by dataset type
    Returns data in wide format (ML-ready)
    
    Args:
        dataset_type: Dataset classification
        limit: Max records to return
        offset: Pagination offset
    
    Returns:
        Dataset records with schema
    """
    from app.models.flexible_data import FlexibleDatasetWide, DatasetSchema
    
    # Get records
    query = db.query(FlexibleDatasetWide).filter(
        FlexibleDatasetWide.dataset_type == dataset_type
    )
    
    total = query.count()
    records = query.order_by(FlexibleDatasetWide.created_at.desc()).offset(offset).limit(limit).all()
    
    # Get schema
    schema = db.query(DatasetSchema).filter(
        DatasetSchema.dataset_type == dataset_type
    ).first()
    
    # Format response
    return {
        'dataset_type': dataset_type,
        'total': total,
        'limit': limit,
        'offset': offset,
        'records': [
            {
                'id': r.id,
                'record_id': r.record_id,
                'data': r.data,
                'data_quality_score': r.data_quality_score,
                'import_batch_id': str(r.import_batch_id),
                'created_at': r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ],
        'schema': schema.schema_definition if schema else None
    }


@router.get("/datasets")
async def list_dataset_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all available dataset types
    
    Returns:
        List of dataset schemas with statistics
    """
    from app.models.flexible_data import DatasetSchema
    
    schemas = db.query(DatasetSchema).filter(
        DatasetSchema.is_active == True
    ).all()
    
    return {
        'total_datasets': len(schemas),
        'datasets': [
            {
                'dataset_type': s.dataset_type,
                'dataset_name': s.dataset_name,
                'description': s.dataset_description,
                'record_count': s.record_count,
                'schema_version': s.schema_version,
                'last_import_date': s.last_import_date.isoformat() if s.last_import_date else None,
                'created_at': s.created_at.isoformat() if s.created_at else None
            }
            for s in schemas
        ]
    }


@router.get("/recent-uploads")
async def get_recent_uploads(
    limit: int = 10,
    include_staging: bool = False,
    include_saved: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get recent uploads across ALL users for visibility
    Shows who uploaded each file with simplified display
    
    Args:
        limit: Maximum number of uploads to return (default: 10 recent uploads)
        include_staging: Include files in preview (not yet saved)
        include_saved: Include saved datasets
    
    Returns:
        List of recent uploads showing uploader name, file name, date, and record count
        Plus total count of ALL datasets (not limited)
    """
    from app.models.flexible_data import ImportPreviewStaging, FlexibleDatasetWide
    from app.models.user import User as UserModel
    from sqlalchemy import desc, func, distinct
    
    uploads = []
    
    # Get TOTAL count of distinct datasets (for dashboard stats)
    total_datasets_count = 0
    if include_saved:
        total_datasets_count = db.query(
            func.count(distinct(FlexibleDatasetWide.import_batch_id))
        ).scalar() or 0
    
    # Get staging uploads (files in preview, not yet saved)
    # Note: ImportPreviewStaging doesn't have user_id column yet, so we track via service
    # For now, assume all staging uploads belong to current user
    if include_staging:
        staging_query = db.query(
            ImportPreviewStaging.session_id,
            ImportPreviewStaging.dataset_name,
            ImportPreviewStaging.dataset_type,
            ImportPreviewStaging.created_at,
            func.count(ImportPreviewStaging.staging_id).label('row_count'),
            func.count(ImportPreviewStaging.staging_id).filter(
                ImportPreviewStaging.is_edited == True
            ).label('edited_count')
        ).filter(
            ImportPreviewStaging.is_deleted == False,
            ImportPreviewStaging.expires_at > func.now()
        ).group_by(
            ImportPreviewStaging.session_id,
            ImportPreviewStaging.dataset_name,
            ImportPreviewStaging.dataset_type,
            ImportPreviewStaging.created_at
        ).order_by(
            desc(ImportPreviewStaging.created_at)
        ).limit(limit)
        
        for row in staging_query.all():
            uploads.append({
                'id': str(row.session_id),
                'file_name': row.dataset_name or 'Unnamed Dataset',
                'dataset_type': row.dataset_type or 'General',
                'uploaded_by': current_user.full_name or current_user.username,
                'uploaded_by_id': current_user.id,
                'uploaded_at': row.created_at.isoformat() if row.created_at else None,
                'file_type': 'CSV/Excel',
                'size': None,
                'row_count': row.row_count,
                'status': 'preview',
                'ml_prep_status': 'not_started',
                'is_from_preprocessing': True,
                'is_owner': True  # Staging files belong to current user
            })
    
    # Get saved datasets - JOIN with users table to get actual uploader
    if include_saved:
        saved_query = db.query(
            FlexibleDatasetWide.import_batch_id,
            FlexibleDatasetWide.dataset_name,
            FlexibleDatasetWide.dataset_type,
            FlexibleDatasetWide.dataset_source,
            FlexibleDatasetWide.import_method,
            FlexibleDatasetWide.created_at,
            FlexibleDatasetWide.created_by.label('uploader_id'),
            UserModel.full_name.label('uploader_name'),
            UserModel.username.label('uploader_username'),
            func.count(FlexibleDatasetWide.id).label('row_count')
        ).outerjoin(
            UserModel,
            FlexibleDatasetWide.created_by == UserModel.id
        ).group_by(
            FlexibleDatasetWide.import_batch_id,
            FlexibleDatasetWide.dataset_name,
            FlexibleDatasetWide.dataset_type,
            FlexibleDatasetWide.dataset_source,
            FlexibleDatasetWide.import_method,
            FlexibleDatasetWide.created_at,
            FlexibleDatasetWide.created_by,
            UserModel.full_name,
            UserModel.username
        ).order_by(
            desc(FlexibleDatasetWide.created_at)
        ).limit(limit)
        
        for row in saved_query.all():
            # Determine file type from import method
            file_type = 'CSV/Excel'
            if row.import_method == 'ocr_processed':
                file_type = 'PDF/Image'
            elif row.import_method == 'api_import':
                file_type = 'API Import'
            
            # Get uploader name - ONLY use actual uploader, not current user
            if row.uploader_name or row.uploader_username:
                uploader_name = row.uploader_name or row.uploader_username
                uploader_id = row.uploader_id
            else:
                # No user found - data imported before user tracking
                uploader_name = 'Unknown User'
                uploader_id = None
            
            # Format date simply (YYYY-MM-DD HH:MM)
            if row.created_at:
                uploaded_date = row.created_at.strftime('%Y-%m-%d %H:%M')
            else:
                uploaded_date = 'Unknown'
            
            uploads.append({
                'id': str(row.import_batch_id),
                'file_name': row.dataset_name or 'Unnamed Dataset',
                'uploaded_by': uploader_name,
                'uploaded_at': row.created_at.isoformat() if row.created_at else None,
                'file_type': file_type,
                'row_count': row.row_count,
                'status': 'saved',
                'ml_prep_status': 'ready',  # Saved files are ready for ML prep
                'is_owner': uploader_id == current_user.id if uploader_id else False
            })
    
    # Sort all uploads by date (most recent first)
    uploads_sorted = sorted(
        uploads, 
        key=lambda x: x.get('uploaded_at') or '', 
        reverse=True
    )[:limit]
    
    return {
        'uploads': uploads_sorted,
        'total': total_datasets_count,  # Total count of ALL datasets (not limited)
        'returned': len(uploads_sorted),  # Number of uploads returned in this response
        'limit': limit
    }


@router.get("/saved-dataset/{batch_id}/preview")
async def get_saved_dataset_preview(
    batch_id: str,
    page: int = 1,
    page_size: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get preview data from a SAVED dataset (FlexibleDatasetWide table)
    Used for EDA and data exploration of finalized datasets
    
    Args:
        batch_id: Import batch ID (UUID)
        page: Page number (1-indexed)
        page_size: Records per page (default: 100)
    
    Returns:
        Paginated data with schema matching preview format
    """
    from app.models.flexible_data import FlexibleDatasetWide
    from sqlalchemy import func
    
    try:
        batch_uuid = uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid batch_id format")
    
    # Get total row count
    total_rows = db.query(func.count(FlexibleDatasetWide.id)).filter(
        FlexibleDatasetWide.import_batch_id == batch_uuid
    ).scalar() or 0
    
    if total_rows == 0:
        raise HTTPException(status_code=404, detail="Dataset not found or empty")
    
    # Calculate pagination
    total_pages = (total_rows + page_size - 1) // page_size
    offset = (page - 1) * page_size
    
    # Fetch paginated rows
    rows_query = db.query(FlexibleDatasetWide).filter(
        FlexibleDatasetWide.import_batch_id == batch_uuid
    ).order_by(FlexibleDatasetWide.id).offset(offset).limit(page_size)
    
    rows = []
    schema = {}
    columns = []
    
    for row in rows_query:
        if row.data:
            # Extract columns from first row
            if not columns:
                columns = list(row.data.keys())
                # Build schema from row data types
                for col in columns:
                    value = row.data.get(col)
                    if isinstance(value, (int, float)):
                        schema[col] = 'numeric'
                    elif isinstance(value, bool):
                        schema[col] = 'boolean'
                    else:
                        schema[col] = 'text'
            
            rows.append({
                'staging_id': row.id,  # Use FlexibleDatasetWide.id as surrogate staging_id
                'data': row.data
            })
    
    return {
        'session_id': str(batch_uuid),
        'total_rows': total_rows,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'rows': rows,
        'schema': schema
    }

