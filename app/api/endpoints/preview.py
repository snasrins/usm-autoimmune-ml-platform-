"""
Data Preview API Endpoints
Parse and preview data WITHOUT saving to database
Allows researchers to review and edit before importing
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, List, Any
import os
import shutil
import pandas as pd
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.file_parser import FileParser
from app.services.column_mapper import ColumnMapper
from app.services.staging_preprocessing_service import StagingPreprocessingService
from app.services.flexible_import_service import FlexibleImportService
from app.services.ml_data_validator import MLDataValidator
from app.services.minio_service import get_minio_service
import uuid as uuid_lib

router = APIRouter()


@router.post("/preview")
async def preview_data_file(
    file: UploadFile = File(...),
    disease_name: str = Form(...),
    disease_code: Optional[str] = Form(None),
    dataset_type: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Parse and preview patient data WITHOUT saving to database
    
    This allows researchers to review and edit data before import.
    Duplicate checking only happens during actual save.
    
    Args:
        file: Excel or CSV file
        disease_name: Disease name (e.g., 'Systemic Lupus Erythematosus')
        disease_code: ICD-10 code (e.g., 'M32.1')
        dataset_type: Dataset identifier (e.g., 'SLE', 'SJOGREN')
    
    Returns:
        Parsed data structure with column mappings for preview/editing
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
    temp_filename = f"preview_{timestamp}_{filename}"
    temp_path = os.path.join(upload_dir, temp_filename)
    
    try:
        # Save file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse file (NO DATABASE SAVE)
        file_parser = FileParser(temp_path)
        validation_result = file_parser.validate_file()
        
        if not validation_result['valid']:
            os.remove(temp_path)
            raise HTTPException(
                status_code=400,
                detail=f"File validation failed: {validation_result['error']}"
            )
        
        # Parse data
        df = file_parser.parse()
        
        # Map columns to understand data structure
        column_mapper = ColumnMapper(db)
        mapping_result = column_mapper.map_columns(df.columns.tolist())
        
        # Convert DataFrame to structured preview format
        columns = df.columns.tolist()
        rows = []
        
        for idx, row in df.iterrows():
            row_dict = {'_row_id': int(idx)}  # Add row ID for editing
            for col in columns:
                value = row[col]
                # Handle NaN and None
                if pd.isna(value):
                    row_dict[col] = None
                else:
                    row_dict[col] = str(value) if not isinstance(value, (int, float)) else value
            rows.append(row_dict)
        
        # Create column metadata
        column_info = []
        for col in columns:
            col_data = {
                'name': col,
                'type': str(df[col].dtype),
                'nullable': df[col].isna().any(),
                'unique_count': df[col].nunique()
            }
            
            # Add mapping info if available
            if col in mapping_result['mapped']:
                col_data['mapped_to'] = mapping_result['mapped'][col]['test_code']
                col_data['confidence'] = mapping_result['mapped'][col]['confidence']
            elif col in mapping_result['unmapped']:
                col_data['mapped_to'] = None
                col_data['requires_mapping'] = True
            
            column_info.append(col_data)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return {
            'success': True,
            'filename': filename,
            'preview_id': temp_filename.replace('preview_', '').replace(f'_{filename}', ''),
            'row_count': len(rows),
            'column_count': len(columns),
            'columns': column_info,
            'rows': rows,
            'mapping_summary': {
                'mapped_count': len(mapping_result['mapped']),
                'unmapped_count': len(mapping_result['unmapped']),
                'unmapped_columns': mapping_result['unmapped']
            },
            'metadata': {
                'disease_name': disease_name,
                'disease_code': disease_code,
                'dataset_type': dataset_type,
                'uploaded_by': current_user.id,
                'uploaded_at': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Preview failed: {str(e)}"
        )


@router.post("/import-from-preview")
async def import_from_preview(
    edited_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Import edited preview data to database
    
    This is called AFTER user reviews and edits the preview.
    Duplicate checking happens here.
    
    Args:
        edited_data: The edited data from preview with metadata
    
    Returns:
        Import results and statistics
    """
    from app.services import BatchImporter
    import uuid
    
    try:
        # Extract metadata
        metadata = edited_data.get('metadata', {})
        rows = edited_data.get('rows', [])
        columns = edited_data.get('columns', [])
        
        # Create temporary CSV from edited data
        df = pd.DataFrame(rows)
        
        # Remove _row_id column if exists
        if '_row_id' in df.columns:
            df = df.drop(columns=['_row_id'])
        
        # Save temporarily
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_path = f"/data/uploads/edited_{timestamp}.csv"
        df.to_csv(temp_path, index=False)
        
        # Import using BatchImporter
        importer = BatchImporter(db, user_id=current_user.id)
        result = importer.import_file(
            file_path=temp_path,
            disease_name=metadata.get('disease_name', 'Unknown'),
            dataset_type=metadata.get('dataset_type', 'GENERIC'),
            disease_code=metadata.get('disease_code'),
            auto_approve_tests=metadata.get('auto_approve', False)
        )
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )


# ============================================
# LAYER 5 PREPROCESSING ENDPOINTS
# Connects Data Pipeline → Preprocessing → flexible_dataset_wide → ML Pipeline
# ============================================

@router.get("/preview/{session_id}/quality")
async def get_preprocessing_quality_report(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get data quality report for staging session
    
    Used by Layer 5 Data Cleaning interface to show quality metrics
    before applying preprocessing operations.
    
    Args:
        session_id: Preview session UUID
    
    Returns:
        Quality metrics: missing values, duplicates, outliers, quality score
    """
    try:
        session_uuid = uuid_lib.UUID(session_id)
        preprocessing_service = StagingPreprocessingService(db)
        report = preprocessing_service.get_quality_report(session_uuid)
        
        return report
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid session ID: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality report failed: {str(e)}")


@router.get("/preview/{session_id}/problematic-rows")
async def get_problematic_rows(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get actual problematic rows for interactive cleaning
    
    Returns rows with issues (missing values, duplicates, outliers) 
    including row details, affected columns, and data preview.
    
    Args:
        session_id: Preview session UUID
    
    Returns:
        List of problematic rows with issue details
    """
    try:
        session_uuid = uuid_lib.UUID(session_id)
        preprocessing_service = StagingPreprocessingService(db)
        problematic_rows = preprocessing_service.get_problematic_rows(session_uuid)
        
        return {"rows": problematic_rows}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid session ID: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch problematic rows: {str(e)}")


@router.post("/preview/{session_id}/clean-selected")
async def clean_selected_rows(
    session_id: str,
    config: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Clean selected rows based on user selection
    
    Applies cleaning operations only to specified rows, allowing
    user to selectively fix data quality issues.
    
    Args:
        session_id: Preview session UUID
        config: {
            row_ids: List[int],
            method: str (for missing values),
            outlier_method: str
        }
    
    Returns:
        Operation summary with rows cleaned count
    """
    try:
        session_uuid = uuid_lib.UUID(session_id)
        preprocessing_service = StagingPreprocessingService(db)
        
        result = preprocessing_service.clean_selected_rows(
            session_uuid,
            row_ids=config.get("row_ids", []),
            method=config.get("method", "median"),
            outlier_method=config.get("outlier_method", "cap")
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Selective cleaning failed: {str(e)}")


@router.post("/preview/{session_id}/preprocess/missing-values")
async def preprocess_missing_values(
    session_id: str,
    method: str = 'mean',
    threshold: float = 0.5,
    columns: Optional[List[str]] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Handle missing values in staging data
    
    Applies imputation to import_preview_staging JSONB data in-place.
    Updates staging rows, then user can preview changes before saving
    to flexible_dataset_wide.
    
    Args:
        session_id: Preview session UUID
        method: 'mean', 'median', 'mode', 'ffill', 'bfill', 'drop'
        threshold: Drop columns with missing % above this (0.0-1.0)
        columns: Specific columns to process (None = all)
    
    Returns:
        Before/after statistics and operation report
    """
    try:
        session_uuid = uuid_lib.UUID(session_id)
        preprocessing_service = StagingPreprocessingService(db)
        
        result = preprocessing_service.handle_missing_values(
            session_uuid,
            method=method,
            threshold=threshold,
            columns=columns
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Missing value handling failed: {str(e)}")


@router.post("/preview/{session_id}/preprocess/duplicates")
async def preprocess_remove_duplicates(
    session_id: str,
    keep_first: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove duplicate rows from staging data
    
    Args:
        session_id: Preview session UUID
        keep_first: Keep first occurrence (True) or last (False)
    
    Returns:
        Duplicates removed count and statistics
    """
    try:
        session_uuid = uuid_lib.UUID(session_id)
        preprocessing_service = StagingPreprocessingService(db)
        
        result = preprocessing_service.remove_duplicates(
            session_uuid,
            keep_first=keep_first
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Duplicate removal failed: {str(e)}")


@router.post("/preview/{session_id}/preprocess/outliers")
async def preprocess_handle_outliers(
    session_id: str,
    method: str = 'iqr',
    threshold: float = 1.5,
    columns: Optional[List[str]] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Detect and handle outliers in staging data
    
    Args:
        session_id: Preview session UUID
        method: 'iqr' or 'zscore'
        threshold: IQR multiplier (1.5=mild, 3=extreme) or Z-score value
        columns: Specific columns (None = all numeric)
    
    Returns:
        Outliers detected and handled count
    """
    try:
        session_uuid = uuid_lib.UUID(session_id)
        preprocessing_service = StagingPreprocessingService(db)
        
        result = preprocessing_service.handle_outliers(
            session_uuid,
            method=method,
            threshold=threshold,
            columns=columns
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Outlier handling failed: {str(e)}")


@router.post("/preview/{session_id}/preprocess/aggregate-patients")
async def preprocess_aggregate_patients(
    session_id: str,
    patient_id_column: str = 'patient_id',
    strategy: str = 'latest',
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Consolidate duplicate patient records (Layer 5 - Data Quality)
    
    PURPOSE: Patient-level deduplication for data quality
    - Identifies patients with multiple records
    - Merges them into single comprehensive record
    - Applicable when dataset has duplicate patient entries
    
    Args:
        session_id: Preview session UUID
        patient_id_column: Column containing patient identifier (default: 'patient_id')
        strategy: Aggregation strategy
            - 'latest': Keep most recent record (by date columns)
            - 'most_complete': Keep record with fewest missing values
            - 'merge': Combine non-null values from all records
    
    Returns:
        Aggregation report with before/after stats
    """
    try:
        session_uuid = uuid_lib.UUID(session_id)
        preprocessing_service = StagingPreprocessingService(db)
        
        result = preprocessing_service.aggregate_patient_records(
            session_uuid,
            patient_id_column=patient_id_column,
            aggregation_strategy=strategy
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Patient aggregation failed: {str(e)}")



@router.post("/preview/{session_id}/preprocess/normalize")
async def preprocess_normalize_data(
    session_id: str,
    method: str = 'standard',
    columns: Optional[List[str]] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Normalize numeric columns in staging data
    
    Args:
        session_id: Preview session UUID
        method: 'standard' (z-score), 'minmax' (0-1), 'robust' (median/IQR)
        columns: Specific columns (None = all numeric)
    
    Returns:
        Normalization statistics and ranges
    """
    try:
        session_uuid = uuid_lib.UUID(session_id)
        preprocessing_service = StagingPreprocessingService(db)
        
        result = preprocessing_service.normalize_data(
            session_uuid,
            method=method,
            columns=columns
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Normalization failed: {str(e)}")


@router.get("/preview/{session_id}/preview")
async def get_preprocessing_preview(
    session_id: str,
    rows: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get preview of staging data after preprocessing
    
    Shows current state of data in import_preview_staging
    after any preprocessing operations have been applied.
    
    Args:
        session_id: Preview session UUID
        rows: Number of rows to return
    
    Returns:
        Preview data with current statistics
    """
    try:
        session_uuid = uuid_lib.UUID(session_id)
        preprocessing_service = StagingPreprocessingService(db)
        
        preview = preprocessing_service.get_before_after_preview(
            session_uuid,
            rows=rows
        )
        
        return preview
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


@router.post("/preview/{session_id}/save-preprocessed")
async def save_preprocessed_to_wide_table(
    session_id: str,
    dataset_type: str,
    dataset_source: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Save preprocessed staging data to flexible_dataset_wide
    
    This completes the Layer 5 preprocessing flow:
    import_preview_staging → Apply Preprocessing → Update staging →
    Save to flexible_dataset_wide → ML loads preprocessed data
    
    Args:
        session_id: Preview session UUID
        dataset_type: Dataset classification (e.g., 'SLE', 'Sjogren')
        dataset_source: Source description
    
    Returns:
        Import statistics and batch ID
    """
    try:
        session_uuid = uuid_lib.UUID(session_id)
        
        # Create preprocessing service instance to get metadata
        preprocessing_service = StagingPreprocessingService(db)
        preprocessing_metadata = preprocessing_service.get_preprocessing_metadata()
        
        # Use FlexibleImportService to save to wide table
        import_service = FlexibleImportService(db, user_id=current_user.id)
        result = import_service.import_from_staging(
            session_id=session_uuid,
            dataset_source=dataset_source or f"Preprocessed Layer 5 - {datetime.now().strftime('%Y-%m-%d')}",
            preprocessing_metadata=preprocessing_metadata
        )
        
        # ========================================
        # SAVE PREPROCESSED DATA TO MINIO
        # ========================================
        try:
            # Get the saved data from wide table
            from app.models.flexible_dataset import FlexibleDatasetWide
            batch_uuid = uuid_lib.UUID(result['batch_id'])
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
                        'dataset_type': dataset_type,
                        'dataset_source': dataset_source,
                        'preprocessing_steps': preprocessing_metadata,
                        'saved_at': datetime.now().isoformat(),
                        'saved_by': current_user.username
                    }
                )
                
                result['minio_path'] = minio_path
                print(f"✓ Preprocessed data saved to MinIO: {minio_path}")
        
        except Exception as e:
            print(f"⚠️  Warning: Failed to save to MinIO: {str(e)}")
            # Don't fail the request, just log the warning
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save to flexible_dataset_wide failed: {str(e)}")


# ============================================
# ML VALIDATION ENDPOINTS
# Flexible validation - warns but doesn't block user workflow
# ============================================

@router.get("/ml/validate/{batch_id}")
async def validate_data_for_ml_training(
    batch_id: str,
    target_column: str = 'labels_disease_classification',
    min_samples: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Validate if data in flexible_dataset_wide is ready for ML training
    
    Flexible validation approach:
    - Returns 'ready', 'warning', or 'critical' status
    - Provides recommendations without blocking workflow
    - Users can proceed with warnings (e.g., missing some labels)
    - Only blocks for critical issues (e.g., no data at all)
    
    Args:
        batch_id: Import batch UUID to validate
        target_column: ML target column (default: labels_disease_classification)
        min_samples: Recommended minimum sample size
    
    Returns:
        Validation report with status, issues, and recommendations
    """
    try:
        batch_uuid = uuid_lib.UUID(batch_id)
        
        validator = MLDataValidator(db)
        report = validator.validate_for_ml_training(
            batch_id=batch_uuid,
            target_column=target_column,
            min_samples=min_samples
        )
        
        return report
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid batch ID: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/ml/validate/dataset-type/{dataset_type}")
async def validate_dataset_type_for_ml(
    dataset_type: str,
    target_column: str = 'labels_disease_classification',
    min_samples: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Validate all records of a specific dataset type for ML training
    
    Useful for validating entire dataset categories (e.g., all SLE records)
    before starting ML model training.
    
    Args:
        dataset_type: Dataset type to validate (e.g., 'SLE', 'Sjogren')
        target_column: ML target column
        min_samples: Recommended minimum sample size
    
    Returns:
        Validation report
    """
    try:
        validator = MLDataValidator(db)
        report = validator.validate_for_ml_training(
            dataset_type=dataset_type,
            target_column=target_column,
            min_samples=min_samples
        )
        
        return report
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/ml/labeling-progress/{batch_id}")
async def get_labeling_progress(
    batch_id: str,
    target_column: str = 'labels_disease_classification',
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get labeling progress for a batch
    
    Shows which records have labels and which are still unlabeled.
    Helps users track progress when filling labels incrementally.
    
    Args:
        batch_id: Import batch UUID
        target_column: Target column to check for labels
    
    Returns:
        Progress report with labeled/unlabeled record counts and IDs
    """
    try:
        batch_uuid = uuid_lib.UUID(batch_id)
        
        validator = MLDataValidator(db)
        progress = validator.get_labeling_progress(
            batch_id=batch_uuid,
            target_column=target_column
        )
        
        return progress
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid batch ID: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get labeling progress: {str(e)}")
