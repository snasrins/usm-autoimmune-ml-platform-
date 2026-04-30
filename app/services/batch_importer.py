"""
Batch Importer Service
Orchestrates complete data import pipeline with transaction management
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, DataError

from app.models import (
    Patient,
    Diagnosis,
    LabResultFlexible,
    DiseaseSpecificData,
    UploadedFile,
    DataIngestionAudit
)
from app.services.file_parser import FileParser
from app.services.column_mapper import ColumnMapper
from app.services.anonymizer import PatientAnonymizer
from app.services.data_transformer import DataTransformer


class BatchImporter:
    """Import patient data in batches with full transaction control"""
    
    def __init__(self, db: Session, user_id: int = 1):
        self.db = db
        self.user_id = user_id
        
        # Initialize services
        self.file_parser = None  # Created per file
        self.column_mapper = ColumnMapper(db)
        self.anonymizer = PatientAnonymizer(id_prefix="USMA")
        self.transformer = DataTransformer(db)
        
        # Import statistics
        self.stats = {
            'patients_imported': 0,
            'lab_results_imported': 0,
            'diagnoses_imported': 0,
            'disease_data_imported': 0,
            'errors': [],
            'warnings': []
        }
    
    def import_file(
        self,
        file_path: str,
        disease_name: str,
        dataset_type: str,
        disease_code: Optional[str] = None,
        auto_approve_tests: bool = False
    ) -> Dict[str, Any]:
        """
        Main entry point for file import
        
        Args:
            file_path: Path to Excel/CSV file
            disease_name: Disease name (e.g., 'SLE', 'Sjogren')
            dataset_type: Dataset identifier (e.g., 'SLE', 'SJOGREN')
            disease_code: ICD-10 code (e.g., 'M32.1')
            auto_approve_tests: If True, create new test definitions automatically
        
        Returns:
            Dict with import results and statistics
        """
        start_time = time.time()
        batch_id = str(uuid.uuid4())
        
        # Reset statistics
        self._reset_stats()
        
        try:
            # Phase 1: Parse file
            print("\n[Phase 1/5] Parsing file...")
            self.file_parser = FileParser(file_path)
            validation_result = self.file_parser.validate_file()
            
            if not validation_result['valid']:
                return self._create_error_response(
                    f"File validation failed: {validation_result['error']}",
                    batch_id
                )
            
            df = self.file_parser.parse()
            print(f"✓ Parsed {len(df)} rows, {len(df.columns)} columns")
            
            # Phase 2: Map columns
            print("\n[Phase 2/5] Mapping columns to lab tests...")
            mapping_result = self.column_mapper.map_columns(df.columns.tolist())
            
            mapped_count = len(mapping_result['mapped'])
            unmapped_count = len(mapping_result['unmapped'])
            low_confidence_count = len(mapping_result['low_confidence'])
            
            print(f"✓ Mapped: {mapped_count}, Unmapped: {unmapped_count}, Low confidence: {low_confidence_count}")
            
            # Handle unmapped columns
            if unmapped_count > 0:
                if auto_approve_tests:
                    print(f"\n  Auto-creating {unmapped_count} new test definitions...")
                    new_tests = self._create_new_tests(mapping_result['unmapped'])
                    # Update mapping result
                    for col_name, test in new_tests.items():
                        mapping_result['mapped'][col_name] = {
                            'test_code': test.test_code,
                            'test_id': test.test_id,
                            'confidence': 1.0,
                            'match_type': 'auto_created'
                        }
                    print(f"✓ Created {len(new_tests)} new tests")
                else:
                    self.stats['warnings'].append(
                        f"{unmapped_count} unmapped columns require admin approval"
                    )
            
            # Create column->test_id mapping
            column_mapping = {
                col: mapping_result['mapped'][col]['test_id']
                for col in mapping_result['mapped']
            }
            
            # Store unmapped columns for JSONB
            unmapped_columns = mapping_result['unmapped']  # Already a list
            
            # Phase 3: Create file record
            print("\n[Phase 3/5] Creating file record...")
            uploaded_file = self._create_file_record(
                validation_result,
                dataset_type,
                mapping_result,
                batch_id
            )
            self.db.add(uploaded_file)
            self.db.flush()  # Get file_id
            
            file_id = uploaded_file.file_id
            print(f"✓ File record created (ID: {file_id})")
            
            # Commit file record so it survives if import fails
            self.db.commit()
            
            # Phase 4: Import patients and lab results
            print(f"\n[Phase 4/5] Importing {len(df)} patients...")
            self._import_patients_batch(
                df,
                column_mapping,
                unmapped_columns,
                disease_name,
                disease_code,
                batch_id
            )
            
            # Phase 5: Create audit log
            print("\n[Phase 5/5] Creating audit log...")
            execution_time_ms = int((time.time() - start_time) * 1000)
            audit = self._create_audit_log(
                file_id,
                batch_id,
                'import',
                'success',
                self.stats['patients_imported'],
                execution_time_ms
            )
            self.db.add(audit)
            
            # Re-fetch file record to update it (may be detached after earlier commit)
            uploaded_file = self.db.query(UploadedFile).filter(
                UploadedFile.file_id == file_id
            ).first()
            
            # Update file record
            uploaded_file.upload_status = 'completed'
            uploaded_file.import_stats = {
                'patients': self.stats['patients_imported'],
                'lab_results': self.stats['lab_results_imported'],
                'diagnoses': self.stats['diagnoses_imported'],
                'disease_data': self.stats['disease_data_imported'],
                'errors': len(self.stats['errors']),
                'warnings': len(self.stats['warnings'])
            }
            
            # Commit transaction
            self.db.commit()
            
            print(f"\n✓ Import completed successfully!")
            print(f"  Patients: {self.stats['patients_imported']}")
            print(f"  Lab results: {self.stats['lab_results_imported']}")
            print(f"  Diagnoses: {self.stats['diagnoses_imported']}")
            print(f"  Time: {execution_time_ms/1000:.2f}s")
            
            return self._create_success_response(
                batch_id,
                file_id,
                execution_time_ms
            )
            
        except Exception as e:
            # Rollback transaction
            self.db.rollback()
            
            print(f"\n✗ Import failed: {str(e)}")
            
            # Log error and update file status
            if 'file_id' in locals():
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Update file status to failed
                try:
                    uploaded_file = self.db.query(UploadedFile).filter(
                        UploadedFile.file_id == file_id
                    ).first()
                    if uploaded_file:
                        uploaded_file.upload_status = 'failed'
                        uploaded_file.validation_errors = {'error': str(e)}
                except:
                    pass  # File record might not exist
                
                # Create error audit log
                audit = self._create_audit_log(
                    file_id,
                    batch_id,
                    'import',
                    'error',
                    0,
                    execution_time_ms,
                    error_message=str(e)
                )
                self.db.add(audit)
                self.db.commit()
            
            return self._create_error_response(str(e), batch_id)
    
    def _import_patients_batch(
        self,
        df,
        column_mapping: Dict[str, int],
        unmapped_columns: List[str],
        disease_name: str,
        disease_code: Optional[str],
        batch_id: str
    ):
        """Import patients in batch with progress tracking"""
        total_rows = len(df)
        
        for idx, row in df.iterrows():
            try:
                # Progress indicator
                if (idx + 1) % 10 == 0:
                    print(f"  Processing patient {idx + 1}/{total_rows}...")
                
                # Anonymize patient
                patient_data = row.to_dict()
                anonymized = self.anonymizer.anonymize_patient(patient_data)
                
                # Transform to model
                patient, lab_results = self.transformer.transform_patient_row(
                    row,
                    column_mapping,
                    anonymized,
                    batch_id
                )
                
                # Validate
                patient_errors = self.transformer.validate_patient_data(patient)
                if patient_errors:
                    self.stats['errors'].append(
                        f"Row {idx + 1}: {', '.join(patient_errors)}"
                    )
                    continue
                
                # Insert patient
                self.db.add(patient)
                self.db.flush()  # Get patient_id
                
                patient_id = patient.id
                self.stats['patients_imported'] += 1
                
                # Insert diagnosis
                if disease_name:
                    # Parse diagnosis date safely
                    diagnosis_date = self._parse_date_safely(
                        row.get('The first diagnosis') or row.get('diagnosis_date')
                    )
                    diagnosis = self.transformer.create_diagnosis(
                        patient_id=patient_id,
                        disease_name=disease_name,
                        disease_code=disease_code,
                        diagnosis_date=diagnosis_date,
                        is_primary=True,
                        created_by=self.user_id
                    )
                    self.db.add(diagnosis)
                    self.stats['diagnoses_imported'] += 1
                
                # Insert lab results
                for lab_result in lab_results:
                    lab_result.patient_id = patient_id
                    lab_result.uploaded_by = self.user_id
                    
                    # Validate
                    result_errors = self.transformer.validate_lab_result(lab_result)
                    if result_errors:
                        self.stats['warnings'].append(
                            f"Row {idx + 1}, Test {lab_result.test_id}: {', '.join(result_errors)}"
                        )
                        continue
                    
                    self.db.add(lab_result)
                    self.stats['lab_results_imported'] += 1
                
                # Store unmapped data in JSONB
                if unmapped_columns:
                    unmapped_data = self.transformer.extract_unmapped_data(row, unmapped_columns)
                    if unmapped_data:
                        disease_data = self.transformer.create_disease_specific_data(
                            patient_id=patient_id,
                            disease_name=disease_name,
                            data_category='unmapped_fields',
                            data=unmapped_data,
                            uploaded_by=self.user_id
                        )
                        self.db.add(disease_data)
                        self.stats['disease_data_imported'] += 1
                
            except Exception as e:
                # Rollback this patient's transaction
                self.db.rollback()
                self.stats['errors'].append(f"Row {idx + 1}: {str(e)}")
                continue
    
    def _parse_date_safely(self, date_value: Any) -> Optional[datetime]:
        """Parse date value safely, return None if invalid"""
        import pandas as pd
        
        if date_value is None or pd.isna(date_value):
            return None
        
        # Check if it looks like a date (not a yes/no string)
        date_str = str(date_value).strip()
        
        # Skip obvious non-dates
        if any(word in date_str.lower() for word in ['yes', 'no', 'yellow']):
            return None
        
        try:
            # Try to parse as date
            if isinstance(date_value, str):
                parsed = pd.to_datetime(date_value)
            elif isinstance(date_value, datetime):
                parsed = date_value
            else:
                parsed = pd.to_datetime(date_value)
            
            # Sanity check - must be reasonable year
            if parsed.year < 1900 or parsed.year > 2100:
                return None
            
            return parsed
        except:
            return None
    
    def _create_new_tests(self, unmapped: List[str]) -> Dict:
        """Create new test definitions from unmapped columns"""
        from app.models import LabTestDefinition
        
        new_tests = {}
        suggestions = self.column_mapper.suggest_new_tests(unmapped)
        
        for suggestion in suggestions:
            test = LabTestDefinition(
                test_code=suggestion['test_code'],
                test_name=suggestion['test_name'],
                test_category=suggestion['suggested_category'],
                data_type=suggestion['suggested_data_type'],
                unit=None,
                default_reference_range=None,
                relevant_diseases=['Unknown'],
                is_active=True
            )
            self.db.add(test)
            self.db.flush()
            
            new_tests[suggestion['original_column']] = test
        
        return new_tests
    
    def _create_file_record(
        self,
        validation_result: Dict,
        dataset_type: str,
        mapping_result: Dict,
        batch_id: str
    ) -> UploadedFile:
        """Create UploadedFile record"""
        metadata = self.file_parser.get_metadata()
        
        uploaded_file = UploadedFile(
            original_filename=validation_result['filename'],
            stored_filename=f"{batch_id}.{validation_result['file_extension']}",
            file_path=validation_result['file_path'],
            file_size_bytes=validation_result['file_size'],
            file_type=validation_result['file_extension'].upper(),
            file_hash=validation_result['file_hash'],
            row_count=metadata['row_count'],
            column_count=metadata['column_count'],
            column_mapping={
                'mapped': mapping_result['mapped'],
                'unmapped': mapping_result['unmapped'],  # Already a list
                'low_confidence': mapping_result['low_confidence']
            },
            upload_status='processing',
            dataset_type=dataset_type,
            uploaded_by=self.user_id
        )
        
        return uploaded_file
    
    def _create_audit_log(
        self,
        file_id: int,
        batch_id: str,
        action_type: str,
        action_status: str,
        records_affected: int,
        execution_time_ms: int,
        error_message: Optional[str] = None
    ) -> DataIngestionAudit:
        """Create DataIngestionAudit record"""
        audit = DataIngestionAudit(
            file_id=file_id,
            batch_id=batch_id,
            action_type=action_type,
            action_status=action_status,
            records_affected=records_affected,
            execution_time_ms=execution_time_ms,
            error_message=error_message,
            performed_by=self.user_id
        )
        
        return audit
    
    def _reset_stats(self):
        """Reset import statistics"""
        self.stats = {
            'patients_imported': 0,
            'lab_results_imported': 0,
            'diagnoses_imported': 0,
            'disease_data_imported': 0,
            'errors': [],
            'warnings': []
        }
    
    def _create_success_response(self, batch_id: str, file_id: int, execution_time_ms: int) -> Dict:
        """Create success response"""
        return {
            'success': True,
            'batch_id': batch_id,
            'file_id': file_id,
            'statistics': {
                'patients_imported': self.stats['patients_imported'],
                'lab_results_imported': self.stats['lab_results_imported'],
                'diagnoses_imported': self.stats['diagnoses_imported'],
                'disease_data_imported': self.stats['disease_data_imported'],
                'error_count': len(self.stats['errors']),
                'warning_count': len(self.stats['warnings'])
            },
            'errors': self.stats['errors'],
            'warnings': self.stats['warnings'],
            'execution_time_ms': execution_time_ms
        }
    
    def _create_error_response(self, error_message: str, batch_id: str) -> Dict:
        """Create error response"""
        return {
            'success': False,
            'batch_id': batch_id,
            'error': error_message,
            'statistics': self.stats
        }


# Usage example
if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create database session
    engine = create_engine("postgresql://usm_db_admin:USMDBPASSWORD@172.24.175.24:5432/usm_autoimmune_registry")
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Create importer
        importer = BatchImporter(db, user_id=1)
        
        # Import file
        result = importer.import_file(
            file_path="/path/to/AAM-SLE-E (real data).xlsx",
            disease_name="Systemic Lupus Erythematosus",
            dataset_type="SLE",
            disease_code="M32.1",
            auto_approve_tests=False  # Set True to auto-create new tests
        )
        
        print("\n=== Import Result ===")
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Batch ID: {result['batch_id']}")
            print(f"File ID: {result['file_id']}")
            print(f"Patients: {result['statistics']['patients_imported']}")
            print(f"Lab Results: {result['statistics']['lab_results_imported']}")
            print(f"Time: {result['execution_time_ms']/1000:.2f}s")
        else:
            print(f"Error: {result['error']}")
        
    finally:
        db.close()
