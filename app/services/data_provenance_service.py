"""
Data Provenance Tracking Service
Tracks complete lineage of data transformations from upload to ML training
Ensures reproducible ML experiments
"""
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging
import json

from app.models.flexible_data import FlexibleDatasetWide, ImportPreviewStaging

logger = logging.getLogger(__name__)


class DataProvenanceService:
    """
    Track data lineage and transformations for reproducibility
    
    Provenance Chain:
    1. Upload → import_preview_staging
    2. Layer 5 Preprocessing → tracking in staging
    3. Save → flexible_dataset_wide (with metadata)
    4. ML Training → track model provenance
    
    Benefits:
    - Reproducible ML experiments
    - Debugging data quality issues
    - Audit trail for compliance
    - Understanding data transformations
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_upload_provenance(
        self,
        import_batch_id: uuid.UUID,
        dataset_type: str,
        source_file: str,
        uploaded_by: int,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Record provenance for data upload
        
        Args:
            import_batch_id: Unique batch identifier
            dataset_type: Type of dataset (structured/semistructured/unstructured)
            source_file: Original filename
            uploaded_by: User ID
            metadata: Additional metadata
        
        Returns:
            Provenance record
        """
        provenance = {
            'stage': 'upload',
            'import_batch_id': str(import_batch_id),
            'dataset_type': dataset_type,
            'source_file': source_file,
            'uploaded_by': uploaded_by,
            'uploaded_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        logger.info(f"Recorded upload provenance: {import_batch_id} from {source_file}")
        
        return provenance
    
    def record_preprocessing_provenance(
        self,
        session_id: uuid.UUID,
        operations: List[Dict],
        user_id: int,
        preprocessing_metadata: Dict
    ) -> Dict:
        """
        Record provenance for Layer 5 preprocessing
        
        Args:
            session_id: Preview session ID
            operations: List of preprocessing operations applied
            user_id: User who applied preprocessing
            preprocessing_metadata: Complete preprocessing metadata
        
        Returns:
            Provenance record
        """
        provenance = {
            'stage': 'layer_5_preprocessing',
            'session_id': str(session_id),
            'operations': operations,
            'applied_by': user_id,
            'applied_at': datetime.now().isoformat(),
            'preprocessing_metadata': preprocessing_metadata,
            'operation_count': len(operations),
            'operation_types': list(set([op.get('operation') for op in operations]))
        }
        
        logger.info(
            f"Recorded preprocessing provenance: {session_id} "
            f"with {len(operations)} operations"
        )
        
        return provenance
    
    def record_save_to_wide_table_provenance(
        self,
        import_batch_id: uuid.UUID,
        dataset_type: str,
        record_count: int,
        preprocessing_applied: bool,
        preprocessing_provenance: Optional[Dict] = None
    ) -> Dict:
        """
        Record provenance when saving to flexible_dataset_wide
        
        Args:
            import_batch_id: Import batch ID
            dataset_type: Dataset type
            record_count: Number of records saved
            preprocessing_applied: Whether Layer 5 preprocessing was applied
            preprocessing_provenance: Preprocessing provenance if available
        
        Returns:
            Provenance record
        """
        provenance = {
            'stage': 'save_to_wide_table',
            'import_batch_id': str(import_batch_id),
            'dataset_type': dataset_type,
            'record_count': record_count,
            'preprocessing_applied': preprocessing_applied,
            'saved_at': datetime.now().isoformat(),
            'preprocessing_provenance': preprocessing_provenance
        }
        
        logger.info(
            f"Recorded save provenance: {import_batch_id} "
            f"({record_count} records, preprocessing={preprocessing_applied})"
        )
        
        return provenance
    
    def record_ml_training_provenance(
        self,
        import_batch_id: uuid.UUID,
        dataset_type: str,
        model_name: str,
        model_version: str,
        training_params: Dict,
        feature_engineering_applied: List[str],
        ml_preprocessing_applied: Dict,
        trained_by: int
    ) -> Dict:
        """
        Record provenance for ML training
        
        Args:
            import_batch_id: Source data batch ID
            dataset_type: Dataset type
            model_name: Name of trained model
            model_version: Model version
            training_params: Training parameters
            feature_engineering_applied: List of features engineered
            ml_preprocessing_applied: ML preprocessing steps
            trained_by: User ID
        
        Returns:
            Provenance record
        """
        provenance = {
            'stage': 'ml_training',
            'import_batch_id': str(import_batch_id),
            'dataset_type': dataset_type,
            'model_name': model_name,
            'model_version': model_version,
            'training_params': training_params,
            'feature_engineering_applied': feature_engineering_applied,
            'ml_preprocessing_applied': ml_preprocessing_applied,
            'trained_by': trained_by,
            'trained_at': datetime.now().isoformat()
        }
        
        logger.info(
            f"Recorded ML training provenance: {model_name}/{model_version} "
            f"from batch {import_batch_id}"
        )
        
        return provenance
    
    def get_complete_provenance_chain(
        self,
        import_batch_id: uuid.UUID
    ) -> Dict:
        """
        Get complete provenance chain for a dataset
        
        Args:
            import_batch_id: Import batch ID to trace
        
        Returns:
            Complete provenance chain from upload to ML training
        """
        logger.info(f"Retrieving complete provenance chain for batch {import_batch_id}")
        
        # Query flexible_dataset_wide for records
        records = self.db.query(FlexibleDatasetWide).filter(
            FlexibleDatasetWide.import_batch_id == import_batch_id
        ).all()
        
        if not records:
            logger.warning(f"No records found for batch {import_batch_id}")
            return {
                'import_batch_id': str(import_batch_id),
                'found': False,
                'message': 'No records found for this batch'
            }
        
        # Extract provenance from JSONB data
        provenance_chain = {
            'import_batch_id': str(import_batch_id),
            'dataset_type': records[0].dataset_type,
            'record_count': len(records),
            'created_at': records[0].created_at.isoformat(),
            'stages': []
        }
        
        # Stage 1: Upload (from metadata if available)
        sample_data = records[0].data or {}
        if '_upload_metadata' in sample_data:
            provenance_chain['stages'].append({
                'stage': 'upload',
                'data': sample_data['_upload_metadata']
            })
        
        # Stage 2: Layer 5 Preprocessing (from metadata)
        if '_preprocessing_applied' in sample_data:
            provenance_chain['stages'].append({
                'stage': 'layer_5_preprocessing',
                'data': sample_data['_preprocessing_applied']
            })
        
        # Stage 3: Structured Tests Transformation (from metadata)
        if '_structured_tests_transformed' in sample_data:
            provenance_chain['stages'].append({
                'stage': 'structured_tests_transformation',
                'data': sample_data['_structured_tests_transformed']
            })
        
        # Stage 4: Labeling (from metadata)
        if '_labeling_metadata' in sample_data:
            provenance_chain['stages'].append({
                'stage': 'labeling',
                'data': sample_data['_labeling_metadata']
            })
        
        # Stage 5: Feature Engineering (from metadata if ML training happened)
        if '_feature_engineering_metadata' in sample_data:
            provenance_chain['stages'].append({
                'stage': 'feature_engineering',
                'data': sample_data['_feature_engineering_metadata']
            })
        
        # Stage 6: ML Training (from metadata if available)
        if '_ml_training_metadata' in sample_data:
            provenance_chain['stages'].append({
                'stage': 'ml_training',
                'data': sample_data['_ml_training_metadata']
            })
        
        logger.info(
            f"Retrieved provenance chain with {len(provenance_chain['stages'])} stages"
        )
        
        return provenance_chain
    
    def validate_provenance_completeness(
        self,
        import_batch_id: uuid.UUID,
        required_stages: Optional[List[str]] = None
    ) -> Dict:
        """
        Validate that provenance chain is complete
        
        Args:
            import_batch_id: Batch ID to validate
            required_stages: List of required stages (default: all)
        
        Returns:
            Validation result with missing stages
        """
        if required_stages is None:
            required_stages = [
                'upload',
                'layer_5_preprocessing',
                'structured_tests_transformation',
                'labeling',
                'feature_engineering',
                'ml_training'
            ]
        
        chain = self.get_complete_provenance_chain(import_batch_id)
        
        if not chain.get('found', True):
            return {
                'valid': False,
                'message': 'Batch not found',
                'missing_stages': required_stages
            }
        
        present_stages = [stage['stage'] for stage in chain.get('stages', [])]
        missing_stages = [stage for stage in required_stages if stage not in present_stages]
        
        result = {
            'valid': len(missing_stages) == 0,
            'import_batch_id': str(import_batch_id),
            'required_stages': required_stages,
            'present_stages': present_stages,
            'missing_stages': missing_stages,
            'completeness_percentage': (len(present_stages) / len(required_stages)) * 100 if required_stages else 100
        }
        
        if result['valid']:
            logger.info(f"Provenance chain complete for batch {import_batch_id}")
        else:
            logger.warning(
                f"Provenance chain incomplete for batch {import_batch_id}: "
                f"missing {missing_stages}"
            )
        
        return result
    
    def export_provenance_report(
        self,
        import_batch_id: uuid.UUID,
        format: str = 'json'
    ) -> str:
        """
        Export provenance chain as report
        
        Args:
            import_batch_id: Batch ID
            format: 'json' or 'markdown'
        
        Returns:
            Formatted provenance report
        """
        chain = self.get_complete_provenance_chain(import_batch_id)
        
        if format == 'json':
            return json.dumps(chain, indent=2)
        
        elif format == 'markdown':
            report = f"# Data Provenance Report\n\n"
            report += f"**Import Batch ID:** {chain['import_batch_id']}\n"
            report += f"**Dataset Type:** {chain.get('dataset_type', 'Unknown')}\n"
            report += f"**Record Count:** {chain.get('record_count', 0)}\n"
            report += f"**Created At:** {chain.get('created_at', 'Unknown')}\n\n"
            report += f"## Transformation Stages\n\n"
            
            for i, stage in enumerate(chain.get('stages', []), 1):
                report += f"### {i}. {stage['stage'].replace('_', ' ').title()}\n\n"
                report += f"```json\n{json.dumps(stage['data'], indent=2)}\n```\n\n"
            
            return report
        
        else:
            raise ValueError(f"Unknown format: {format}")
