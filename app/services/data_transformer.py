"""
Data Transformer Service
Converts parsed Excel/CSV data to database model format
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

from app.models import (
    Patient, 
    Diagnosis,
    LabTestDefinition,
    LabResultFlexible,
    DiseaseSpecificData
)


class DataTransformer:
    """Transform raw data to database model instances"""
    
    def __init__(self, db: Session):
        self.db = db
        self._load_test_definitions()
    
    def _load_test_definitions(self):
        """Load all lab test definitions from database"""
        tests = self.db.query(LabTestDefinition).all()
        
        # Create lookup maps
        self.tests_by_code = {test.test_code: test for test in tests}
        self.tests_by_id = {test.test_id: test for test in tests}
    
    def transform_patient_row(
        self, 
        row: pd.Series, 
        column_mapping: Dict[str, int],
        anonymized_patient: Dict,
        import_batch_id: str
    ) -> Tuple[Patient, List[LabResultFlexible]]:
        """
        Transform one row of Excel data into Patient + LabResults
        
        Args:
            row: Pandas Series from DataFrame
            column_mapping: Dict[column_name] -> test_id
            anonymized_patient: Output from PatientAnonymizer
            import_batch_id: UUID for batch tracking
        
        Returns:
            Tuple of (Patient instance, List of LabResult instances)
        """
        # Create Patient instance
        patient = Patient(
            anonymous_id=anonymized_patient['anonymous_id'],
            original_id_hash=anonymized_patient['original_id_hash'],
            age=anonymized_patient['age'],
            age_range=anonymized_patient['age_range'],
            gender=anonymized_patient['gender'],
            ethnicity=anonymized_patient['ethnicity'],
            contact_encrypted=anonymized_patient['contact_encrypted'],
            import_batch_id=import_batch_id,
            is_active=True,
            is_anonymized=True,
            additional_data=anonymized_patient['additional_data']
        )
        
        # Create LabResult instances
        lab_results = []
        
        for column_name, test_id in column_mapping.items():
            # Get test definition
            test = self.tests_by_id.get(test_id)
            if not test:
                continue
            
            # Get value from row
            raw_value = row.get(column_name)
            
            # Skip if no value
            if raw_value is None or pd.isna(raw_value):
                continue
            
            # Transform based on data type
            lab_result = self._create_lab_result(
                test=test,
                raw_value=raw_value,
                test_date=row.get('test_date') or row.get('date_diagnosed') or row.get('The first diagnosis')
            )
            
            if lab_result:
                lab_results.append(lab_result)
        
        return patient, lab_results
    
    def _create_lab_result(
        self, 
        test: LabTestDefinition, 
        raw_value: Any,
        test_date: Any
    ) -> Optional[LabResultFlexible]:
        """
        Create LabResultFlexible instance from raw value
        """
        # Parse test date
        if test_date and not pd.isna(test_date):
            try:
                if isinstance(test_date, str):
                    test_date = pd.to_datetime(test_date)
                elif isinstance(test_date, datetime):
                    pass
                else:
                    test_date = None
            except:
                test_date = None
        else:
            test_date = None
        
        # Determine value type and parse
        if test.data_type == 'numeric':
            value_numeric, value_text = self._parse_numeric_value(raw_value)
        elif test.data_type == 'qualitative':
            value_numeric = None
            value_text = self._parse_text_value(raw_value)
        else:
            # Mixed type - try numeric first
            value_numeric, value_text = self._parse_mixed_value(raw_value)
        
        # Must have at least one value
        if value_numeric is None and value_text is None:
            return None
        
        # Get reference range
        reference_range = test.default_reference_range
        
        # Determine if abnormal
        is_abnormal, abnormal_flag = self._check_abnormal(
            value_numeric, 
            value_text,
            reference_range
        )
        
        # Create lab result
        lab_result = LabResultFlexible(
            test_id=test.test_id,
            test_date=test_date,
            value_numeric=value_numeric,
            value_text=value_text,
            unit=test.unit,
            reference_range=reference_range,
            is_abnormal=is_abnormal,
            abnormal_flag=abnormal_flag,
            result_status='final'
        )
        
        return lab_result
    
    def _parse_numeric_value(self, raw_value: Any) -> Tuple[Optional[float], Optional[str]]:
        """
        Parse numeric value from raw input
        Returns (numeric_value, text_value)
        """
        if pd.isna(raw_value):
            return None, None
        
        try:
            # Handle strings like ">100", "<5", "≥10"
            value_str = str(raw_value).strip()
            
            # Check for comparison operators
            if value_str.startswith('>') or value_str.startswith('<') or value_str.startswith('≥') or value_str.startswith('≤'):
                # Store full string as text
                # Try to extract numeric part
                numeric_str = value_str.lstrip('><≥≤').strip()
                try:
                    numeric_val = float(numeric_str)
                    return numeric_val, value_str
                except:
                    return None, value_str
            
            # Try direct conversion
            numeric_val = float(raw_value)
            return numeric_val, str(raw_value)
            
        except:
            return None, str(raw_value)
    
    def _parse_text_value(self, raw_value: Any) -> Optional[str]:
        """Parse text value"""
        if pd.isna(raw_value):
            return None
        return str(raw_value).strip()
    
    def _parse_mixed_value(self, raw_value: Any) -> Tuple[Optional[float], Optional[str]]:
        """Parse value that could be numeric or text"""
        numeric_val, text_val = self._parse_numeric_value(raw_value)
        
        if numeric_val is not None:
            return numeric_val, text_val
        else:
            return None, self._parse_text_value(raw_value)
    
    def _check_abnormal(
        self, 
        value_numeric: Optional[float],
        value_text: Optional[str],
        reference_range: Optional[Dict]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if value is abnormal based on reference range
        Returns (is_abnormal, abnormal_flag)
        """
        if value_numeric is None or reference_range is None:
            return False, None
        
        # Extract reference range
        min_val = reference_range.get('min')
        max_val = reference_range.get('max')
        
        if min_val is None and max_val is None:
            return False, None
        
        # Check bounds
        is_abnormal = False
        abnormal_flag = None
        
        if min_val is not None and value_numeric < min_val:
            is_abnormal = True
            abnormal_flag = 'L'  # Low
        elif max_val is not None and value_numeric > max_val:
            is_abnormal = True
            abnormal_flag = 'H'  # High
        
        return is_abnormal, abnormal_flag
    
    def create_diagnosis(
        self,
        patient_id: int,
        disease_name: str,
        disease_code: Optional[str] = None,
        diagnosis_date: Optional[datetime] = None,
        severity: Optional[str] = None,
        is_primary: bool = True,
        created_by: int = 1
    ) -> Diagnosis:
        """
        Create Diagnosis instance
        """
        diagnosis = Diagnosis(
            patient_id=patient_id,
            disease_code=disease_code,
            disease_name=disease_name,
            diagnosis_date=diagnosis_date,
            is_primary=is_primary,
            severity=severity,
            created_by=created_by
        )
        return diagnosis
    
    def create_disease_specific_data(
        self,
        patient_id: int,
        disease_name: str,
        data_category: str,
        data: Dict,
        collection_date: Optional[datetime] = None,
        uploaded_by: int = 1
    ) -> DiseaseSpecificData:
        """
        Create DiseaseSpecificData instance for JSONB storage
        """
        disease_data = DiseaseSpecificData(
            patient_id=patient_id,
            disease_name=disease_name,
            data_category=data_category,
            data=data,
            collection_date=collection_date,
            uploaded_by=uploaded_by
        )
        return disease_data
    
    def extract_unmapped_data(
        self,
        row: pd.Series,
        unmapped_columns: List[str]
    ) -> Dict:
        """
        Extract unmapped columns into JSONB format
        Can be stored in additional_data or disease_specific_data
        """
        unmapped_data = {}
        
        for col in unmapped_columns:
            value = row.get(col)
            if value is not None and not pd.isna(value):
                # Convert numpy types to Python types
                if isinstance(value, (pd.Timestamp, datetime)):
                    unmapped_data[col] = value.isoformat()
                elif hasattr(value, 'item'):  # numpy scalar
                    unmapped_data[col] = value.item()
                else:
                    unmapped_data[col] = value
        
        return unmapped_data if unmapped_data else None
    
    def validate_patient_data(self, patient: Patient) -> List[str]:
        """
        Validate patient data quality
        Returns list of error messages (empty if valid)
        """
        errors = []
        
        # Check required fields
        if not patient.anonymous_id:
            errors.append("Missing anonymous_id")
        if not patient.original_id_hash:
            errors.append("Missing original_id_hash")
        
        # Validate age
        if patient.age is not None:
            if patient.age < 0 or patient.age > 120:
                errors.append(f"Invalid age: {patient.age}")
        
        # Validate gender
        if patient.gender and patient.gender not in ['Male', 'Female', 'Other']:
            errors.append(f"Invalid gender: {patient.gender}")
        
        return errors
    
    def validate_lab_result(self, lab_result: LabResultFlexible) -> List[str]:
        """
        Validate lab result data quality
        Returns list of error messages (empty if valid)
        """
        errors = []
        
        # Check required fields
        if not lab_result.test_id:
            errors.append("Missing test_id")
        
        # Check value constraint (at least one value required)
        if lab_result.value_numeric is None and lab_result.value_text is None and lab_result.value_jsonb is None:
            errors.append("Missing all value fields (at least one required)")
        
        # Validate numeric range
        if lab_result.value_numeric is not None:
            if lab_result.value_numeric < -1e10 or lab_result.value_numeric > 1e10:
                errors.append(f"Numeric value out of reasonable range: {lab_result.value_numeric}")
        
        return errors


# Usage example
if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base
    
    # Create test database session
    engine = create_engine("postgresql://usm_db_admin:USMDBPASSWORD@localhost:5432/usm_autoimmune_registry")
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Create transformer
    transformer = DataTransformer(db)
    
    # Test with sample row
    sample_row = pd.Series({
        'Hospitalization number': 'D1902107',
        'Age': 34,
        'Gender': 'Female',
        'ANA': 'Positive',
        'Anti_dsDNA': 156.7,
        'C3': 0.68,
        'C4': 0.15,
        'test_date': '2024-01-15'
    })
    
    # Sample column mapping
    column_mapping = {
        'ANA': 1,  # Assuming test_id=1 for ANA
        'Anti_dsDNA': 2,
        'C3': 3,
        'C4': 4
    }
    
    # Sample anonymized patient
    anonymized_patient = {
        'anonymous_id': 'USMA-2026-0001',
        'original_id_hash': 'abc123...',
        'age': 34,
        'age_range': '30-39',
        'gender': 'Female',
        'ethnicity': None,
        'contact_encrypted': None,
        'additional_data': None
    }
    
    # Transform
    patient, lab_results = transformer.transform_patient_row(
        sample_row,
        column_mapping,
        anonymized_patient,
        'batch-2026-001'
    )
    
    print(f"Patient: {patient.anonymous_id}, Age {patient.age}")
    print(f"Lab Results: {len(lab_results)} tests")
    for result in lab_results:
        print(f"  Test {result.test_id}: {result.value_numeric or result.value_text}")
    
    db.close()
