"""
Unstructured to Tabular Conversion Service
Converts OCR-extracted medical entities to tabular format for preview/editing
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.flexible_data import ImportPreviewStaging


class UnstructuredToTabularService:
    """Convert unstructured OCR results to tabular format"""
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
    
    def convert_from_validation_queue(
        self,
        validation_id: int,
        dataset_type: str,
        conversion_mode: str = "grouped"
    ) -> Dict[str, Any]:
        """
        Convert OCR result from unstructured_document_processed to tabular preview
        
        Args:
            validation_id: ID from unstructured_document_processed table
            dataset_type: Dataset classification (e.g., 'SLE_OCR', 'LabReport')
            conversion_mode: 'grouped' (one row with all entities) or 'individual' (one row per entity)
        
        Returns:
            {
                'session_id': uuid,
                'dataset_type': str,
                'row_count': int,
                'conversion_mode': str
            }
        """
        # Fetch OCR result from unstructured_document_processed
        query = text("""
            SELECT 
                extracted_data
            FROM unstructured_document_processed
            WHERE id = :validation_id
        """)
        
        result = self.db.execute(query, {"validation_id": validation_id}).fetchone()
        
        if not result:
            raise ValueError(f"OCR record {validation_id} not found")
        
        validation_data = result[0]
        
        # Extract entities and metadata
        medical_entities = validation_data.get('medical_entities', [])
        structured_tests = validation_data.get('structured_tests', [])  # NEW: Structured test rows
        metadata = validation_data.get('metadata', {})
        document_info = validation_data.get('document', {})
        extracted_text = validation_data.get('extracted_text', '')
        
        # PRIORITY 1: Use structured tests if available (proper table structure)
        if structured_tests:
            rows = self._convert_from_structured_tests(
                structured_tests, metadata, document_info
            )
        # FALLBACK 1: Use medical_entities if available (flat format)
        elif medical_entities:
            # Convert based on mode
            if conversion_mode == "grouped":
                rows = self._convert_grouped(medical_entities, metadata, document_info)
            else:
                rows = self._convert_individual(medical_entities, metadata, document_info)
        # FALLBACK 2: No structured data - create single row with raw text
        else:
            rows = [{
                'source_document': document_info.get('filename', 'Unknown'),
                'document_type': document_info.get('file_type', 'unknown'),
                'source_path': document_info.get('source_path', ''),
                'extracted_text': extracted_text[:5000] if extracted_text else '',  # Truncate for preview
                'text_length': len(extracted_text) if extracted_text else 0,
                'page_count': document_info.get('page_count', 0),
                'ocr_confidence': document_info.get('confidence_score', 0.0),
                'ocr_engine': document_info.get('ocr_engine', 'Unknown'),
                'processing_time_s': document_info.get('processing_time_s', 0.0),
                'vram_used_mb': document_info.get('vram_used_mb', 0.0),
                'entity_count': 0,
                'note': 'No structured entities extracted - raw text available'
            }]
        
        # Create preview session
        session_id = uuid.uuid4()
        expires_at = datetime.now() + timedelta(hours=24)
        
        # Insert rows into staging
        preview_records = []
        for row_num, row_data in enumerate(rows, 1):
            staging_record = ImportPreviewStaging(
                session_id=session_id,
                dataset_type=dataset_type,
                dataset_name=f"OCR: {document_info.get('filename', 'Unknown')}",
                row_data=row_data,
                row_number=row_num,
                validation_status='valid',
                validation_errors=None,
                expires_at=expires_at
            )
            preview_records.append(staging_record)
        
        self.db.bulk_save_objects(preview_records)
        self.db.commit()
        
        return {
            'session_id': str(session_id),
            'dataset_type': dataset_type,
            'row_count': len(rows),
            'conversion_mode': conversion_mode,
            'source_validation_id': validation_id,
            'expires_at': expires_at.isoformat()
        }
    
    def _convert_from_structured_tests(
        self,
        tests: List[Dict],
        metadata: Dict,
        document_info: Dict
    ) -> List[Dict]:
        """
        NEW: Convert from structured test format (proper table structure)
        
        This creates ONE ROW PER TEST instead of one row with entity_0...entity_N
        
        Input tests: [
            {
                "test_name": "Haemoglobin",
                "test_name_cn": "血红蛋白",
                "result": "15.8",
                "unit": "g/dL",
                "ref_range_low": 13.0,
                "ref_range_high": 18.0,
                "flag": "",
                "section": "HAEMATOLOGY",
                "is_abnormal": False
            },
            ...
        ]
        
        Output rows: One row per test with all metadata preserved
        """
        rows = []
        
        # Common metadata to add to each row
        common_data = {
            'source_document': document_info.get('filename', 'Unknown'),
            'document_type': document_info.get('file_type', 'pdf'),
            'ocr_engine': document_info.get('ocr_engine', 'Qwen3-VL-2B-Instruct'),
            'ocr_confidence': document_info.get('confidence_score', 0.0),
            'page_count': document_info.get('page_count', 1),
            'processing_time_s': document_info.get('processing_time_s', 0.0),
            
            # Patient metadata
            'lab_no': metadata.get('lab_no', ''),
            'mrn': metadata.get('mrn', ''),
            'patient_name': metadata.get('patient_name', ''),
            'gender': metadata.get('gender', ''),
            'age': metadata.get('age', ''),
            'dob': metadata.get('dob', ''),
            
            # Lab metadata
            'facility': metadata.get('facility', ''),
            'branch': metadata.get('branch', ''),
            'location': metadata.get('location', ''),
            'collected_date': metadata.get('collected_date', ''),
            'received_date': metadata.get('received_date', ''),
            'reported_date': metadata.get('reported_date', ''),
            'specimen_type': metadata.get('specimen_type', ''),
        }
        
        # Create one row per test
        for test in tests:
            row = common_data.copy()
            
            # Add test-specific data
            row.update({
                'test_name': test.get('test_name', ''),
                'test_name_cn': test.get('test_name_cn', ''),
                'result': test.get('result', ''),
                'result_operator': test.get('result_operator', ''),
                'unit': test.get('unit', ''),
                'ref_range_low': test.get('ref_range_low'),
                'ref_range_high': test.get('ref_range_high'),
                'ref_range_text': test.get('ref_range_text', ''),
                'flag': test.get('flag', ''),
                'section': test.get('section', ''),
                'is_abnormal': test.get('is_abnormal', False)
            })
            
            rows.append(row)
        
        return rows
    
    def _convert_grouped(
        self,
        entities: List[Dict],
        metadata: Dict,
        document_info: Dict
    ) -> List[Dict]:
        """
        Convert to grouped format - 100% FLEXIBLE (NO hardcoded fields)
        
        Strategy: Flatten ALL JSON keys to columns, no categorization
        
        Example output:
        {
            "source_document": "lab_report.pdf",
            "ocr_engine": "Qwen3-VL-2B",
            "ocr_confidence": 0.87,
            "entity_0_value": "Hemoglobin: 15.8 g/dL",
            "entity_1_value": "WBC: 6.5 x10^9/L",
            "entity_2_value": "SLE",
            ...
            "meta_key_1": "value1",  # Whatever metadata exists
            "meta_key_2": "value2",
            ...
        }
        """
        row = {}
        
        # Add document info (generic - no field assumptions)
        row['source_document'] = document_info.get('filename', 'unknown')
        row['document_type'] = 'ocr_processed'
        row['ocr_engine'] = document_info.get('ocr_engine', 'unknown')
        row['ocr_confidence'] = document_info.get('confidence_score', 0.0)
        row['page_count'] = document_info.get('page_count', 1)
        
        # Flatten ALL metadata keys (no assumptions about what exists)
        for key, value in metadata.items():
            if value:
                # Prefix with 'meta_' to avoid column name conflicts
                safe_key = f"meta_{key}"
                row[safe_key] = value
        
        # Flatten ALL entities as enumerated columns (no type categorization)
        for idx, entity in enumerate(entities):
            # Store raw entity value
            row[f"entity_{idx}_value"] = entity.get('value', '')
            row[f"entity_{idx}_type"] = entity.get('type', 'unknown')  # Keep original type for reference
            row[f"entity_{idx}_confidence"] = entity.get('confidence', 0.0)
            
            # If entity has parsed components, flatten those too
            if isinstance(entity.get('value'), dict):
                for comp_key, comp_value in entity['value'].items():
                    row[f"entity_{idx}_{comp_key}"] = comp_value
        
        return [row]  # Single row with all data flattened
    
    def _convert_individual(
        self,
        entities: List[Dict],
        metadata: Dict,
        document_info: Dict
    ) -> List[Dict]:
        """
        Convert to individual format - 100% FLEXIBLE (NO hardcoded fields)
        One row per entity, with all metadata attached
        
        Example output:
        [
            {
                "source_document": "lab_report.pdf",
                "entity_value": "Hemoglobin: 15.8 g/dL",
                "entity_type": "extracted_from_document",
                "entity_confidence": 0.9,
                "meta_key_1": "value1",  # All metadata attached to each row
                ...
            },
            {
                "source_document": "lab_report.pdf",
                "entity_value": "SLE",
                "entity_type": "extracted_from_document",
                "entity_confidence": 0.95,
                "meta_key_1": "value1",
                ...
            }
        ]
        """
        rows = []
        
        for entity in entities:
            row = {}
            
            # Add document info (same for all rows)
            row['source_document'] = document_info.get('filename', 'unknown')
            row['document_type'] = 'ocr_processed'
            row['ocr_engine'] = document_info.get('ocr_engine', 'unknown')
            row['ocr_confidence'] = document_info.get('confidence_score', 0.0)
            
            # Add entity data (NO type interpretation)
            row['entity_value'] = entity.get('value', '')
            row['entity_type'] = entity.get('type', 'extracted_from_document')  # Keep for reference
            row['entity_confidence'] = entity.get('confidence', 0.0)
            
            # Flatten ALL metadata (NO assumptions about fields)
            for key, value in metadata.items():
                if value:
                    safe_key = f"meta_{key}"
                    row[safe_key] = value
            
            rows.append(row)
        
        return rows
    
    # NOTE: _parse_lab_test() method REMOVED
    # Reason: Parsing lab tests is a HARDCODED assumption about medical data
    # In 100% flexible pipeline, we store RAW entity values
    # Users can parse/interpret in downstream analysis (Python/SQL/UI)
