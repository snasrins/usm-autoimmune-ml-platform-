"""
EDA (Exploratory Data Analysis) API Endpoints
USMA-33: Develop EDA platform
USMA-22-26: Data preprocessing pipeline
USMA-32: Automated data processing
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Query, Body
from sqlalchemy.orm import Session, attributes
from sqlalchemy.orm.attributes import flag_modified
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import os
import hashlib
import json
import uuid as uuid_lib
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.dataset import Dataset, EDAReport
from app.models.flexible_data import FlexibleDatasetWide, ImportPreviewStaging
from app.services.preprocessing import DataPreprocessor
from app.services.eda_analyzer import EDAAnalyzer
from app.services.minio_service import get_minio_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def clean_nan_values(obj):
    """
    Recursively convert NaN, Infinity, and -Infinity to None for JSON compliance.
    PostgreSQL JSONB and JSON encoder cannot handle these values.
    """
    if isinstance(obj, dict):
        return {key: clean_nan_values(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    elif pd.isna(obj):
        return None
    return obj


def ensure_dict(data):
    """
    Ensure data is a dict. Handles None, string JSON, and existing dicts.
    """
    if data is None:
        return {}
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            # json.loads("null") returns None, so handle that
            return parsed if isinstance(parsed, dict) else {}
        except:
            return {}
    if isinstance(data, dict):
        return data
    return {}


# ============================================
# DATA UPLOAD & PREVIEW
# ============================================

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload dataset for EDA analysis
    Supports CSV, Excel (xlsx, xls)
    """
    # Validate file type
    allowed_extensions = ['.csv', '.xlsx', '.xls']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Create upload directory
    upload_dir = "/data/eda_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stored_filename = f"{current_user.id}_{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, stored_filename)
    
    # Save file
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Calculate file hash
        file_hash = hashlib.sha256(contents).hexdigest()
        file_size = len(contents)
        
        # Read and analyze dataset
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Get column information
        columns_info = []
        for col in df.columns:
            columns_info.append({
                "name": col,
                "dtype": str(df[col].dtype),
                "nullable": bool(df[col].isnull().any()),
                "unique_count": int(df[col].nunique())
            })
        
        # Quick data quality check
        preprocessor = DataPreprocessor()
        quality_report = preprocessor.analyze_data_quality(df)
        
        # Create dataset record
        dataset = Dataset(
            name=name,
            description=description,
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size_bytes=file_size,
            file_hash=file_hash,
            row_count=len(df),
            column_count=len(df.columns),
            columns=columns_info,
            dataset_stats=quality_report,
            missing_percentage=quality_report["missing_values"]["missing_percentage"],
            duplicate_rows=quality_report["duplicates"]["duplicate_rows"],
            preprocessing_status='raw',
            uploaded_by=current_user.id
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        return {
            "success": True,
            "message": "Dataset uploaded successfully",
            "dataset": {
                "id": dataset.id,
                "name": dataset.name,
                "rows": dataset.row_count,
                "columns": dataset.column_count,
                "size_mb": round(file_size / 1024**2, 2),
                "missing_percentage": dataset.missing_percentage,
                "duplicate_rows": dataset.duplicate_rows
            },
            "quality_summary": {
                "missing_values": quality_report["missing_values"]["total_missing"],
                "duplicate_rows": quality_report["duplicates"]["duplicate_rows"],
                "columns_with_missing": len(quality_report["missing_values"]["columns_with_missing"])
            }
        }
    
    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        
        logger.error(f"Dataset upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload dataset: {str(e)}"
        )


@router.get("/datasets")
async def list_datasets(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """List all uploaded datasets for current user"""
    datasets = db.query(Dataset).filter(
        Dataset.uploaded_by == current_user.id,
        Dataset.is_active == True,
        Dataset.is_deleted == False
    ).offset(skip).limit(limit).all()
    
    return {
        "total": len(datasets),
        "datasets": [
            {
                "id": ds.id,
                "name": ds.name,
                "description": ds.description,
                "rows": ds.row_count,
                "columns": ds.column_count,
                "size_mb": round(ds.file_size_bytes / 1024**2, 2) if ds.file_size_bytes else 0,
                "missing_percentage": ds.missing_percentage,
                "preprocessing_status": ds.preprocessing_status,
                "uploaded_at": ds.upload_timestamp.isoformat() if ds.upload_timestamp else None
            }
            for ds in datasets
        ]
    }


@router.get("/datasets/{dataset_id}/preview")
async def preview_dataset(
    dataset_id: int,
    rows: int = Query(default=10, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Preview first N rows of dataset
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.uploaded_by == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # Read dataset
        if dataset.original_filename.endswith('.csv'):
            df = pd.read_csv(dataset.file_path, nrows=rows)
        else:
            df = pd.read_excel(dataset.file_path, nrows=rows)
        
        # Convert to records
        preview_data = df.head(rows).to_dict(orient='records')
        
        # Convert NaN to None for JSON serialization
        for record in preview_data:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
        
        return {
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "total_rows": dataset.row_count,
            "preview_rows": len(preview_data),
            "columns": dataset.columns,
            "data": preview_data
        }
    
    except Exception as e:
        logger.error(f"Failed to preview dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to preview dataset: {str(e)}")


# ============================================
# DATA QUALITY & ANALYSIS
# ============================================

@router.get("/datasets/{dataset_id}/quality")
async def analyze_data_quality(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    USMA-26: Comprehensive data quality analysis
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.uploaded_by == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Return cached stats if available
    if dataset.dataset_stats:
        return {
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "quality_report": dataset.dataset_stats
        }
    
    # Generate fresh quality report
    try:
        if dataset.original_filename.endswith('.csv'):
            df = pd.read_csv(dataset.file_path)
        else:
            df = pd.read_excel(dataset.file_path)
        
        preprocessor = DataPreprocessor()
        quality_report = preprocessor.analyze_data_quality(df)
        
        # Update dataset with stats
        dataset.dataset_stats = quality_report
        db.commit()
        
        return {
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "quality_report": quality_report
        }
    
    except Exception as e:
        logger.error(f"Failed to analyze data quality: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data quality analysis failed: {str(e)}")


@router.get("/datasets/{dataset_id}/summary")
async def get_summary_statistics(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    USMA-33: Generate summary statistics for dataset
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.uploaded_by == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # Load dataset
        if dataset.original_filename.endswith('.csv'):
            df = pd.read_csv(dataset.file_path)
        else:
            df = pd.read_excel(dataset.file_path)
        
        # Generate summary
        analyzer = EDAAnalyzer()
        summary = analyzer.generate_summary_statistics(df)
        
        # Save as EDA report
        report = EDAReport(
            dataset_id=dataset.id,
            report_type='summary',
            generated_by=current_user.id,
            analysis_results=summary
        )
        db.add(report)
        db.commit()
        
        # ========================================
        # SAVE EDA SUMMARY TO MINIO
        # ========================================
        try:
            import json
            
            # Convert summary to JSON
            summary_json = json.dumps(summary, indent=2).encode('utf-8')
            
            # Save to MinIO
            minio_service = get_minio_service()
            minio_path = minio_service.save_eda_artifact(
                artifact_data=summary_json,
                batch_id=str(dataset.id),
                artifact_name='summary_statistics.json',
                artifact_type='json',
                metadata={
                    'dataset_id': dataset.id,
                    'dataset_name': dataset.name,
                    'report_type': 'summary',
                    'generated_at': datetime.now().isoformat(),
                    'generated_by': current_user.username
                }
            )
            
            logger.info(f"✓ EDA summary saved to MinIO: {minio_path}")
        
        except Exception as minio_error:
            logger.warning(f"⚠️  Failed to save EDA summary to MinIO: {minio_error}")
        
        return {
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "summary_statistics": summary
        }
    
    except Exception as e:
        logger.error(f"Failed to generate summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.get("/datasets/{dataset_id}/univariate/{column}")
async def analyze_univariate(
    dataset_id: int,
    column: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    USMA-33: Univariate analysis for specific column
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.uploaded_by == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # Load dataset
        if dataset.original_filename.endswith('.csv'):
            df = pd.read_csv(dataset.file_path)
        else:
            df = pd.read_excel(dataset.file_path)
        
        # Generate analysis
        analyzer = EDAAnalyzer()
        analysis = analyzer.generate_univariate_analysis(df, column)
        
        # Save report
        report = EDAReport(
            dataset_id=dataset.id,
            report_type='univariate',
            generated_by=current_user.id,
            analysis_results={"column": column, "analysis": analysis}
        )
        db.add(report)
        db.commit()
        
        return analysis
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Univariate analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/datasets/{dataset_id}/bivariate")
async def analyze_bivariate(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    USMA-33: Bivariate analysis (correlations)
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.uploaded_by == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # Load dataset
        if dataset.original_filename.endswith('.csv'):
            df = pd.read_csv(dataset.file_path)
        else:
            df = pd.read_excel(dataset.file_path)
        
        # Generate analysis
        analyzer = EDAAnalyzer()
        analysis = analyzer.generate_bivariate_analysis(df)
        
        # Save report
        report = EDAReport(
            dataset_id=dataset.id,
            report_type='bivariate',
            generated_by=current_user.id,
            analysis_results=analysis
        )
        db.add(report)
        db.commit()
        
        return {
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "bivariate_analysis": analysis
        }
    
    except Exception as e:
        logger.error(f"Bivariate analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ============================================
# DATA PREPROCESSING
# ============================================

@router.post("/datasets/{batch_id}/preprocess/missing-values")
async def handle_missing_values(
    batch_id: str,
    strategy: Dict[str, str] = None,
    threshold: float = Query(default=0.5, ge=0, le=1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    USMA-22: Handle missing values in dataset
    Works with flexible_dataset_wide (UUID batch) or staging data
    strategy: Dict mapping column names to imputation strategies
              Options: 'mean', 'median', 'mode', 'ffill', 'bfill', 'drop'
    threshold: Drop columns with missing % above this threshold
    """
    try:
        batch_uuid = uuid_lib.UUID(batch_id)
        use_staging = False
        
        # First try saved data (FlexibleDatasetWide)
        records = db.query(FlexibleDatasetWide).filter(
            FlexibleDatasetWide.import_batch_id == batch_uuid
        ).all()
        
        # If no saved data, try staging (ImportPreviewStaging)
        if not records:
            records = db.query(ImportPreviewStaging).filter(
                ImportPreviewStaging.session_id == batch_uuid,
                ImportPreviewStaging.is_deleted == False
            ).all()
            use_staging = True
        
        if not records:
            raise HTTPException(status_code=404, detail="No records found. Make sure the dataset has been uploaded.")
        
        # Extract data from JSONB
        data_rows = []
        for record in records:
            jsonb_data = ensure_dict(record.row_data if use_staging else record.data)
            if jsonb_data:
                flat_data = {}
                for key, value in jsonb_data.items():
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            flat_key = f"{key}.{subkey}"
                            flat_data[flat_key] = subvalue
                    else:
                        flat_data[key] = value
                data_rows.append(flat_data)
        
        if not data_rows:
            raise HTTPException(status_code=400, detail="No data found in records")
        
        df = pd.DataFrame(data_rows)
        
        # Apply preprocessing
        preprocessor = DataPreprocessor()
        df_processed, report = preprocessor.handle_missing_values(df, strategy, threshold)
        
        # Update records with imputed data
        for idx, record in enumerate(records):
            if idx < len(df_processed):
                row_data_dict = df_processed.iloc[idx].to_dict()
                
                # Ensure we have a dict to work with
                if use_staging:
                    jsonb_field = ensure_dict(record.row_data)
                else:
                    jsonb_field = ensure_dict(record.data)
                
                for key, value in row_data_dict.items():
                    if '.' in key:
                        parent, child = key.split('.', 1)
                        if parent not in jsonb_field:
                            jsonb_field[parent] = {}
                        jsonb_field[parent][child] = value
                    else:
                        jsonb_field[key] = value
                
                # Clean NaN/Inf values and assign back
                if use_staging:
                    record.row_data = clean_nan_values(jsonb_field)
                    flag_modified(record, 'row_data')
                else:
                    record.data = clean_nan_values(jsonb_field)
                    flag_modified(record, 'data')
        
        db.commit()
        
        return {
            "success": True,
            "batch_id": batch_id,
            "records_processed": len(records),
            "report": clean_nan_values(report),
            "new_shape": {
                "rows": len(df_processed),
                "columns": len(df_processed.columns)
            },
            "data_source": "staging" if use_staging else "saved"
        }
    
    except Exception as e:
        logger.error(f"Missing value handling failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Preprocessing failed: {str(e)}")


@router.post("/datasets/{dataset_id}/preprocess/encode")
async def encode_categorical(
    dataset_id: int,
    encoding_type: str = Query(default='auto', regex='^(auto|label|onehot)$'),
    columns: Optional[List[str]] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    USMA-24: Encode categorical variables
    encoding_type: 'auto', 'label', 'onehot'
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.uploaded_by == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # Load dataset
        if dataset.original_filename.endswith('.csv'):
            df = pd.read_csv(dataset.file_path)
        else:
            df = pd.read_excel(dataset.file_path)
        
        # Apply encoding
        preprocessor = DataPreprocessor()
        df_processed, report = preprocessor.encode_categorical_variables(df, encoding_type, columns)
        
        # Save processed dataset
        processed_filename = dataset.stored_filename.replace('.', '_encoded.')
        processed_path = dataset.file_path.replace(dataset.stored_filename, processed_filename)
        
        if processed_filename.endswith('.csv'):
            df_processed.to_csv(processed_path, index=False)
        else:
            df_processed.to_excel(processed_path, index=False)
        
        return {
            "success": True,
            "dataset_id": dataset.id,
            "encoding_report": report
        }
    
    except Exception as e:
        logger.error(f"Categorical encoding failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Encoding failed: {str(e)}")


@router.post("/datasets/{batch_id}/preprocess/normalize")
async def normalize_data(
    batch_id: str,
    method: str = Query(default='standard', regex='^(standard|minmax|robust)$'),
    columns: Optional[List[str]] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    USMA-25: Normalize/standardize numeric data
    method: 'standard' (z-score), 'minmax', 'robust'
    Works with flexible_dataset_wide (UUID batch) or staging data
    """
    try:
        # Query flexible_dataset_wide records or staging
        batch_uuid = uuid_lib.UUID(batch_id)
        use_staging = False
        
        records = db.query(FlexibleDatasetWide).filter(
            FlexibleDatasetWide.import_batch_id == batch_uuid
        ).all()
        
        if not records:
            records = db.query(ImportPreviewStaging).filter(
                ImportPreviewStaging.session_id == batch_uuid,
                ImportPreviewStaging.is_deleted == False
            ).all()
            use_staging = True
        
        if not records:
            raise HTTPException(status_code=404, detail="No records found. Make sure the dataset has been uploaded.")
        
        # Extract numeric data from JSONB
        data_rows = []
        for record in records:
            jsonb_data = ensure_dict(record.row_data if use_staging else record.data)
            if jsonb_data:
                flat_data = {}
                # Flatten nested JSONB structure
                for key, value in jsonb_data.items():
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            flat_key = f"{key}.{subkey}"
                            if isinstance(subvalue, (int, float)) and subvalue is not None:
                                flat_data[flat_key] = subvalue
                    elif isinstance(value, (int, float)) and value is not None:
                        flat_data[key] = value
                data_rows.append(flat_data)
        
        if not data_rows:
            raise HTTPException(status_code=400, detail="No numeric data found in records")
        
        # Convert to DataFrame
        df = pd.DataFrame(data_rows)
        
        # Apply normalization
        preprocessor = DataPreprocessor()
        df_processed, report = preprocessor.normalize_data(df, method, columns)
        
        # Update records with normalized data
        for idx, record in enumerate(records):
            if idx < len(df_processed):
                row_data_dict = df_processed.iloc[idx].to_dict()
                
                # Ensure we have a dict to work with
                if use_staging:
                    jsonb_field = ensure_dict(record.row_data)
                else:
                    jsonb_field = ensure_dict(record.data)
                
                # Update JSONB with normalized values
                for key, value in row_data_dict.items():
                    if '.' in key:
                        parent, child = key.split('.', 1)
                        if parent not in jsonb_field:
                            jsonb_field[parent] = {}
                        jsonb_field[parent][child] = float(value) if pd.notna(value) else None
                    else:
                        jsonb_field[key] = float(value) if pd.notna(value) else None
                
                # Clean NaN/Inf values and assign back
                if use_staging:
                    record.row_data = clean_nan_values(jsonb_field)
                    flag_modified(record, 'row_data')
                else:
                    record.data = clean_nan_values(jsonb_field)
                    flag_modified(record, 'data')
        
        db.commit()
        
        return {
            "success": True,
            "batch_id": batch_id,
            "records_processed": len(records),
            "normalization_report": clean_nan_values(report),
            "data_source": "staging" if use_staging else "saved"
        }
    
    except Exception as e:
        logger.error(f"Normalization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Normalization failed: {str(e)}")


@router.get("/datasets/{dataset_id}/outliers")
async def detect_outliers(
    dataset_id: int,
    method: str = Query(default='iqr', regex='^(iqr|z-score)$'),
    threshold: float = Query(default=1.5, gt=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    USMA-23: Detect outliers in dataset
    method: 'iqr' or 'z-score'
    threshold: IQR multiplier (1.5) or z-score threshold (3)
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.uploaded_by == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # Load dataset
        if dataset.original_filename.endswith('.csv'):
            df = pd.read_csv(dataset.file_path)
        else:
            df = pd.read_excel(dataset.file_path)
        
        # Detect outliers
        preprocessor = DataPreprocessor()
        _, report = preprocessor.detect_outliers(df, method, None, threshold)
        
        # Save as EDA report
        eda_report = EDAReport(
            dataset_id=dataset.id,
            report_type='outliers',
            generated_by=current_user.id,
            analysis_results=report
        )
        db.add(eda_report)
        db.commit()
        
        return {
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "outlier_report": report
        }
    
    except Exception as e:
        logger.error(f"Outlier detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Outlier detection failed: {str(e)}")


@router.post("/datasets/{batch_id}/preprocess/winsorize")
async def winsorize_data(
    batch_id: str,
    lower_percentile: float = Query(default=0.01, ge=0.0, le=0.1),
    upper_percentile: float = Query(default=0.99, ge=0.9, le=1.0),
    columns: Optional[List[str]] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Winsorize outliers by capping at specified percentiles
    Works with flexible_dataset_wide (UUID batch) or staging data
    """
    try:
        batch_uuid = uuid_lib.UUID(batch_id)
        use_staging = False
        
        records = db.query(FlexibleDatasetWide).filter(
            FlexibleDatasetWide.import_batch_id == batch_uuid
        ).all()
        
        if not records:
            records = db.query(ImportPreviewStaging).filter(
                ImportPreviewStaging.session_id == batch_uuid,
                ImportPreviewStaging.is_deleted == False
            ).all()
            use_staging = True
        
        if not records:
            raise HTTPException(status_code=404, detail="No records found. Make sure the dataset has been uploaded.")
        
        # Extract numeric data from JSONB
        data_rows = []
        for record in records:
            jsonb_data = ensure_dict(record.row_data if use_staging else record.data)
            if jsonb_data:
                flat_data = {}
                for key, value in jsonb_data.items():
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            flat_key = f"{key}.{subkey}"
                            if isinstance(subvalue, (int, float)) and subvalue is not None:
                                flat_data[flat_key] = subvalue
                    elif isinstance(value, (int, float)) and value is not None:
                        flat_data[key] = value
                data_rows.append(flat_data)
        
        if not data_rows:
            raise HTTPException(status_code=400, detail="No numeric data found in records")
        
        df = pd.DataFrame(data_rows)
        
        # Apply winsorization
        preprocessor = DataPreprocessor()
        df_processed, report = preprocessor.winsorize_outliers(
            df, lower_percentile, upper_percentile, columns
        )
        
        # Update records with winsorized data
        for idx, record in enumerate(records):
            if idx < len(df_processed):
                row_data_dict = df_processed.iloc[idx].to_dict()
                
                # Ensure we have a dict to work with
                if use_staging:
                    jsonb_field = ensure_dict(record.row_data)
                else:
                    jsonb_field = ensure_dict(record.data)
                
                for key, value in row_data_dict.items():
                    if '.' in key:
                        parent, child = key.split('.', 1)
                        if parent not in jsonb_field:
                            jsonb_field[parent] = {}
                        jsonb_field[parent][child] = float(value) if pd.notna(value) else None
                    else:
                        jsonb_field[key] = float(value) if pd.notna(value) else None
                
                # Clean NaN/Inf values and assign back
                if use_staging:
                    record.row_data = clean_nan_values(jsonb_field)
                    flag_modified(record, 'row_data')
                else:
                    record.data = clean_nan_values(jsonb_field)
                    flag_modified(record, 'data')
        
        db.commit()
        
        return {
            "success": True,
            "batch_id": batch_id,
            "records_processed": len(records),
            "winsorization_report": clean_nan_values(report),
            "data_source": "staging" if use_staging else "saved"
        }
    
    except Exception as e:
        logger.error(f"Winsorization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Winsorization failed: {str(e)}")


@router.post("/datasets/{batch_id}/preprocess/filter-variables")
async def filter_high_missing_variables(
    batch_id: str,
    threshold: float = Query(default=0.5, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove variables (columns) with high missing data
    Works with flexible_dataset_wide (UUID batch) or staging data
    """
    try:
        batch_uuid = uuid_lib.UUID(batch_id)
        use_staging = False
        
        records = db.query(FlexibleDatasetWide).filter(
            FlexibleDatasetWide.import_batch_id == batch_uuid
        ).all()
        
        if not records:
            records = db.query(ImportPreviewStaging).filter(
                ImportPreviewStaging.session_id == batch_uuid,
                ImportPreviewStaging.is_deleted == False
            ).all()
            use_staging = True
        
        if not records:
            raise HTTPException(status_code=404, detail="No records found. Make sure the dataset has been uploaded.")
        
        # Extract data from JSONB
        data_rows = []
        for record in records:
            jsonb_data = ensure_dict(record.row_data if use_staging else record.data)
            if jsonb_data:
                flat_data = {}
                for key, value in jsonb_data.items():
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            flat_key = f"{key}.{subkey}"
                            flat_data[flat_key] = subvalue
                    else:
                        flat_data[key] = value
                data_rows.append(flat_data)
        
        if not data_rows:
            raise HTTPException(status_code=400, detail="No data found in records")
        
        df = pd.DataFrame(data_rows)
        
        # Apply variable filtration
        preprocessor = DataPreprocessor()
        df_filtered, report = preprocessor.filter_high_missing_variables(df, threshold)
        
        # Update records with filtered data (remove columns)
        removed_cols = report.get('removed_columns', [])
        for record in records:
            # Ensure we have a dict to work with
            if use_staging:
                jsonb_field = ensure_dict(record.row_data)
            else:
                jsonb_field = ensure_dict(record.data)
            
            for col in removed_cols:
                if '.' in col:
                    parent, child = col.split('.', 1)
                    if parent in jsonb_field and isinstance(jsonb_field[parent], dict):
                        jsonb_field[parent].pop(child, None)
                else:
                    jsonb_field.pop(col, None)
            
            # Clean NaN/Inf values and assign back
            if use_staging:
                record.row_data = clean_nan_values(jsonb_field)
                flag_modified(record, 'row_data')
            else:
                record.data = clean_nan_values(jsonb_field)
                flag_modified(record, 'data')
        
        db.commit()
        
        return {
            "success": True,
            "batch_id": batch_id,
            "records_processed": len(records),
            "filtration_report": clean_nan_values(report),
            "data_source": "staging" if use_staging else "saved"
        }
    
    except Exception as e:
        logger.error(f"Variable filtration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Variable filtration failed: {str(e)}")


@router.post("/datasets/{batch_id}/preprocess/complete-pipeline")
async def run_complete_preprocessing_pipeline(
    batch_id: str,
    config: Dict = Body(default={
        "filter_missing_threshold": 0.5,
        "imputation_strategy": {"default": "median"},
        "winsorize_lower": 0.01,
        "winsorize_upper": 0.99,
        "standardization_method": "standard"
    }),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Run complete preprocessing pipeline matching research methodology:
    1. Variable Filtration (>50% missing)
    2. Imputation (median/mode)
    3. Outlier Handling (winsorization)
    4. Standardization (Z-score)
    Works with flexible_dataset_wide (UUID batch) or staging data
    """
    try:
        batch_uuid = uuid_lib.UUID(batch_id)
        use_staging = False
        
        # First try saved data (FlexibleDatasetWide)
        records = db.query(FlexibleDatasetWide).filter(
            FlexibleDatasetWide.import_batch_id == batch_uuid
        ).all()
        
        # If no saved data, try staging (ImportPreviewStaging)
        if not records:
            logger.info(f"No saved data for batch {batch_id}, checking staging...")
            records = db.query(ImportPreviewStaging).filter(
                ImportPreviewStaging.session_id == batch_uuid,
                ImportPreviewStaging.is_deleted == False
            ).all()
            use_staging = True
            if records:
                logger.info(f"Using staging data: {len(records)} records")
        
        if not records:
            raise HTTPException(status_code=404, detail="No records found. Make sure the dataset has been uploaded.")
        
        logger.info(f"Preprocessing {len(records)} records (staging={use_staging})")
        
        # Extract data from JSONB - use row_data for staging, data for saved
        data_rows = []
        for record in records:
            jsonb_data = ensure_dict(record.row_data if use_staging else record.data)
            if jsonb_data:
                flat_data = {}
                for key, value in jsonb_data.items():
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            flat_key = f"{key}.{subkey}"
                            flat_data[flat_key] = subvalue
                    else:
                        flat_data[key] = value
                data_rows.append(flat_data)
        
        if not data_rows:
            raise HTTPException(status_code=400, detail="No data found in records")
        
        df = pd.DataFrame(data_rows)
        preprocessor = DataPreprocessor()
        pipeline_report = {
            "steps": [],
            "original_shape": df.shape,
            "original_columns": len(df.columns),
            "original_rows": len(df)
        }
        
        # Step 1: Variable Filtration
        df, filtration_report = preprocessor.filter_high_missing_variables(
            df, config.get("filter_missing_threshold", 0.5)
        )
        pipeline_report["steps"].append(filtration_report)
        
        # Step 2: Imputation
        df, imputation_report = preprocessor.handle_missing_values(
            df, config.get("imputation_strategy")
        )
        pipeline_report["steps"].append(imputation_report)
        
        # Step 3: Winsorization
        df, winsorize_report = preprocessor.winsorize_outliers(
            df,
            config.get("winsorize_lower", 0.01),
            config.get("winsorize_upper", 0.99)
        )
        pipeline_report["steps"].append(winsorize_report)
        
        # Step 4: Standardization
        df, standardization_report = preprocessor.normalize_data(
            df, config.get("standardization_method", "standard")
        )
        pipeline_report["steps"].append(standardization_report)
        
        # Final statistics
        pipeline_report["final_shape"] = df.shape
        pipeline_report["final_columns"] = len(df.columns)
        pipeline_report["final_rows"] = len(df)
        pipeline_report["columns_removed"] = pipeline_report["original_columns"] - pipeline_report["final_columns"]
        pipeline_report["rows_unchanged"] = len(df)
        
        # Update records with preprocessed data
        for idx, record in enumerate(records):
            if idx < len(df):
                row_data_dict = df.iloc[idx].to_dict()
                
                # Ensure we have a dict to work with
                if use_staging:
                    jsonb_field = ensure_dict(record.row_data)
                else:
                    jsonb_field = ensure_dict(record.data)
                
                for key, value in row_data_dict.items():
                    if '.' in key:
                        parent, child = key.split('.', 1)
                        if parent not in jsonb_field:
                            jsonb_field[parent] = {}
                        jsonb_field[parent][child] = value
                    else:
                        jsonb_field[key] = value
                
                # Clean NaN/Inf values and assign back
                if use_staging:
                    record.row_data = clean_nan_values(jsonb_field)
                    flag_modified(record, 'row_data')
                else:
                    record.data = clean_nan_values(jsonb_field)
                    flag_modified(record, 'data')
        
        db.commit()
        
        logger.info(
            f"Complete preprocessing pipeline finished: "
            f"{pipeline_report['original_columns']} → {pipeline_report['final_columns']} columns, "
            f"{pipeline_report['original_rows']} rows preserved"
        )
        
        return {
            "success": True,
            "batch_id": batch_id,
            "pipeline_report": clean_nan_values(pipeline_report),
            "data_source": "staging" if use_staging else "saved"
        }
    
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Preprocessing pipeline failed: {str(e)}")


@router.get("/datasets/{dataset_id}/reports")
async def get_eda_reports(
    dataset_id: int,
    report_type: Optional[str] = Query(None, regex='^(summary|univariate|bivariate|outliers)$'),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all EDA reports for a dataset
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.uploaded_by == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    query = db.query(EDAReport).filter(EDAReport.dataset_id == dataset_id)
    
    if report_type:
        query = query.filter(EDAReport.report_type == report_type)
    
    reports = query.order_by(EDAReport.generated_at.desc()).all()
    
    return {
        "dataset_id": dataset.id,
        "dataset_name": dataset.name,
        "total_reports": len(reports),
        "reports": [
            {
                "id": r.id,
                "report_type": r.report_type,
                "generated_at": r.generated_at.isoformat() if r.generated_at else None,
                "analysis_results": r.analysis_results
            }
            for r in reports
        ]
    }


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete dataset (soft delete)"""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.uploaded_by == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    dataset.is_deleted = True
    dataset.is_active = False
    db.commit()
    
    return {"success": True, "message": "Dataset deleted successfully"}
