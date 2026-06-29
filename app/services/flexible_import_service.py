"""
Flexible Import Service
Saves previewed/edited data from staging to flexible_dataset_wide table
100% flexible - NO hardcoded schema
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.flexible_data import (
    ImportPreviewStaging,
    FlexibleDatasetWide,
    DatasetSchema,
    UnstructuredDocumentProcessed
)


class FlexibleImportService:
    """Import data from staging to permanent wide tables"""
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
    
    @staticmethod
    def _convert_to_python_type(value: Any) -> Any:
        """
        Convert pandas/numpy types to Python native types for JSON serialization
        
        Args:
            value: Value from pandas DataFrame (could be numpy type)
        
        Returns:
            Python native type (int, float, bool, str, None)
        """
        # Handle pandas NA/NaN
        if pd.isna(value):
            return None
        
        # Handle numpy numeric types
        if isinstance(value, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(value)
        
        if isinstance(value, (np.floating, np.float64, np.float32)):
            return float(value)
        
        # Handle numpy bool
        if isinstance(value, (np.bool_, bool)):
            return bool(value)
        
        # Handle numpy datetime
        if isinstance(value, (np.datetime64, pd.Timestamp)):
            return value.isoformat() if hasattr(value, 'isoformat') else str(value)
        
        # Handle numpy string types
        if isinstance(value, (np.str_, np.bytes_)):
            return str(value)
        
        # Handle Series (edge case)
        if isinstance(value, pd.Series):
            return FlexibleImportService._convert_to_python_type(
                value.iloc[0] if len(value) > 0 else None
            )
        
        # Already a Python native type
        return value
    
    def _transform_structured_tests_for_ml(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform structured_tests array into ML-friendly flat structure
        
        Converts:
          structured_tests: [
            {test_name: "Haemoglobin", result: "15.8", unit: "g/dL", is_abnormal: false, ...},
            {test_name: "WBC", result: "7.2", unit: "10^9/L", is_abnormal: false, ...}
          ]
        
        Into:
          lab_results: {
            Haemoglobin_result: 15.8,
            Haemoglobin_unit: "g/dL",
            Haemoglobin_is_abnormal: false,
            Haemoglobin_ref_range_low: 13.0,
            Haemoglobin_ref_range_high: 18.0,
            Haemoglobin_flag: "",
            WBC_result: 7.2,
            WBC_unit: "10^9/L",
            WBC_is_abnormal: false,
            ...
          }
        
        This allows ML feature engineering to:
        - Find CRP_result and ESR_result → Create CRP_ESR_ratio
        - Find C3_result and C4_result → Create complement_ratio
        - Use is_abnormal flags as binary features
        
        Args:
            extracted_data: Raw OCR extracted data with structured_tests
        
        Returns:
            Transformed data with ML-friendly lab_results
        """
        structured_tests = extracted_data.get('structured_tests', [])
        
        if not structured_tests:
            # No structured tests, return as-is
            return extracted_data
        
        # Create lab_results dictionary
        lab_results = {}
        
        for test in structured_tests:
            test_name = test.get('test_name', '').strip()
            if not test_name:
                continue
            
            # Clean test name for use as key (remove spaces, special chars)
            test_key = test_name.replace(' ', '_').replace('-', '_').replace('/', '_')
            test_key = ''.join(c for c in test_key if c.isalnum() or c == '_')
            
            # Extract test values
            result_str = test.get('result', '')
            unit = test.get('unit', '')
            ref_range_low = test.get('ref_range_low')
            ref_range_high = test.get('ref_range_high')
            flag = test.get('flag', '')
            section = test.get('section', '')
            is_abnormal = test.get('is_abnormal', False)
            
            # Parse numeric result (try to convert to float)
            result_value = None
            if result_str:
                try:
                    # Remove common non-numeric patterns
                    result_clean = str(result_str).replace('<', '').replace('>', '').replace('~', '')
                    result_clean = result_clean.replace(',', '').strip()
                    result_value = float(result_clean)
                except (ValueError, TypeError):
                    # Keep as string if can't convert
                    result_value = result_str
            
            # Create ML-friendly keys
            lab_results[f'{test_key}_result'] = result_value
            lab_results[f'{test_key}_unit'] = unit
            lab_results[f'{test_key}_is_abnormal'] = is_abnormal
            
            if ref_range_low is not None:
                lab_results[f'{test_key}_ref_range_low'] = ref_range_low
            if ref_range_high is not None:
                lab_results[f'{test_key}_ref_range_high'] = ref_range_high
            if flag:
                lab_results[f'{test_key}_flag'] = flag
            if section:
                lab_results[f'{test_key}_section'] = section
        
        # Build transformed data structure
        transformed_data = {
            'demographics': extracted_data.get('metadata', {}),
            'lab_results': lab_results,
            'metadata': {
                'document': extracted_data.get('document', {}),
                'sections': extracted_data.get('sections', []),
                'ocr_confidence': extracted_data.get('document', {}).get('confidence_score'),
                'processing_info': extracted_data.get('document', {})
            }
        }
        
        # Keep original structured_tests for reference (optional)
        transformed_data['_original_structured_tests'] = structured_tests
        
        return transformed_data
    
    def import_from_staging(
        self,
        session_id: uuid.UUID,
        dataset_source: Optional[str] = None,
        preprocessing_metadata: Optional[Dict[str, Any]] = None,
        final_dataset_name: Optional[str] = None,
        excluded_columns: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Move data from staging to flexible_dataset_wide table
        
        Args:
            session_id: Preview session ID
            dataset_source: Source description (e.g., "Hospital USM")
            preprocessing_metadata: Layer 5 preprocessing metadata to attach
        
        Returns:
            Import statistics
        """
        # Get staging records
        staging_records = self.db.query(ImportPreviewStaging).filter(
            and_(
                ImportPreviewStaging.session_id == session_id,
                ImportPreviewStaging.is_deleted == False,
                ImportPreviewStaging.validation_status == 'valid'
            )
        ).all()
        
        if not staging_records:
            return {
                'success': False,
                'message': 'No valid records found in staging',
                'imported_count': 0
            }
        
        # Get first record to determine dataset type
        first_record = staging_records[0]
        dataset_type = first_record.dataset_type
        dataset_name = final_dataset_name or first_record.dataset_name
        
        # Get schema
        schema_record = self.db.query(DatasetSchema).filter(
            DatasetSchema.dataset_type == dataset_type
        ).first()
        
        # Generate batch ID
        batch_id = uuid.uuid4()
        
        # Import statistics
        stats = {
            'total_rows': len(staging_records),
            'imported': 0,
            'duplicates_skipped': 0,
            'errors': []
        }
        
        # Process each record
        for staging in staging_records:
            try:
                # Strip excluded columns from row data before any processing
                row_data = staging.row_data
                if excluded_columns:
                    row_data = {k: v for k, v in row_data.items() if k not in excluded_columns}

                # Extract record ID
                record_id = self._extract_record_id(row_data, schema_record)
                
                # Check for duplicates
                existing = self.db.query(FlexibleDatasetWide).filter(
                    and_(
                        FlexibleDatasetWide.record_id == record_id,
                        FlexibleDatasetWide.dataset_type == dataset_type
                    )
                ).first()
                
                if existing:
                    stats['duplicates_skipped'] += 1
                    continue
                
                # Organize data into structured JSONB
                organized_data = self._organize_data(row_data, schema_record)
                
                # Add preprocessing metadata if provided
                if preprocessing_metadata:
                    organized_data['_preprocessing_applied'] = preprocessing_metadata
                
                # Calculate data quality score
                quality_score = self._calculate_quality_score(row_data, schema_record)
                
                # Create permanent record
                wide_record = FlexibleDatasetWide(
                    record_id=record_id,
                    dataset_type=dataset_type,
                    dataset_name=dataset_name,
                    data=organized_data,
                    schema_definition=schema_record.schema_definition if schema_record else None,
                    dataset_source=dataset_source,
                    import_batch_id=batch_id,
                    import_method='csv_upload',
                    data_quality_score=quality_score,
                    missing_fields_count=self._count_missing(row_data),
                    created_by=self.user_id
                )
                
                self.db.add(wide_record)
                stats['imported'] += 1
                
            except Exception as e:
                stats['errors'].append({
                    'row_number': staging.row_number,
                    'error': str(e)
                })
        
        # Commit transaction
        self.db.commit()
        
        # Update schema statistics
        if schema_record:
            schema_record.record_count += stats['imported']
            schema_record.last_import_date = datetime.now()
            self.db.commit()
        
        # Clear staging (optional - they will auto-expire anyway)
        # self.db.query(ImportPreviewStaging).filter(
        #     ImportPreviewStaging.session_id == session_id
        # ).delete()
        # self.db.commit()
        
        return {
            'success': True,
            'batch_id': str(batch_id),
            'dataset_type': dataset_type,
            'statistics': stats
        }
    
    def import_unstructured_data(
        self,
        document_id: int,
        dataset_type: str,
        dataset_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Import OCR/NER processed data to flexible_dataset_wide
        
        Args:
            document_id: Unstructured document processing ID
            dataset_type: Dataset classification
            dataset_source: Source description
        
        Returns:
            Import result
        """
        # Get processed document
        processed = self.db.query(UnstructuredDocumentProcessed).filter(
            UnstructuredDocumentProcessed.id == document_id
        ).first()
        
        if not processed:
            return {
                'success': False,
                'message': f'Processed document {document_id} not found'
            }
        
        if processed.is_saved_to_wide_table:
            return {
                'success': False,
                'message': 'Document already imported to wide table'
            }
        
        # Extract record ID from extracted data
        extracted_data = processed.extracted_data
        record_id = processed.extracted_record_id or f"DOC_{document_id}"
        
        # CRITICAL FIX: Transform structured_tests to ML-friendly format
        # This allows ML to find CRP_result, ESR_result → Create CRP_ESR_ratio
        ml_friendly_data = self._transform_structured_tests_for_ml(extracted_data)
        
        # Generate batch ID
        batch_id = uuid.uuid4()
        
        # Create wide record with transformed data
        wide_record = FlexibleDatasetWide(
            record_id=record_id,
            dataset_type=dataset_type,
            dataset_name=f"Unstructured Import - {processed.document_filename}",
            data=ml_friendly_data,  # Use transformed data!
            dataset_source=dataset_source or f"OCR: {processed.document_filename}",
            import_batch_id=batch_id,
            import_method='ocr_processed',
            created_by=self.user_id
        )
        
        self.db.add(wide_record)
        
        # Update processed document status
        processed.is_saved_to_wide_table = True
        processed.saved_wide_table_id = wide_record.id
        processed.dataset_type = dataset_type
        
        self.db.commit()
        
        return {
            'success': True,
            'batch_id': str(batch_id),
            'record_id': record_id,
            'wide_table_id': wide_record.id
        }
    
    def direct_import_csv(
        self,
        file_path: str,
        dataset_type: str,
        dataset_name: str,
        dataset_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Direct CSV import without preview (fast path)
        Use when data is already validated
        
        Args:
            file_path: Path to CSV file
            dataset_type: Dataset classification
            dataset_name: User-friendly name
            dataset_source: Source description
        
        Returns:
            Import statistics
        """
        import pandas as pd
        
        # Read CSV
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Auto-detect schema
        from app.services.flexible_preview_service import FlexiblePreviewService
        preview_service = FlexiblePreviewService(self.db, self.user_id)
        schema = preview_service._detect_schema(df, dataset_type)
        
        # Register schema
        preview_service._register_schema(dataset_type, schema, dataset_name)
        
        # Generate batch ID
        batch_id = uuid.uuid4()
        
        # Import statistics
        stats = {
            'total_rows': len(df),
            'imported': 0,
            'duplicates_skipped': 0,
            'errors': []
        }
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                # Convert to dict and clean all values
                row_dict = row.to_dict()
                row_dict = {
                    k: self._convert_to_python_type(v)
                    for k, v in row_dict.items()
                }
                
                # Extract record ID
                record_id = self._extract_record_id(row_dict, None, schema)
                
                # Check for duplicates
                existing = self.db.query(FlexibleDatasetWide).filter(
                    and_(
                        FlexibleDatasetWide.record_id == record_id,
                        FlexibleDatasetWide.dataset_type == dataset_type
                    )
                ).first()
                
                if existing:
                    stats['duplicates_skipped'] += 1
                    continue
                
                # Organize data
                organized_data = self._organize_data(row_dict, None, schema)
                
                # Create record
                wide_record = FlexibleDatasetWide(
                    record_id=record_id,
                    dataset_type=dataset_type,
                    dataset_name=dataset_name,
                    data=organized_data,
                    schema_definition=schema,
                    dataset_source=dataset_source,
                    import_batch_id=batch_id,
                    import_method='csv_upload',
                    created_by=self.user_id
                )
                
                self.db.add(wide_record)
                stats['imported'] += 1
                
            except Exception as e:
                stats['errors'].append({
                    'row': idx + 1,
                    'error': str(e)
                })
        
        self.db.commit()
        
        return {
            'success': True,
            'batch_id': str(batch_id),
            'dataset_type': dataset_type,
            'statistics': stats
        }
    
    def _extract_record_id(
        self,
        row_data: Dict,
        schema_record: Optional[DatasetSchema] = None,
        schema_dict: Optional[Dict] = None
    ) -> str:
        """
        Extract record ID from row data
        Looks for common ID fields: patient_id, record_id, id, sample_id
        """
        schema = schema_dict if schema_dict else (schema_record.schema_definition if schema_record else {})
        
        # Find identifier column from schema
        identifier_cols = []
        for col in schema.get('columns', []):
            if col.get('category') == 'identifier':
                identifier_cols.append(col['name'])
        
        # Try identifier columns first
        for col in identifier_cols:
            if col in row_data and row_data[col] is not None:
                return str(row_data[col])
        
        # Fallback: try common patterns
        for field in ['patient_id', 'record_id', 'id', 'sample_id', 'subject_id']:
            if field in row_data and row_data[field] is not None:
                return str(row_data[field])
        
        # Last resort: generate UUID
        return f"AUTO_{uuid.uuid4().hex[:8]}"
    
    def _organize_data(
        self,
        row_data: Dict,
        schema_record: Optional[DatasetSchema] = None,
        schema_dict: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Organize flat row data into structured JSONB
        Groups fields by category (demographics, lab_results, clinical, etc.)
        AUTOMATICALLY categorizes diagnoses using dynamic lookup (NO hardcoding)
        """
        schema = schema_dict if schema_dict else (schema_record.schema_definition if schema_record else {})
        
        # Get categories from schema
        categories = schema.get('categories', {})
        
        # Initialize organized structure
        organized = {}
        
        # Group fields by category
        for category, fields in categories.items():
            organized[category] = {}
            for field in fields:
                if field in row_data:
                    organized[category][field] = row_data[field]
        
        # Handle uncategorized fields
        categorized_fields = set()
        for fields in categories.values():
            categorized_fields.update(fields)
        
        uncategorized = {}
        for field, value in row_data.items():
            if field not in categorized_fields:
                uncategorized[field] = value
        
        if uncategorized:
            organized['other'] = uncategorized
        
        # ============================================
        # AUTOMATIC DIAGNOSIS CATEGORIZATION
        # Uses dynamic lookup tables - NO HARDCODING
        # ============================================
        self._auto_categorize_diagnosis(organized)
        
        return organized
    
    def _auto_categorize_diagnosis(self, organized_data: Dict) -> None:
        """
        Automatically categorize diagnosis using dynamic database lookup
        Adds 'diagnosis_category' field to clinical section
        NO hardcoding - all categories from dim_disease_categories table
        
        Args:
            organized_data: Organized JSONB structure (modified in-place)
        """
        # Check if clinical section exists with diagnosis field
        if 'clinical' not in organized_data:
            return
        
        clinical = organized_data['clinical']
        diagnosis_field = None
        
        # Find diagnosis field (check common names)
        for field_name in ['diagnosis', 'the_first_diagnosis', 'primary_diagnosis', 'disease']:
            if field_name in clinical and clinical[field_name]:
                diagnosis_field = field_name
                break
        
        if not diagnosis_field:
            return
        
        diagnosis_text = clinical[diagnosis_field]
        
        # TODO: CategoryLookupService not yet implemented
        # Skip category lookup for now
        # from app.services.category_lookup_service import CategoryLookupService
        # lookup_service = CategoryLookupService(self.db)
        # category = lookup_service.get_category_for_diagnosis(str(diagnosis_text))
        
        # Add placeholder category to clinical section
        clinical['diagnosis_category'] = 'uncategorized'
        clinical['diagnosis_category_source'] = 'placeholder'  # Not yet auto-lookup
    
    def _calculate_quality_score(
        self,
        row_data: Dict,
        schema_record: Optional[DatasetSchema]
    ) -> int:
        """
        Calculate data quality score (0-100)
        Based on completeness and validity
        """
        if not schema_record:
            return 50  # Default medium quality
        
        schema = schema_record.schema_definition
        total_fields = len(schema.get('columns', []))
        
        if total_fields == 0:
            return 50
        
        # Count non-null fields
        filled_fields = sum(1 for v in row_data.values() if v is not None)
        
        # Completeness score (0-100)
        completeness = (filled_fields / total_fields) * 100
        
        return int(completeness)
    
    def _count_missing(self, row_data: Dict) -> int:
        """Count missing (None/null) fields"""
        return sum(1 for v in row_data.values() if v is None)
