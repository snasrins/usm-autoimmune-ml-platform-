"""
ML Bridge Service
Dedicated service to transform Data Pipeline output to ML-ready format
Handles JSONB flattening, validation, and feature preparation
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
import logging
import uuid

from app.models.flexible_data import FlexibleDatasetWide, ImportPreviewStaging
from app.services.ml_schema_validator import MLSchemaValidator
from app.services.data_provenance_service import DataProvenanceService

logger = logging.getLogger(__name__)


class MLBridgeService:
    """
    Bridge service between Data Pipeline and ML Pipeline
    
    Responsibilities:
    1. Transform flexible_dataset_wide (JSONB) → ML-ready DataFrame
    2. Validate data quality before ML consumption
    3. Handle JSONB flattening with proper type conversion
    4. Apply data cleaning for ML requirements
    5. Track provenance through transformation
    
    Benefits:
    - Clean interface between pipelines
    - Centralized validation logic
    - Reusable transformation code
    - Clear separation of concerns
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = MLSchemaValidator(db)
        self.provenance = DataProvenanceService(db)
    
    def _ensure_dict(self, data) -> Dict:
        """Ensure data is a dict. Handles None, string JSON, and existing dicts."""
        import json
        if data is None:
            return {}
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
                return parsed if isinstance(parsed, dict) else {}
            except:
                return {}
        if isinstance(data, dict):
            return data
        return {}
    
    def prepare_data_for_ml(
        self,
        import_batch_id: Optional[uuid.UUID] = None,
        dataset_type: Optional[str] = None,
        target_column: str = "labels_disease_classification",
        validate: bool = True,
        drop_unlabeled: bool = False
    ) -> Dict:
        """
        Main method: Transform data pipeline output to ML-ready format
        
        Args:
            import_batch_id: Specific batch (None = all data)
            dataset_type: Dataset type filter
            target_column: Target variable column
            validate: Whether to validate before transformation
            drop_unlabeled: Whether to drop records without labels
        
        Returns:
            Dictionary containing:
                - df: Pandas DataFrame (ML-ready)
                - target_column: Target column name
                - metadata: Transformation metadata
                - validation_report: Validation results
                - provenance: Data provenance chain
        """
        logger.info(
            f"Preparing data for ML: batch={import_batch_id}, "
            f"type={dataset_type}, target={target_column}"
        )
        
        # Step 1: Validate data quality
        validation_report = None
        if validate:
            logger.info("Step 1: Validating data quality...")
            validation_report = self.validator.validate_for_ml_training(
                import_batch_id=import_batch_id,
                dataset_type=dataset_type,
                target_column=target_column
            )
            
            if not validation_report['valid']:
                logger.error("Validation failed - cannot proceed with ML preparation")
                return {
                    'success': False,
                    'error': 'Validation failed',
                    'validation_report': validation_report
                }
            
            # Log warnings
            for warning in validation_report.get('warnings', []):
                logger.warning(f"⚠️  {warning['message']}")
        
        # Step 2: Load data from flexible_dataset_wide (saved) or staging
        logger.info("Step 2: Loading data...")
        use_staging = False
        records = []
        
        # First try saved data (FlexibleDatasetWide)
        query = self.db.query(FlexibleDatasetWide)
        if import_batch_id:
            query = query.filter(FlexibleDatasetWide.import_batch_id == import_batch_id)
        if dataset_type:
            query = query.filter(FlexibleDatasetWide.dataset_type == dataset_type)
        
        records = query.all()
        
        # If no saved data, try staging (ImportPreviewStaging)
        if not records and import_batch_id:
            logger.info("No saved data found, checking staging...")
            staging_query = self.db.query(ImportPreviewStaging).filter(
                ImportPreviewStaging.session_id == import_batch_id,
                ImportPreviewStaging.is_deleted == False
            )
            records = staging_query.all()
            use_staging = True
            if records:
                logger.info(f"Using staging data: {len(records)} records")
        
        if not records:
            logger.error("No records found in saved or staging data")
            return {
                'success': False,
                'error': 'No records found. Make sure the dataset has been uploaded.'
            }
        
        logger.info(f"Loaded {len(records)} records (staging={use_staging})")
        
        # Store source info for later
        self._use_staging = use_staging
        
        # DEBUG: Show sample of raw JSONB structure
        if records:
            raw_data = records[0].row_data if use_staging else records[0].data
            first_record_data = self._ensure_dict(raw_data)
            if first_record_data:
                sample_keys = list(first_record_data.keys())[:20]
                logger.info(f"Sample JSONB keys from first record: {sample_keys}")
                # Check if labels exist in JSONB
                if 'labels' in first_record_data:
                    logger.info(f"'labels' structure: {first_record_data['labels']}")
                if 'labels_disease_classification' in first_record_data:
                    logger.info(f"'labels_disease_classification' value: {first_record_data['labels_disease_classification']}")
        
        # Step 3: Flatten JSONB to DataFrame
        logger.info("Step 3: Flattening JSONB to DataFrame...")
        df = self._flatten_jsonb_to_dataframe(records, use_staging=use_staging)
        logger.info(f"Flattened to DataFrame: {df.shape}")
        logger.info(f"Columns in DataFrame: {list(df.columns)[:30]}...")  # Show first 30 columns
        
        # Step 3.5: Auto-detect target column if not found
        logger.info(f"Step 3.5: Checking target column: '{target_column}'")
        if target_column not in df.columns:
            logger.warning(f"⚠️  Requested target column '{target_column}' NOT found!")
            
            # Fallback options (in priority order)
            fallback_options = [
                'clinical_diagnosis_category',  # New dynamic category system
                'labels_disease_classification',  # Old flat label field
                'diagnosis_category',  # Fallback if clinical_ prefix dropped
            ]
            
            # Find first available fallback
            found_target = None
            for option in fallback_options:
                if option in df.columns and option != target_column:
                    found_target = option
                    logger.info(f"✓ Found fallback target column: '{found_target}'")
                    target_column = found_target
                    break
            
            if not found_target:
                # Last resort: look for any column with 'label' or 'category'
                candidate_cols = [c for c in df.columns if 'label' in c.lower() or 'category' in c.lower()]
                if candidate_cols:
                    logger.error(f"❌ No fallback target found! Candidates: {candidate_cols}")
                    return {
                        'success': False,
                        'error': f"Target column '{target_column}' not found. Available candidates: {candidate_cols}",
                        'metadata': {'available_columns': list(df.columns)}
                    }
                else:
                    logger.error(f"❌ No target column candidates found!")
                    return {
                        'success': False,
                        'error': f"Target column '{target_column}' not found and no fallback options available",
                        'metadata': {'available_columns': list(df.columns)}
                    }
        else:
            logger.info(f"✓ Target column '{target_column}' FOUND in DataFrame")
            # Show sample values
            if target_column in df.columns:
                logger.info(f"Target column sample values: {df[target_column].value_counts().to_dict()}")
        
        # DEBUG: Check if target column exists (legacy code)
        # NOTE: Removed old debug code - target detection now above
        
        # Step 4: Clean data for ML
        logger.info("Step 4: Cleaning data for ML...")
        df = self._clean_for_ml(df, target_column)
        logger.info(f"After cleaning: {df.shape}")
        
        # Step 5: Handle unlabeled records
        if drop_unlabeled and target_column in df.columns:
            initial_count = len(df)
            df = df[df[target_column].notna()]
            dropped = initial_count - len(df)
            if dropped > 0:
                logger.info(f"Dropped {dropped} unlabeled records")
        
        # Step 6: Get provenance chain
        logger.info("Step 5: Retrieving provenance chain...")
        provenance_chain = None
        if import_batch_id:
            provenance_chain = self.provenance.get_complete_provenance_chain(import_batch_id)
        
        # Step 7: Compile metadata
        metadata = {
            'source_table': 'flexible_dataset_wide',
            'import_batch_id': str(import_batch_id) if import_batch_id else 'all',
            'dataset_type': dataset_type or 'all',
            'original_record_count': len(records),
            'final_record_count': len(df),
            'column_count': len(df.columns),
            'target_column': target_column,
            'has_target': target_column in df.columns,
            'labeled_count': int(df[target_column].notna().sum()) if target_column in df.columns else 0,
            'unlabeled_count': int(df[target_column].isna().sum()) if target_column in df.columns else 0,
            'transformation_steps': [
                'load_from_flexible_dataset_wide',
                'flatten_jsonb',
                'clean_for_ml',
                'handle_unlabeled' if drop_unlabeled else None
            ],
            'validation_performed': validate
        }
        
        logger.info(
            f"✅ ML data preparation complete: {metadata['final_record_count']} records, "
            f"{metadata['column_count']} columns, "
            f"{metadata['labeled_count']} labeled"
        )
        
        return {
            'success': True,
            'df': df,
            'target_column': target_column,
            'metadata': metadata,
            'validation_report': validation_report,
            'provenance': provenance_chain
        }
    
    def _flatten_jsonb_to_dataframe(self, records: List, use_staging: bool = False) -> pd.DataFrame:
        """
        Flatten JSONB data to Pandas DataFrame
        
        Args:
            records: List of FlexibleDatasetWide or ImportPreviewStaging records
            use_staging: Whether records are from staging table
        
        Returns:
            Flattened DataFrame
        """
        data_list = []
        for record in records:
            # Start with metadata - different fields based on source
            if use_staging:
                row_data = {
                    'record_id': record.staging_id,
                    'import_batch_id': str(record.session_id),
                    'dataset_type': record.dataset_type,
                    'created_at': record.created_at
                }
                raw_jsonb = record.row_data
            else:
                row_data = {
                    'record_id': record.id,
                    'import_batch_id': str(record.import_batch_id),
                    'dataset_type': record.dataset_type,
                    'created_at': record.created_at
                }
                raw_jsonb = record.data
            
            # Ensure jsonb_data is a dict (handle None, string JSON)
            jsonb_data = self._ensure_dict(raw_jsonb)
            
            # Add JSONB data (flattened)
            if jsonb_data:
                # CRITICAL: Save flat keys BEFORE flattening
                # pd.json_normalize can miss root-level keys when nested objects exist
                flat_keys_to_preserve = ['labels_disease_classification']
                preserved_values = {key: jsonb_data.get(key) for key in flat_keys_to_preserve if key in jsonb_data}
                
                # Flatten nested JSONB structure
                flattened = pd.json_normalize(jsonb_data, sep='_').to_dict(orient='records')[0]
                row_data.update(flattened)
                
                # Restore preserved flat keys (overwrite if normalize changed them)
                for key, value in preserved_values.items():
                    row_data[key] = value
                    logger.info(f"✓ Preserved label: {key} = {value}")
            
            data_list.append(row_data)
        
        df = pd.DataFrame(data_list)
        
        logger.info(f"Flattened JSONB: {len(df)} rows, {len(df.columns)} columns")
        
        # Debug: Check available target columns
        available_targets = {
            'clinical_diagnosis_category': 'clinical_diagnosis_category' in df.columns,
            'labels_disease_classification': 'labels_disease_classification' in df.columns,
            'diagnosis_category': 'diagnosis_category' in df.columns,
        }
        logger.info(f"Available target columns: {[(k, v) for k, v in available_targets.items() if v]}")
        
        # Legacy compatibility: Check old labels_disease_classification
        if 'labels_disease_classification' in df.columns:
            logger.info(f"✓ labels_disease_classification column found! Sample: {df['labels_disease_classification'].value_counts().to_dict()}")
        
        # Preferred: Check new clinical_diagnosis_category
        if 'clinical_diagnosis_category' in df.columns:
            logger.info(f"✓ clinical_diagnosis_category column found! Sample: {df['clinical_diagnosis_category'].value_counts().to_dict()}")
        
        # Warn if neither exists
        if not any(available_targets.values()):
            label_cols = [c for c in df.columns if 'label' in c.lower() or 'diagnosis' in c.lower() or 'category' in c.lower()]
            logger.warning(f"⚠️  No standard target columns found! Columns containing 'label/diagnosis/category': {label_cols}")
        
        return df
    
    def _clean_for_ml(self, df: pd.DataFrame, target_column: str) -> pd.DataFrame:
        """
        Clean DataFrame for ML requirements
        
        Args:
            df: Input DataFrame
            target_column: Target column name
        
        Returns:
            Cleaned DataFrame
        """
        df = df.copy()
        
        # Remove metadata columns (start with _)
        metadata_cols = [col for col in df.columns if col.startswith('_')]
        if metadata_cols:
            logger.info(f"Removing {len(metadata_cols)} metadata columns")
            df = df.drop(columns=metadata_cols)
        
        # Convert data types
        df = self._convert_data_types(df)
        
        # Handle infinite values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isin([np.inf, -np.inf]).any():
                logger.warning(f"Replacing infinite values in {col} with NaN")
                df[col] = df[col].replace([np.inf, -np.inf], np.nan)
        
        # Remove constant columns (except target)
        # Also drop columns with unhashable values (lists/dicts) — unusable as ML features
        constant_cols = []
        for col in df.columns:
            if col == target_column:
                continue
            try:
                if df[col].nunique() == 1:
                    constant_cols.append(col)
            except TypeError:
                # Column contains unhashable types (lists/dicts) — not usable as a feature
                constant_cols.append(col)
        
        if constant_cols:
            logger.info(f"Removing {len(constant_cols)} constant/unhashable columns")
            df = df.drop(columns=constant_cols)
        
        return df
    
    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert data types to ML-compatible formats
        
        Args:
            df: Input DataFrame
        
        Returns:
            DataFrame with converted types
        """
        df = df.copy()
        
        for col in df.columns:
            # Skip already numeric columns
            if df[col].dtype in [np.int64, np.float64]:
                continue
            
            # Only convert if most values are actually numeric
            # pd.to_numeric(errors='coerce') NEVER raises — check first to avoid
            # silently nuking string columns like labels_disease_classification
            if df[col].dtype == object:
                non_null = df[col].dropna()
                if len(non_null) == 0:
                    continue
                # Drop columns that contain non-scalar values (lists/dicts)
                # — they cannot be used as ML features and cause TypeError in nunique()
                first_val = non_null.iloc[0]
                if isinstance(first_val, (list, dict)):
                    continue  # will be removed by the constant/unhashable check in _clean_for_ml
                converted = pd.to_numeric(non_null, errors='coerce')
                success_rate = converted.notna().sum() / len(non_null)
                # Only apply numeric conversion if ≥70% of values parse as numbers
                if success_rate >= 0.70:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                # else: leave as string/categorical (e.g. label columns, disease names)
        
        return df
    
    def validate_and_prepare(
        self,
        import_batch_id: uuid.UUID,
        target_column: str = "clinical_diagnosis_category"
    ) -> Dict:
        """
        Convenience method: Validate and prepare data in one call
        
        Args:
            import_batch_id: Batch ID
            target_column: Target column
        
        Returns:
            Prepared data dictionary
        """
        return self.prepare_data_for_ml(
            import_batch_id=import_batch_id,
            target_column=target_column,
            validate=True,
            drop_unlabeled=False
        )
    
    def get_ml_ready_statistics(
        self,
        import_batch_id: Optional[uuid.UUID] = None,
        dataset_type: Optional[str] = None
    ) -> Dict:
        """
        Get statistics about ML-ready data
        
        Args:
            import_batch_id: Batch ID filter
            dataset_type: Dataset type filter
        
        Returns:
            Statistics dictionary
        """
        result = self.prepare_data_for_ml(
            import_batch_id=import_batch_id,
            dataset_type=dataset_type,
            validate=False
        )
        
        if not result['success']:
            return result
        
        df = result['df']
        metadata = result['metadata']
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        stats = {
            'success': True,
            'total_records': len(df),
            'total_columns': len(df.columns),
            'numeric_columns': len(numeric_cols),
            'categorical_columns': len(categorical_cols),
            'missing_values_per_column': df.isnull().sum().to_dict(),
            'total_missing_percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100,
            'metadata': metadata
        }
        
        return stats
