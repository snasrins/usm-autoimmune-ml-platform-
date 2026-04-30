"""
ML Data Validation Service
Validates data in flexible_dataset_wide before ML training
Provides warnings and recommendations (flexible - doesn't block workflow)
"""
from typing import Dict, List, Any, Optional
import uuid
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.flexible_data import FlexibleDatasetWide, ImportPreviewStaging

logger = logging.getLogger(__name__)


def _ensure_dict(data) -> dict:
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


class MLDataValidator:
    """
    Validate data readiness for ML training
    Provides warnings and recommendations without blocking user workflow
    Supports both saved (FlexibleDatasetWide) and staging (ImportPreviewStaging) data
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._use_staging = False
    
    def _get_record_data(self, record) -> dict:
        """Get data dict from record, handling both saved and staging data."""
        if self._use_staging:
            return _ensure_dict(record.row_data)
        else:
            return _ensure_dict(record.data)
    
    def validate_for_ml_training(
        self,
        batch_id: Optional[uuid.UUID] = None,
        dataset_type: Optional[str] = None,
        target_column: str = 'labels_disease_classification',
        min_samples: int = 100,
        max_missing_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Validate if data is ML-ready
        
        Returns validation report with:
        - status: 'ready', 'warning', 'critical'
        - issues: List of problems found
        - recommendations: Suggested actions
        - can_proceed: Boolean (True for ready/warning, False for critical)
        
        Args:
            batch_id: Specific import batch to validate
            dataset_type: Filter by dataset type
            target_column: ML target column to check
            min_samples: Minimum samples needed for training
            max_missing_threshold: Maximum % of missing values allowed per record
        
        Returns:
            Validation report with flexible recommendations
        """
        # First try saved data (FlexibleDatasetWide)
        query = self.db.query(FlexibleDatasetWide)
        
        if batch_id:
            query = query.filter(FlexibleDatasetWide.import_batch_id == batch_id)
        if dataset_type:
            query = query.filter(FlexibleDatasetWide.dataset_type == dataset_type)
        
        records = query.all()
        self._use_staging = False
        
        # If no saved data, check staging
        if not records and batch_id:
            logger.info("No saved data found, checking staging for ML validation...")
            staging_query = self.db.query(ImportPreviewStaging).filter(
                ImportPreviewStaging.session_id == batch_id,
                ImportPreviewStaging.is_deleted == False
            )
            records = staging_query.all()
            self._use_staging = True
            if records:
                logger.info(f"Using staging data for validation: {len(records)} records")
        
        if not records:
            return {
                'status': 'critical',
                'can_proceed': False,
                'total_records': 0,
                'issues': [{
                    'type': 'no_data',
                    'severity': 'critical',
                    'message': 'No data found in saved or staging tables',
                    'recommendation': 'Please upload and save data before training'
                }],
                'recommendations': ['Upload data through Data Pipeline']
            }
        
        # Initialize validation results
        issues = []
        recommendations = []
        warnings = []
        
        # 1. Check sample size
        total_records = len(records)
        if total_records < min_samples:
            issues.append({
                'type': 'insufficient_samples',
                'severity': 'warning',
                'count': total_records,
                'minimum': min_samples,
                'message': f'Only {total_records} samples found (recommended: {min_samples}+)',
                'recommendation': 'Training may work but model performance could be poor. Consider collecting more data.',
                'can_proceed': True  # Allow but warn
            })
            warnings.append(f'Low sample count: {total_records} (recommended: {min_samples}+)')
        
        # 2. Check for target column (FLEXIBLE - warn but allow null)
        missing_target = []
        target_distribution = {}
        
        for record in records:
            record_data = self._get_record_data(record)
            target_value = self._extract_nested_value(record_data, target_column)
            
            if target_value is None:
                record_id = record.staging_id if self._use_staging else record.record_id
                missing_target.append(record_id)
            else:
                target_distribution[str(target_value)] = target_distribution.get(str(target_value), 0) + 1
        
        if missing_target:
            severity = 'critical' if len(missing_target) == total_records else 'warning'
            issues.append({
                'type': 'missing_target_column',
                'severity': severity,
                'count': len(missing_target),
                'percentage': round(len(missing_target) / total_records * 100, 2),
                'message': f'{len(missing_target)} records missing target column "{target_column}"',
                'recommendation': 'Add labels through Label Assignment UI. You can fill these later and retrain.' if severity == 'warning' else 'All records missing labels - cannot train without target variable',
                'can_proceed': severity == 'warning',
                'affected_records': missing_target[:10]  # Show first 10
            })
            
            if severity == 'warning':
                warnings.append(f'{len(missing_target)} records without labels (can be filled later)')
            else:
                recommendations.append('Use Label Assignment UI to add disease classifications')
        
        # 3. Check class balance (if target exists)
        if target_distribution:
            total_labeled = sum(target_distribution.values())
            n_classes = len(target_distribution)
            class_percentages = {k: round(v / total_labeled * 100, 2) for k, v in target_distribution.items()}
            
            # Check minimum number of classes
            if n_classes < 2:
                issues.append({
                    'type': 'insufficient_classes',
                    'severity': 'critical',
                    'count': n_classes,
                    'classes': list(target_distribution.keys()),
                    'message': f'Only {n_classes} unique class found in target column: {list(target_distribution.keys())}. Need at least 2 classes for classification.',
                    'recommendation': 'Add labels with different disease classifications. Ensure your dataset has multiple diagnoses (e.g., RA, SLE, Mixed).',
                    'can_proceed': False
                })
                recommendations.append('Add diverse disease classifications through Label Assignment UI')
            
            # Check for severe imbalance
            min_class_pct = min(class_percentages.values()) if class_percentages else 0
            max_class_pct = max(class_percentages.values()) if class_percentages else 0
            
            if min_class_pct < 5 and n_classes >= 2:
                issues.append({
                    'type': 'class_imbalance',
                    'severity': 'warning',
                    'distribution': class_percentages,
                    'message': f'Severe class imbalance detected (min class: {min_class_pct}%)',
                    'recommendation': 'Consider SMOTE or class weights during training. ML pipeline handles this automatically.',
                    'can_proceed': True
                })
                warnings.append(f'Class imbalance: {class_percentages}')
        
        # 4. Check data completeness per record
        high_missing_records = []
        total_fields_count = 0
        total_missing_count = 0
        
        for record in records:
            record_data = self._get_record_data(record)
            missing_count, total_fields = self._count_missing_fields(record_data)
            total_fields_count += total_fields
            total_missing_count += missing_count
            
            if total_fields > 0:
                missing_pct = missing_count / total_fields
                if missing_pct > max_missing_threshold:
                    record_id = record.staging_id if self._use_staging else record.record_id
                    high_missing_records.append({
                        'record_id': record_id,
                        'missing_percentage': round(missing_pct * 100, 2)
                    })
        
        overall_missing_pct = (total_missing_count / total_fields_count * 100) if total_fields_count > 0 else 0
        
        if high_missing_records:
            issues.append({
                'type': 'high_missing_values',
                'severity': 'warning',
                'count': len(high_missing_records),
                'overall_missing_percentage': round(overall_missing_pct, 2),
                'message': f'{len(high_missing_records)} records have >{max_missing_threshold * 100}% missing values',
                'recommendation': 'Use Layer 5 Preprocessing to handle missing values, or ML pipeline will auto-impute.',
                'can_proceed': True,
                'sample_records': high_missing_records[:5]
            })
            warnings.append(f'{len(high_missing_records)} records with high missing values')
        
        # 5. Check for preprocessing metadata
        preprocessed_count = 0
        preprocessing_methods = set()
        
        for record in records:
            record_data = self._get_record_data(record)
            preprocessing_meta = record_data.get('_preprocessing_applied', {})
            if preprocessing_meta.get('layer_5'):
                preprocessed_count += 1
                operations = preprocessing_meta.get('operations', [])
                preprocessing_methods.update(operations)
        
        if preprocessed_count == 0:
            issues.append({
                'type': 'no_preprocessing',
                'severity': 'info',
                'message': 'No Layer 5 preprocessing detected',
                'recommendation': 'Consider using Layer 5 Data Cleaning for better quality. ML pipeline will handle basic preprocessing.',
                'can_proceed': True
            })
        
        # 6. Check available features
        all_feature_columns = set()
        for record in records:
            record_data = self._get_record_data(record)
            flat_data = self._flatten_jsonb(record_data)
            all_feature_columns.update(flat_data.keys())
        
        # Remove metadata fields
        feature_columns = [col for col in all_feature_columns if not col.startswith('_')]
        
        if len(feature_columns) < 5:
            issues.append({
                'type': 'insufficient_features',
                'severity': 'warning',
                'count': len(feature_columns),
                'message': f'Only {len(feature_columns)} features detected',
                'recommendation': 'More features generally improve model performance',
                'can_proceed': True
            })
        
        # 7. Determine overall status
        critical_issues = [i for i in issues if i.get('severity') == 'critical']
        warning_issues = [i for i in issues if i.get('severity') in ['warning', 'info']]
        
        if critical_issues:
            status = 'critical'
            can_proceed = False
        elif warning_issues:
            status = 'warning'
            can_proceed = True
        else:
            status = 'ready'
            can_proceed = True
        
        # Build final report
        return {
            'status': status,
            'can_proceed': can_proceed,
            'total_records': total_records,
            'labeled_records': total_records - len(missing_target),
            'unlabeled_records': len(missing_target),
            'target_column': target_column,
            'target_distribution': target_distribution if target_distribution else None,
            'total_features': len(feature_columns),
            'preprocessing_applied': preprocessed_count > 0,
            'preprocessing_methods': list(preprocessing_methods),
            'overall_missing_percentage': round(overall_missing_pct, 2),
            'issues': issues,
            'warnings': warnings,
            'recommendations': recommendations,
            'data_quality_summary': {
                'sufficient_samples': total_records >= min_samples,
                'has_labels': len(missing_target) < total_records,
                'acceptable_completeness': overall_missing_pct < 50,
                'preprocessed': preprocessed_count > 0
            }
        }
    
    def get_labeling_progress(
        self,
        batch_id: Optional[uuid.UUID] = None,
        dataset_type: Optional[str] = None,
        target_column: str = 'labels_disease_classification'
    ) -> Dict[str, Any]:
        """
        Get labeling progress for data
        Helps users track which records still need labels
        Supports both saved and staging data
        
        Returns:
            Progress report with unlabeled record IDs
        """
        # First try saved data
        query = self.db.query(FlexibleDatasetWide)
        
        if batch_id:
            query = query.filter(FlexibleDatasetWide.import_batch_id == batch_id)
        if dataset_type:
            query = query.filter(FlexibleDatasetWide.dataset_type == dataset_type)
        
        records = query.all()
        self._use_staging = False
        
        # If no saved data, check staging
        if not records and batch_id:
            staging_query = self.db.query(ImportPreviewStaging).filter(
                ImportPreviewStaging.session_id == batch_id,
                ImportPreviewStaging.is_deleted == False
            )
            records = staging_query.all()
            self._use_staging = True
        
        labeled = []
        unlabeled = []
        
        for record in records:
            record_data = self._get_record_data(record)
            target_value = self._extract_nested_value(record_data, target_column)
            record_id = record.staging_id if self._use_staging else record.record_id
            
            if target_value is None:
                unlabeled.append({
                    'record_id': record_id,
                    'dataset_type': record.dataset_type,
                    'created_at': record.created_at.isoformat() if record.created_at else None
                })
            else:
                labeled.append({
                    'record_id': record_id,
                    'label': str(target_value)
                })
        
        total = len(records)
        labeled_count = len(labeled)
        unlabeled_count = len(unlabeled)
        
        return {
            'total_records': total,
            'labeled_count': labeled_count,
            'unlabeled_count': unlabeled_count,
            'progress_percentage': round((labeled_count / total * 100) if total > 0 else 0, 2),
            'labeled_records': labeled,
            'unlabeled_records': unlabeled,
            'status': 'complete' if unlabeled_count == 0 else 'in_progress' if labeled_count > 0 else 'not_started'
        }
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def _extract_nested_value(self, data: dict, path: str) -> Any:
        """
        Extract value from nested JSONB using dot notation
        Example: 'labels.disease_classification' → data['labels']['disease_classification']
        """
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _count_missing_fields(self, data: dict) -> tuple:
        """
        Count missing (None/null) fields in nested JSONB
        Returns: (missing_count, total_fields)
        """
        def count_recursive(obj):
            if isinstance(obj, dict):
                missing = 0
                total = 0
                for key, value in obj.items():
                    if key.startswith('_'):  # Skip metadata
                        continue
                    if value is None:
                        missing += 1
                        total += 1
                    elif isinstance(value, dict):
                        sub_missing, sub_total = count_recursive(value)
                        missing += sub_missing
                        total += sub_total
                    else:
                        total += 1
                return missing, total
            else:
                return (0, 0)
        
        return count_recursive(data)
    
    def _flatten_jsonb(self, data: dict, parent_key: str = '', sep: str = '_') -> dict:
        """Flatten nested JSONB structure"""
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_jsonb(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        
        return dict(items)
