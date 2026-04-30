"""
ML Schema Validator
Validates flexible_dataset_wide data before ML training
Ensures data quality and prevents training failures
"""
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
import uuid

from app.models.flexible_data import FlexibleDatasetWide, ImportPreviewStaging

logger = logging.getLogger(__name__)


def ensure_dict(data):
    """Ensure data is a dict. Handles None, string JSON, and existing dicts."""
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


class MLSchemaValidator:
    """
    Validate data schema before ML training
    
    Checks:
    - Required fields exist
    - Data types are correct
    - Value ranges are valid
    - No unexpected nulls
    - JSONB structure is valid
    - Sufficient data for training
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_for_ml_training(
        self,
        import_batch_id: Optional[uuid.UUID] = None,
        dataset_type: Optional[str] = None,
        min_records: int = 50,
        target_column: str = "labels_disease_classification"
    ) -> Dict:
        """
        Comprehensive validation before ML training
        
        Args:
            import_batch_id: Specific batch to validate (None = all data)
            dataset_type: Dataset type to validate (None = all types)
            min_records: Minimum required records
            target_column: Target column for ML
        
        Returns:
            Validation report with issues and recommendations
        """
        logger.info(
            f"Validating data for ML training: "
            f"batch={import_batch_id}, type={dataset_type}"
        )
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'info': [],
            'checks_performed': [],
            'recommendations': []
        }
        
        # Build query - try saved data first, then staging
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
            logger.info(f"No saved data for batch {import_batch_id}, checking staging...")
            staging_query = self.db.query(ImportPreviewStaging).filter(
                ImportPreviewStaging.session_id == import_batch_id,
                ImportPreviewStaging.is_deleted == False
            )
            records = staging_query.all()
            use_staging = True
            if records:
                logger.info(f"Using staging data: {len(records)} records")
        
        if not records:
            validation_result['valid'] = False
            validation_result['errors'].append({
                'check': 'data_exists',
                'message': 'No data found in saved or staging tables',
                'severity': 'critical'
            })
            return validation_result
        
        # Convert to DataFrame for analysis (ensure each record is a dict)
        data_list = [ensure_dict(record.row_data if use_staging else record.data) for record in records]
        df = pd.json_normalize(data_list)
        
        logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
        
        # === CHECK 1: Minimum Records ===
        validation_result['checks_performed'].append('minimum_records')
        if len(df) < min_records:
            validation_result['warnings'].append({
                'check': 'minimum_records',
                'message': f'Only {len(df)} records found (recommended: {min_records}+)',
                'severity': 'warning',
                'current_value': len(df),
                'recommended_value': min_records
            })
        else:
            validation_result['info'].append({
                'check': 'minimum_records',
                'message': f'Sufficient records: {len(df)} >= {min_records}',
                'status': 'pass'
            })
        
        # === CHECK 2: Target Column Exists ===
        validation_result['checks_performed'].append('target_column_exists')
        if target_column not in df.columns:
            validation_result['valid'] = False
            validation_result['errors'].append({
                'check': 'target_column_exists',
                'message': f'Target column "{target_column}" not found',
                'severity': 'critical',
                'recommendation': 'Assign labels using /label-assignment page'
            })
        else:
            # Check target column completeness
            null_count = df[target_column].isnull().sum()
            null_percentage = (null_count / len(df)) * 100
            
            if null_count > 0:
                validation_result['warnings'].append({
                    'check': 'target_completeness',
                    'message': f'{null_count} records ({null_percentage:.1f}%) missing labels',
                    'severity': 'warning',
                    'unlabeled_count': int(null_count),
                    'unlabeled_percentage': float(null_percentage)
                })
                validation_result['recommendations'].append(
                    f'Label {null_count} remaining records for better model performance'
                )
            else:
                validation_result['info'].append({
                    'check': 'target_completeness',
                    'message': 'All records have labels',
                    'status': 'pass'
                })
        
        # === CHECK 3: Feature Columns ===
        validation_result['checks_performed'].append('feature_columns')
        feature_cols = [col for col in df.columns if not col.startswith('_')]
        numeric_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df[feature_cols].select_dtypes(include=['object']).columns.tolist()
        
        total_features = len(numeric_cols) + len(categorical_cols)
        
        if total_features < 5:
            validation_result['warnings'].append({
                'check': 'feature_count',
                'message': f'Only {total_features} features found (recommended: 10+)',
                'severity': 'warning',
                'feature_count': total_features
            })
        else:
            validation_result['info'].append({
                'check': 'feature_count',
                'message': f'Sufficient features: {total_features} ({len(numeric_cols)} numeric, {len(categorical_cols)} categorical)',
                'status': 'pass'
            })
        
        # === CHECK 4: Missing Values ===
        validation_result['checks_performed'].append('missing_values')
        missing_per_column = df[feature_cols].isnull().sum()
        high_missing_cols = missing_per_column[missing_per_column > len(df) * 0.5]
        
        if len(high_missing_cols) > 0:
            validation_result['warnings'].append({
                'check': 'missing_values',
                'message': f'{len(high_missing_cols)} columns have >50% missing values',
                'severity': 'warning',
                'high_missing_columns': high_missing_cols.to_dict()
            })
            validation_result['recommendations'].append(
                'Consider removing columns with >50% missing values or apply imputation'
            )
        else:
            validation_result['info'].append({
                'check': 'missing_values',
                'message': 'No columns with excessive missing values',
                'status': 'pass'
            })
        
        # === CHECK 5: Data Type Consistency ===
        validation_result['checks_performed'].append('data_types')
        mixed_type_cols = []
        for col in numeric_cols:
            try:
                pd.to_numeric(df[col], errors='raise')
            except:
                mixed_type_cols.append(col)
        
        if mixed_type_cols:
            validation_result['warnings'].append({
                'check': 'data_types',
                'message': f'{len(mixed_type_cols)} numeric columns have mixed types',
                'severity': 'warning',
                'affected_columns': mixed_type_cols
            })
        else:
            validation_result['info'].append({
                'check': 'data_types',
                'message': 'All numeric columns have consistent types',
                'status': 'pass'
            })
        
        # === CHECK 6: Value Ranges ===
        validation_result['checks_performed'].append('value_ranges')
        infinite_cols = []
        for col in numeric_cols:
            if df[col].isin([np.inf, -np.inf]).any():
                infinite_cols.append(col)
        
        if infinite_cols:
            validation_result['warnings'].append({
                'check': 'value_ranges',
                'message': f'{len(infinite_cols)} columns contain infinite values',
                'severity': 'warning',
                'affected_columns': infinite_cols
            })
            validation_result['recommendations'].append(
                'Replace infinite values before training'
            )
        
        # === CHECK 7: Constant Columns ===
        validation_result['checks_performed'].append('constant_columns')
        constant_cols = []
        for col in feature_cols:
            if df[col].nunique() == 1:
                constant_cols.append(col)
        
        if constant_cols:
            validation_result['warnings'].append({
                'check': 'constant_columns',
                'message': f'{len(constant_cols)} columns have only one unique value',
                'severity': 'warning',
                'affected_columns': constant_cols
            })
            validation_result['recommendations'].append(
                'Remove constant columns (they provide no information)'
            )
        
        # === CHECK 8: Class Balance (for classification) ===
        if target_column in df.columns and df[target_column].notna().sum() > 0:
            validation_result['checks_performed'].append('class_balance')
            class_counts = df[target_column].value_counts()
            class_percentages = df[target_column].value_counts(normalize=True) * 100
            
            min_class_percentage = class_percentages.min()
            
            if min_class_percentage < 5:
                validation_result['warnings'].append({
                    'check': 'class_balance',
                    'message': f'Severe class imbalance: smallest class has {min_class_percentage:.1f}%',
                    'severity': 'warning',
                    'class_distribution': class_counts.to_dict()
                })
                validation_result['recommendations'].append(
                    'Consider class balancing techniques (SMOTE, class weights)'
                )
            elif min_class_percentage < 10:
                validation_result['info'].append({
                    'check': 'class_balance',
                    'message': f'Moderate class imbalance: smallest class has {min_class_percentage:.1f}%',
                    'status': 'acceptable',
                    'class_distribution': class_counts.to_dict()
                })
            else:
                validation_result['info'].append({
                    'check': 'class_balance',
                    'message': 'Classes are reasonably balanced',
                    'status': 'pass',
                    'class_distribution': class_counts.to_dict()
                })
        
        # === CHECK 9: JSONB Structure ===
        validation_result['checks_performed'].append('jsonb_structure')
        malformed_records = 0
        for record in data_list:
            if not isinstance(record, dict):
                malformed_records += 1
        
        if malformed_records > 0:
            validation_result['valid'] = False
            validation_result['errors'].append({
                'check': 'jsonb_structure',
                'message': f'{malformed_records} records have malformed JSONB data',
                'severity': 'critical',
                'malformed_count': malformed_records
            })
        else:
            validation_result['info'].append({
                'check': 'jsonb_structure',
                'message': 'All JSONB records are well-formed',
                'status': 'pass'
            })
        
        # === CHECK 10: Preprocessing Applied ===
        validation_result['checks_performed'].append('preprocessing_metadata')
        preprocessing_count = sum(1 for record in data_list if '_preprocessing_applied' in record)
        
        if preprocessing_count == 0:
            validation_result['info'].append({
                'check': 'preprocessing_metadata',
                'message': 'No Layer 5 preprocessing detected (ML will handle preprocessing)',
                'status': 'info'
            })
        else:
            validation_result['info'].append({
                'check': 'preprocessing_metadata',
                'message': f'Layer 5 preprocessing applied to {preprocessing_count} records',
                'status': 'pass',
                'preprocessing_count': preprocessing_count
            })
        
        # === FINAL SUMMARY ===
        validation_result['summary'] = {
            'total_records': len(df),
            'total_features': total_features,
            'numeric_features': len(numeric_cols),
            'categorical_features': len(categorical_cols),
            'checks_passed': len(validation_result['info']),
            'warnings': len(validation_result['warnings']),
            'errors': len(validation_result['errors']),
            'overall_status': 'pass' if validation_result['valid'] and len(validation_result['warnings']) == 0 else 'warning' if validation_result['valid'] else 'fail'
        }
        
        logger.info(
            f"Validation complete: {validation_result['summary']['overall_status']} "
            f"({validation_result['summary']['checks_passed']} passed, "
            f"{validation_result['summary']['warnings']} warnings, "
            f"{validation_result['summary']['errors']} errors)"
        )
        
        return validation_result
    
    def validate_single_record(
        self,
        record_data: Dict,
        required_fields: Optional[List[str]] = None
    ) -> Dict:
        """
        Validate a single record
        
        Args:
            record_data: JSONB data to validate
            required_fields: List of required field names
        
        Returns:
            Validation result
        """
        result = {
            'valid': True,
            'missing_fields': [],
            'invalid_fields': []
        }
        
        if required_fields:
            for field in required_fields:
                if field not in record_data:
                    result['valid'] = False
                    result['missing_fields'].append(field)
        
        return result
