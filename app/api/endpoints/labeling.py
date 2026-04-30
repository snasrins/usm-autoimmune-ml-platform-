"""
Label Assignment API Endpoints
Allows users to assign disease classification labels to unlabeled data
Critical for ML training - provides target variable
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uuid as uuid_lib
from datetime import datetime
import logging
import json

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.flexible_data import FlexibleDatasetWide, ImportPreviewStaging
from app.services.ml_data_validator import MLDataValidator

logger = logging.getLogger(__name__)
router = APIRouter()


def ensure_dict(data) -> dict:
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


# ============================================
# REQUEST MODELS
# ============================================

class LabelAssignment(BaseModel):
    """Single label assignment request"""
    record_id: str
    label: str
    confidence: Optional[float] = None  # User confidence 0-1 (optional)
    notes: Optional[str] = None  # Clinical notes


class BulkLabelAssignment(BaseModel):
    """Bulk label assignment request"""
    record_ids: List[str]
    label: str
    confidence: Optional[float] = None
    notes: Optional[str] = None


class BatchLabelAssignment(BaseModel):
    """Assign same label to entire import batch"""
    batch_id: str
    label: str
    confidence: Optional[float] = None
    notes: Optional[str] = None


# ============================================
# LABEL ASSIGNMENT ENDPOINTS
# ============================================

@router.post("/labeling/assign")
async def assign_label_to_record(
    assignment: LabelAssignment,
    target_column: str = 'labels_disease_classification',
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Assign disease classification label to a single record
    
    User-controlled labeling:
    - Clinician reviews patient data
    - Selects appropriate diagnosis category
    - System updates flexible_dataset_wide JSONB data
    
    Args:
        assignment: Label assignment details (record_id, label, etc.)
        target_column: Target column path (default: labels_disease_classification)
    
    Returns:
        Updated record with label
    """
    try:
        # Find record
        record = db.query(FlexibleDatasetWide).filter(
            FlexibleDatasetWide.record_id == assignment.record_id
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail=f"Record {assignment.record_id} not found")
        
        # Update JSONB data with label
        if record.data is None:
            record.data = {}
        
        # Parse target_column path (supports nested: labels.disease_classification)
        keys = target_column.split('.')
        current = record.data
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set final value
        final_key = keys[-1]
        current[final_key] = assignment.label
        
        # Add labeling metadata
        if '_labeling_metadata' not in record.data:
            record.data['_labeling_metadata'] = {}
        
        record.data['_labeling_metadata'].update({
            'labeled_by': current_user.id,
            'labeled_at': datetime.utcnow().isoformat(),
            'label_confidence': assignment.confidence,
            'label_notes': assignment.notes,
            'target_column': target_column
        })
        
        # Mark JSONB column as modified (required for SQLAlchemy to persist changes)
        flag_modified(record, 'data')
        
        db.flush()
        db.commit()
        db.refresh(record)
        
        return {
            'success': True,
            'record_id': assignment.record_id,
            'label': assignment.label,
            'target_column': target_column,
            'labeled_by': current_user.id,
            'labeled_at': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Label assignment failed: {str(e)}")


@router.post("/labeling/bulk-assign")
async def bulk_assign_labels(
    assignment: BulkLabelAssignment,
    target_column: str = 'labels_disease_classification',
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Assign same label to multiple records (bulk operation)
    
    User selects multiple records in UI and assigns same diagnosis
    Useful for labeling groups of similar patients
    
    Args:
        assignment: Bulk assignment with record_ids and label
        target_column: Target column path
    
    Returns:
        Statistics of bulk assignment
    """
    try:
        updated_count = 0
        failed_records = []
        
        for record_id in assignment.record_ids:
            try:
                record = db.query(FlexibleDatasetWide).filter(
                    FlexibleDatasetWide.record_id == record_id
                ).first()
                
                if not record:
                    failed_records.append({'record_id': record_id, 'error': 'Not found'})
                    continue
                
                # Update JSONB data
                if record.data is None:
                    record.data = {}
                
                # Parse and set label
                keys = target_column.split('.')
                current = record.data
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                current[keys[-1]] = assignment.label
                
                # Add metadata
                if '_labeling_metadata' not in record.data:
                    record.data['_labeling_metadata'] = {}
                
                record.data['_labeling_metadata'].update({
                    'labeled_by': current_user.id,
                    'labeled_at': datetime.utcnow().isoformat(),
                    'label_confidence': assignment.confidence,
                    'label_notes': assignment.notes,
                    'bulk_operation': True
                })
                
                # Mark JSONB column as modified
                flag_modified(record, 'data')
                
                updated_count += 1
                
            except Exception as e:
                failed_records.append({'record_id': record_id, 'error': str(e)})
        
        db.commit()
        
        return {
            'success': True,
            'total_requested': len(assignment.record_ids),
            'updated_count': updated_count,
            'failed_count': len(failed_records),
            'failed_records': failed_records,
            'label': assignment.label
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk label assignment failed: {str(e)}")


@router.post("/labeling/batch-assign")
async def assign_label_to_batch(
    assignment: BatchLabelAssignment,
    target_column: str = 'labels_disease_classification',
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Assign same label to entire import batch
    
    Useful when user uploads data that's all the same category
    Example: Upload batch of 200 confirmed SLE patients
    
    Args:
        assignment: Batch assignment with batch_id and label
        target_column: Target column path
    
    Returns:
        Statistics of batch assignment
    """
    try:
        batch_uuid = uuid_lib.UUID(assignment.batch_id)
        
        # Find all records in batch
        records = db.query(FlexibleDatasetWide).filter(
            FlexibleDatasetWide.import_batch_id == batch_uuid
        ).all()
        
        if not records:
            raise HTTPException(status_code=404, detail=f"No records found for batch {assignment.batch_id}")
        
        updated_count = 0
        
        for record in records:
            if record.data is None:
                record.data = {}
            
            # Parse and set label
            keys = target_column.split('.')
            current = record.data
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            current[keys[-1]] = assignment.label
            
            # Add metadata
            if '_labeling_metadata' not in record.data:
                record.data['_labeling_metadata'] = {}
            
            record.data['_labeling_metadata'].update({
                'labeled_by': current_user.id,
                'labeled_at': datetime.utcnow().isoformat(),
                'label_confidence': assignment.confidence,
                'label_notes': assignment.notes,
                'batch_operation': True,
                'batch_id': assignment.batch_id
            })
            
            # Mark JSONB column as modified (critical for persistence)
            flag_modified(record, 'data')
            
            updated_count += 1
        
        db.commit()
        
        return {
            'success': True,
            'batch_id': assignment.batch_id,
            'total_records': len(records),
            'updated_count': updated_count,
            'label': assignment.label
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid batch ID: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch label assignment failed: {str(e)}")


@router.get("/labeling/unlabeled")
async def get_unlabeled_records(
    target_column: str = 'labels_disease_classification',
    dataset_type: Optional[str] = None,
    batch_id: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get unlabeled records for labeling
    
    Shows user which records still need labels
    Can filter by dataset_type or batch_id
    
    Args:
        target_column: Target column to check for labels
        dataset_type: Filter by dataset type (optional)
        batch_id: Filter by import batch (optional)
        limit: Max records to return
        offset: Pagination offset
    
    Returns:
        List of unlabeled records with details for labeling UI
    """
    try:
        use_staging = False
        all_records = []
        
        # First try saved data (FlexibleDatasetWide)
        query = db.query(FlexibleDatasetWide)
        
        # Apply filters
        if dataset_type:
            query = query.filter(FlexibleDatasetWide.dataset_type == dataset_type)
        
        if batch_id:
            batch_uuid = uuid_lib.UUID(batch_id)
            query = query.filter(FlexibleDatasetWide.import_batch_id == batch_uuid)
        
        # Get all records (we'll filter by label in Python since it's JSONB)
        all_records = query.offset(offset).limit(limit * 2).all()  # Get extra for filtering
        
        # If no saved data and batch_id provided, try staging
        if not all_records and batch_id:
            logger.info(f"No saved data for batch {batch_id}, checking staging...")
            batch_uuid = uuid_lib.UUID(batch_id)
            staging_query = db.query(ImportPreviewStaging).filter(
                ImportPreviewStaging.session_id == batch_uuid,
                ImportPreviewStaging.is_deleted == False
            ).offset(offset).limit(limit * 2)
            all_records = staging_query.all()
            use_staging = True
            if all_records:
                logger.info(f"Using staging data: {len(all_records)} records")
        
        logger.info(f"Fetching unlabeled records: found {len(all_records)} total records (staging={use_staging})")
        
        # Filter unlabeled records
        unlabeled = []
        keys = target_column.split('.')
        
        for record in all_records:
            if len(unlabeled) >= limit:
                break
            
            # Check if label exists (try both nested and flat)
            record_data = ensure_dict(record.row_data if use_staging else record.data)
            current = record_data
            has_label = False
            label_value = None
            
            # Try nested navigation
            temp_current = current
            found = True
            for key in keys:
                if not isinstance(temp_current, dict) or key not in temp_current:
                    found = False
                    break
                temp_current = temp_current[key]
            
            if found and temp_current is not None and temp_current != '':
                has_label = True
                label_value = temp_current
            else:
                # Try flat key
                flat_key = '_'.join(keys)
                if flat_key in current and current[flat_key] not in [None, '', 'null']:
                    has_label = True
                    label_value = current[flat_key]
            
            if not has_label:
                # Record is unlabeled - return full data for UI display
                if use_staging:
                    unlabeled.append({
                        'record_id': record.staging_id,
                        'dataset_type': record.dataset_type,
                        'dataset_name': record.dataset_name,
                        'import_batch_id': str(record.session_id),
                        'created_at': record.created_at.isoformat() if record.created_at else None,
                        'data': record_data  # Return parsed data for flexible display
                    })
                else:
                    unlabeled.append({
                        'record_id': record.record_id,
                        'dataset_type': record.dataset_type,
                        'dataset_name': record.dataset_name,
                        'import_batch_id': str(record.import_batch_id),
                        'created_at': record.created_at.isoformat() if record.created_at else None,
                        'data': record_data  # Return parsed data for flexible display
                    })
        
        logger.info(f"Found {len(unlabeled)} unlabeled records")
        
        return {
            'total_unlabeled': len(unlabeled),
            'unlabeled_records': unlabeled,  # Changed from 'records' to match frontend expectation
            'pagination': {
                'limit': limit,
                'offset': offset,
                'has_more': len(unlabeled) == limit
            },
            'data_source': 'staging' if use_staging else 'saved'
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get unlabeled records: {str(e)}")


@router.get("/labeling/statistics")
async def get_label_statistics(
    target_column: str = 'labels_disease_classification',
    dataset_type: Optional[str] = None,
    import_batch_id: Optional[str] = Query(None, description="Filter by specific batch ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get labeling statistics
    
    Shows:
    - Total records
    - Labeled vs unlabeled count
    - Label distribution (SLE: 850, Sjogren: 200, etc.)
    - Labeling progress percentage
    
    Args:
        target_column: Target column to analyze
        dataset_type: Filter by dataset type (optional)
        import_batch_id: Filter by specific batch (optional)
    
    Returns:
        Labeling statistics
    """
    try:
        use_staging = False
        all_records = []
        
        # First try saved data (FlexibleDatasetWide)
        query = db.query(FlexibleDatasetWide)
        
        if dataset_type:
            query = query.filter(FlexibleDatasetWide.dataset_type == dataset_type)
        
        if import_batch_id:
            batch_uuid = uuid_lib.UUID(import_batch_id)
            query = query.filter(FlexibleDatasetWide.import_batch_id == batch_uuid)
        
        all_records = query.all()
        
        # If no saved data and batch_id provided, try staging
        if not all_records and import_batch_id:
            logger.info(f"No saved data for batch {import_batch_id}, checking staging...")
            batch_uuid = uuid_lib.UUID(import_batch_id)
            staging_query = db.query(ImportPreviewStaging).filter(
                ImportPreviewStaging.session_id == batch_uuid,
                ImportPreviewStaging.is_deleted == False
            )
            all_records = staging_query.all()
            use_staging = True
            if all_records:
                logger.info(f"Using staging data: {len(all_records)} records")
        
        if not all_records:
            logger.warning(f"No records found for batch {import_batch_id}")
            return {
                'total_records': 0,
                'labeled_count': 0,
                'unlabeled_count': 0,
                'progress_percentage': 0,
                'label_distribution': {},
                'target_column': target_column,
                'dataset_type': dataset_type
            }
        
        # Analyze labels
        labeled_count = 0
        unlabeled_count = 0
        label_distribution = {}
        keys = target_column.split('.')
        
        logger.info(f"Analyzing {len(all_records)} records for labels at {target_column} (staging={use_staging})")
        
        for record in all_records:
            record_data = ensure_dict(record.row_data if use_staging else record.data)
            current = record_data
            label_value = None
            
            # Try nested navigation first (labels.disease_classification)
            temp_current = current
            found = True
            for key in keys:
                if not isinstance(temp_current, dict) or key not in temp_current:
                    found = False
                    break
                temp_current = temp_current[key]
            
            if found:
                label_value = temp_current
            else:
                # Try flat key (labels_disease_classification)
                flat_key = '_'.join(keys)
                if flat_key in current:
                    label_value = current[flat_key]
            
            # Consider None, empty string, or 'null' as unlabeled
            if label_value is None or label_value == '' or label_value == 'null':
                unlabeled_count += 1
            else:
                labeled_count += 1
                label_str = str(label_value)
                label_distribution[label_str] = label_distribution.get(label_str, 0) + 1
        
        total = len(all_records)
        progress_percentage = (labeled_count / total * 100) if total > 0 else 0
        
        logger.info(
            f"Label statistics: {total} total, {labeled_count} labeled, "
            f"{unlabeled_count} unlabeled, {progress_percentage:.2f}% progress"
        )
        
        return {
            'total_records': total,
            'labeled_count': labeled_count,
            'unlabeled_count': unlabeled_count,
            'progress_percentage': round(progress_percentage, 2),
            'label_distribution': label_distribution,
            'target_column': target_column,
            'dataset_type': dataset_type
        }
    
    except Exception as e:
        logger.error(f"Failed to get label statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get label statistics: {str(e)}")


class AutoLabelRequest(BaseModel):
    """Auto-label based on existing data"""
    batch_id: Optional[str] = None
    source_column: str  # e.g., "SLEDAI" or "biomarkers_sledai"  
    target_column: str = 'labels_disease_severity'
    label_type: str = 'severity'  # 'severity', 'kidney', or 'activity'


class LabelingRule(BaseModel):
    """Single labeling rule with condition and label"""
    condition: str  # e.g., "< 4", ">= 4 and <= 12", "> 12", "== 'Positive'"
    label: str      # e.g., "Low Activity", "Moderate", "High Activity"
    description: Optional[str] = None


class RuleBasedLabelRequest(BaseModel):
    """Flexible rule-based labeling request"""
    batch_id: Optional[str] = None
    source_column: str  # Column to evaluate (e.g., "SLEDAI", "CRP", "Protein_Urine")
    rules: List[LabelingRule]  # List of condition-label pairs
    target_column: str = 'labels_custom'  # Where to store the label
    overwrite_existing: bool = False  # Whether to re-label already labeled records


@router.post("/labeling/auto-label")
async def auto_label_records(
    request: AutoLabelRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Automatically assign labels based on existing data (e.g., SLEDAI scores)
    
    This saves users from manually labeling 100+ records one by one.
    
    Label Types:
    - 'severity': Based on SLEDAI score
        - Mild: SLEDAI ≤4
        - Moderate: SLEDAI 5-12
        - Severe: SLEDAI >12
    - 'kidney': Based on urinary protein
        - No-kidney-involvement: - or 无
        - Trace-proteinuria: ±
        - Lupus-nephritis: +, 2+, 3+, 4+
    - 'activity': Based on multiple markers
        - Similar to severity but stricter criteria
    
    Args:
        request: Auto-labeling configuration
    
    Returns:
        Count of records labeled
    """
    try:
        query = db.query(FlexibleDatasetWide)
        
        if request.batch_id:
            batch_uuid = uuid_lib.UUID(request.batch_id)
            query = query.filter(FlexibleDatasetWide.import_batch_id == batch_uuid)
        
        records = query.all()
        
        if not records:
            raise HTTPException(status_code=404, detail="No records found")
        
        logger.info(f"Auto-labeling {len(records)} records using {request.label_type} strategy")
        
        # Check first record to see what fields are available
        if records and records[0].data:
            sample_keys = []
            def extract_all_keys(obj, prefix=''):
                """Recursively extract all key paths from JSONB"""
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        current_path = f"{prefix}.{k}" if prefix else k
                        sample_keys.append(current_path)
                        if isinstance(v, dict):
                            extract_all_keys(v, current_path)
            
            extract_all_keys(records[0].data)
            logger.info(f"Available fields in first record: {sample_keys[:20]}")  # Log first 20 fields
        
        labeled_count = 0
        skipped_count = 0
        error_count = 0
        
        for record in records:
            try:
                if record.data is None:
                    record.data = {}
                
                # Extract source value - search multiple possible locations
                source_value = None
                
                # Try direct path first
                source_keys = request.source_column.split('.')
                current = record.data
                
                for key in source_keys:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        current = None
                        break
                
                source_value = current
                
                # If not found, try case-insensitive search in entire JSONB
                if source_value is None:
                    def find_key_recursive(obj, target_key):
                        """Recursively search for key (case-insensitive) in nested dict"""
                        if isinstance(obj, dict):
                            # Try exact match first
                            if target_key in obj:
                                return obj[target_key]
                            # Try case-insensitive match
                            for k, v in obj.items():
                                if k.lower() == target_key.lower():
                                    return v
                            # Recurse into nested dicts
                            for k, v in obj.items():
                                result = find_key_recursive(v, target_key)
                                if result is not None:
                                    return result
                        return None
                    
                    source_value = find_key_recursive(record.data, request.source_column)
                
                if source_value is None:
                    skipped_count += 1
                    continue
                
                # Determine label based on strategy
                label = None
                
                if request.label_type == 'severity':
                    # Based on SLEDAI score
                    try:
                        sledai = float(source_value)
                        if sledai <= 4:
                            label = 'Mild'
                        elif sledai <= 12:
                            label = 'Moderate'
                        else:
                            label = 'Severe'
                    except (ValueError, TypeError):
                        skipped_count += 1
                        continue
                
                elif request.label_type == 'kidney':
                    # Based on urinary protein
                    up = str(source_value).strip()
                    if up in ['-', '无']:
                        label = 'No-kidney-involvement'
                    elif up == '±':
                        label = 'Trace-proteinuria'
                    elif up in ['+', '2+', '3+', '4+']:
                        label = 'Lupus-nephritis'
                    else:
                        skipped_count += 1
                        continue
                
                elif request.label_type == 'activity':
                    # Based on SLEDAI for activity status
                    try:
                        sledai = float(source_value)
                        if sledai == 0:
                            label = 'Remission'
                        elif sledai <= 10:
                            label = 'Active'
                        else:
                            label = 'Flare'
                    except (ValueError, TypeError):
                        skipped_count += 1
                        continue
                
                if label:
                    # Set label using target_column path
                    target_keys = request.target_column.split('.')
                    current = record.data
                    for key in target_keys[:-1]:
                        if key not in current:
                            current[key] = {}
                        current = current[key]
                    
                    current[target_keys[-1]] = label
                    
                    # Add metadata
                    if '_labeling_metadata' not in record.data:
                        record.data['_labeling_metadata'] = {}
                    
                    record.data['_labeling_metadata'].update({
                        'labeled_by': current_user.id,
                        'labeled_at': datetime.utcnow().isoformat(),
                        'label_confidence': 1.0,
                        'auto_labeled': True,
                        'auto_label_source': request.source_column,
                        'auto_label_strategy': request.label_type
                    })
                    
                    flag_modified(record, 'data')
                    labeled_count += 1
            
            except Exception as e:
                logger.error(f"Error labeling record {record.record_id}: {e}")
                error_count += 1
                continue
        
        db.commit()
        
        logger.info(
            f"Auto-labeling complete: {labeled_count} labeled, "
            f"{skipped_count} skipped (no source data), {error_count} errors"
        )
        
        # If nothing was labeled, provide helpful error with available fields
        if labeled_count == 0 and records:
            available_fields = []
            if records[0].data:
                def get_all_keys(obj, prefix=''):
                    keys = []
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            current_path = f"{prefix}.{k}" if prefix else k
                            keys.append(current_path)
                            if isinstance(v, dict) and not k.startswith('_'):
                                keys.extend(get_all_keys(v, current_path))
                    return keys
                
                available_fields = get_all_keys(records[0].data)
                # Filter out metadata
                available_fields = [f for f in available_fields if not f.startswith('_')][:30]
            
            error_msg = (
                f"No records were labeled. Could not find '{request.source_column}' in any record.\n\n"
                f"Available fields in your data: {', '.join(available_fields[:15])}"
                + (f"... and {len(available_fields) - 15} more" if len(available_fields) > 15 else "")
            )
            raise HTTPException(status_code=404, detail=error_msg)
        
        return {
            'success': True,
            'total_records': len(records),
            'labeled_count': labeled_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'label_type': request.label_type,
            'source_column': request.source_column,
            'target_column': request.target_column
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        logger.error(f"Auto-labeling failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Auto-labeling failed: {str(e)}")


@router.post("/labeling/rule-based-label")
async def rule_based_label_records(
    request: RuleBasedLabelRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Flexible rule-based labeling - researcher defines custom rules
    
    This allows complete flexibility:
    - Select any source column (SLEDAI, CRP, Protein, etc.)
    - Define any number of conditional rules
    - Support numeric comparisons (<, >, <=, >=, ==) and text matching
    - Support compound conditions (and, or)
    
    Example Request:
    {
        "batch_id": "uuid",
        "source_column": "SLEDAI",
        "rules": [
            {"condition": "< 4", "label": "Mild", "description": "Low disease activity"},
            {"condition": ">= 4 and <= 12", "label": "Moderate"},
            {"condition": "> 12", "label": "Severe"}
        ],
        "target_column": "disease_severity",
        "overwrite_existing": false
    }
    
    Supported Operators:
    - Numeric: <, >, <=, >=, ==, !=
    - Logical: and, or
    - Text: == 'value', != 'value', in ['val1', 'val2']
    
    Returns:
        Summary of labeling operation
    """
    try:
        # Validate rules
        if not request.rules:
            raise HTTPException(status_code=400, detail="At least one rule must be provided")
        
        # Query records - first try FlexibleDatasetWide (saved data)
        use_staging = False
        records = []
        
        if request.batch_id:
            batch_uuid = uuid_lib.UUID(request.batch_id)
            
            # First check saved data
            query = db.query(FlexibleDatasetWide).filter(
                FlexibleDatasetWide.import_batch_id == batch_uuid
            )
            records = query.all()
            
            # If no saved data, check staging (preview data)
            if not records:
                staging_query = db.query(ImportPreviewStaging).filter(
                    ImportPreviewStaging.session_id == batch_uuid,
                    ImportPreviewStaging.is_deleted == False
                )
                records = staging_query.all()
                use_staging = True
                logger.info(f"Using staging data for batch {request.batch_id}")
        else:
            # No batch_id - query all saved data
            records = db.query(FlexibleDatasetWide).all()
        
        if not records:
            raise HTTPException(status_code=404, detail="No records found. Make sure the dataset exists and has been uploaded.")
        
        logger.info(f"Rule-based labeling: {len(records)} records, {len(request.rules)} rules, source='{request.source_column}', staging={use_staging}")
        
        # Statistics
        labeled_count = 0
        skipped_count = 0
        error_count = 0
        rule_matches = {i: 0 for i in range(len(request.rules))}
        
        for record in records:
            try:
                # Get data field based on table type - ensure it's a dict
                record_id = record.staging_id if use_staging else record.record_id
                
                if use_staging:
                    # Ensure row_data is a dict (handle None, string JSON)
                    record_data = ensure_dict(record.row_data)
                    # Assign back to record so changes persist
                    record.row_data = record_data
                else:
                    record_data = ensure_dict(record.data)
                    record.data = record_data
                
                # Check if already labeled and skip if overwrite=False
                if not request.overwrite_existing:
                    target_keys = request.target_column.split('.')
                    current = record_data
                    for key in target_keys:
                        if isinstance(current, dict) and key in current:
                            current = current[key]
                        else:
                            current = None
                            break
                    
                    if current is not None:
                        skipped_count += 1
                        continue
                
                # Extract source value
                source_value = extract_value_from_jsonb(record_data, request.source_column)
                
                if source_value is None:
                    logger.debug(f"Record {record_id}: source column '{request.source_column}' not found or is None")
                    skipped_count += 1
                    continue
                
                logger.debug(f"Record {record_id}: source value = '{source_value}' (type: {type(source_value).__name__})")
                
                # Evaluate rules in order
                matched_label = None
                matched_rule_idx = None
                
                for idx, rule in enumerate(request.rules):
                    try:
                        logger.debug(f"Evaluating rule {idx}: '{rule.condition}' against value '{source_value}'")
                        if evaluate_condition(source_value, rule.condition):
                            matched_label = rule.label
                            matched_rule_idx = idx
                            logger.debug(f"✓ Rule {idx} matched! Label: {matched_label}")
                            break
                        else:
                            logger.debug(f"✗ Rule {idx} did not match")
                    except Exception as rule_error:
                        logger.warning(f"Rule evaluation error for '{rule.condition}': {rule_error}")
                        continue
                
                if matched_label:
                    # Apply label
                    set_value_in_jsonb(record_data, request.target_column, matched_label)
                    
                    # DEBUG: Verify label was set
                    logger.info(f"Record {record_id}: Set {request.target_column} = {matched_label}")
                    logger.debug(f"Record {record_id}: Keys after labeling: {list(record_data.keys())[:10]}")
                    
                    # Add metadata
                    if '_labeling_metadata' not in record_data:
                        record_data['_labeling_metadata'] = {}
                    
                    record_data['_labeling_metadata'].update({
                        'labeled_by': current_user.id,
                        'labeled_at': datetime.utcnow().isoformat(),
                        'label_confidence': 1.0,
                        'rule_based': True,
                        'source_column': request.source_column,
                        'source_value': str(source_value),
                        'matched_rule': request.rules[matched_rule_idx].condition,
                        'rule_description': request.rules[matched_rule_idx].description
                    })
                    
                    # Mark record as modified
                    if use_staging:
                        flag_modified(record, 'row_data')
                    else:
                        flag_modified(record, 'data')
                    labeled_count += 1
                    rule_matches[matched_rule_idx] += 1
                else:
                    # No rule matched
                    skipped_count += 1
            
            except Exception as e:
                logger.error(f"Error labeling record {record_id}: {e}")
                error_count += 1
                continue
        
        db.commit()
        
        logger.info(
            f"Rule-based labeling complete: {labeled_count} labeled, "
            f"{skipped_count} skipped, {error_count} errors"
        )
        
        # Build response with rule match statistics
        rule_statistics = [
            {
                "rule_index": idx,
                "condition": rule.condition,
                "label": rule.label,
                "matches": rule_matches[idx]
            }
            for idx, rule in enumerate(request.rules)
        ]
        
        return {
            'success': True,
            'total_records': len(records),
            'labeled_count': labeled_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'source_column': request.source_column,
            'target_column': request.target_column,
            'rule_statistics': rule_statistics,
            'data_source': 'staging' if use_staging else 'saved'
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        logger.error(f"Rule-based labeling failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Rule-based labeling failed: {str(e)}")


# ============================================
# HELPER FUNCTIONS FOR RULE EVALUATION
# ============================================

def extract_value_from_jsonb(data: Dict, column_path: str) -> Any:
    """
    Extract value from nested JSONB using dot notation
    Supports case-insensitive search
    """
    # Try direct path first
    keys = column_path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            current = None
            break
    
    if current is not None:
        return current
    
    # Try case-insensitive recursive search
    def find_key_recursive(obj, target_key):
        if isinstance(obj, dict):
            # Try exact match
            if target_key in obj:
                return obj[target_key]
            # Try case-insensitive
            for k, v in obj.items():
                if k.lower() == target_key.lower():
                    return v
            # Recurse
            for k, v in obj.items():
                result = find_key_recursive(v, target_key)
                if result is not None:
                    return result
        return None
    
    return find_key_recursive(data, column_path)


def set_value_in_jsonb(data: Dict, column_path: str, value: Any) -> None:
    """
    Set value in nested JSONB using dot notation
    Creates intermediate dicts if needed
    """
    keys = column_path.split('.')
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value


def evaluate_condition(value: Any, condition: str) -> bool:
    """
    Evaluate a condition against a value
    
    Supports:
    - Numeric: < 4, > 12, >= 5, <= 10, == 4, != 0
    - Compound: >= 4 and <= 12, < 0 or > 100
    - Text: == 'Positive', != 'Negative', in ['A', 'B']
    
    Args:
        value: The value to test
        condition: The condition string
    
    Returns:
        True if condition matches, False otherwise
    """
    condition = condition.strip()
    
    # Handle compound conditions (and, or)
    if ' and ' in condition.lower():
        parts = [p.strip() for p in condition.split(' and ')]
        return all(evaluate_condition(value, part) for part in parts)
    
    if ' or ' in condition.lower():
        parts = [p.strip() for p in condition.split(' or ')]
        return any(evaluate_condition(value, part) for part in parts)
    
    # Handle text matching with quotes
    if "'" in condition or '"' in condition:
        # Text comparison: == 'value', != 'value'
        if "==" in condition:
            _, text_value = condition.split("==")
            text_value = text_value.strip().strip("'\"")
            return str(value).strip() == text_value
        elif "!=" in condition:
            _, text_value = condition.split("!=")
            text_value = text_value.strip().strip("'\"")
            return str(value).strip() != text_value
        elif "in" in condition.lower():
            # in ['val1', 'val2']
            import re
            matches = re.findall(r"['\"](.*?)['\"]", condition)
            return str(value).strip() in matches
    
    # Numeric comparison
    try:
        # Try to convert value to float, handling various formats
        if value is None:
            return False
        
        # Handle string values - strip whitespace and convert
        if isinstance(value, str):
            value = value.strip()
            # Handle empty strings or non-numeric strings
            if not value or value.lower() in ['', 'n/a', 'na', 'none', 'null']:
                return False
        
        numeric_value = float(value)
        
        # Log successful conversion for debugging
        logger.debug(f"Converted value '{value}' to numeric: {numeric_value}")
        
    except (ValueError, TypeError) as e:
        # If can't convert to number, log and return False
        logger.warning(f"Could not convert value '{value}' to number: {e}")
        return False
    
    # Parse operator and threshold
    if condition.startswith("<="):
        threshold = float(condition[2:].strip())
        return numeric_value <= threshold
    elif condition.startswith(">="):
        threshold = float(condition[2:].strip())
        return numeric_value >= threshold
    elif condition.startswith("<"):
        threshold = float(condition[1:].strip())
        return numeric_value < threshold
    elif condition.startswith(">"):
        threshold = float(condition[1:].strip())
        return numeric_value > threshold
    elif condition.startswith("=="):
        threshold = float(condition[2:].strip())
        return numeric_value == threshold
    elif condition.startswith("!="):
        threshold = float(condition[2:].strip())
        return numeric_value != threshold
    
    return False
