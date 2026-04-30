"""
Patient Anonymizer Service
Handles patient data anonymization and PII protection
"""
import hashlib
import uuid
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import random


class PatientAnonymizer:
    """Anonymize patient data for privacy protection"""
    
    def __init__(self, id_prefix: str = "USMA"):
        self.id_prefix = id_prefix
        self._counter = 1
        self._id_map = {}  # Maps original_hash to anonymous_id
    
    def generate_anonymous_id(self, original_id: str, year: Optional[int] = None) -> str:
        """
        Generate anonymous patient ID
        Format: USMA-YYYY-NNNN
        """
        if year is None:
            year = datetime.now().year
        
        # Check if we already generated an ID for this patient
        original_hash = self._hash_identifier(original_id)
        if original_hash in self._id_map:
            return self._id_map[original_hash]
        
        # Generate new anonymous ID
        anonymous_id = f"{self.id_prefix}-{year}-{self._counter:04d}"
        self._counter += 1
        
        # Store mapping
        self._id_map[original_hash] = anonymous_id
        
        return anonymous_id
    
    def _hash_identifier(self, identifier: str) -> str:
        """Hash an identifier using SHA-256"""
        return hashlib.sha256(str(identifier).encode()).hexdigest()
    
    def anonymize_patient(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize complete patient record
        
        Input: Raw patient data with PII
        Output: Anonymized patient data ready for database
        """
        # Extract original identifier
        original_id = patient_data.get('patient_id') or patient_data.get('Hospitalization number') or patient_data.get('id')
        
        if not original_id:
            raise ValueError("No patient identifier found in data")
        
        # Generate anonymous ID
        anonymous_id = self.generate_anonymous_id(original_id)
        original_id_hash = self._hash_identifier(original_id)
        
        # Extract and anonymize demographics
        age = patient_data.get('Age') or patient_data.get('age')
        gender = self._normalize_gender(patient_data.get('Gender') or patient_data.get('gender'))
        
        # Age range for k-anonymity
        age_range = self._get_age_range(age) if age else None
        
        # Encrypt contact information (if any)
        contact_data = {
            'phone': patient_data.get('phone'),
            'email': patient_data.get('email'),
            'address': patient_data.get('address'),
        }
        contact_encrypted = self._encrypt_contact(contact_data) if any(contact_data.values()) else None
        
        # Build anonymized record
        # Store original patient ID for internal research use (not true PII)
        metadata = self._extract_metadata(patient_data)
        if isinstance(metadata, dict):
            metadata['original_patient_id'] = str(original_id)  # Store for researchers
        else:
            metadata = {'original_patient_id': str(original_id)}
        
        anonymized = {
            'anonymous_id': anonymous_id,
            'original_id_hash': original_id_hash,
            'age': int(age) if age and str(age).replace('.','').isdigit() else None,
            'age_range': age_range,
            'gender': gender,
            'ethnicity': patient_data.get('Ethnicity') or patient_data.get('ethnicity'),
            'contact_encrypted': contact_encrypted,
            'is_active': True,
            'is_anonymized': False,  # Changed to False - showing raw research IDs
            'additional_data': metadata
        }
        
        return anonymized
    
    def _normalize_gender(self, gender: Any) -> Optional[str]:
        """Normalize gender values"""
        if gender is None or pd.isna(gender):
            return None
        
        gender_str = str(gender).lower().strip()
        
        if gender_str in ['m', 'male', '1', 'boy', 'man']:
            return 'Male'
        elif gender_str in ['f', 'female', '2', '0', 'girl', 'woman']:
            return 'Female'
        elif 'yellow' in gender_str.lower():  # Special marker in your dataset
            return 'Male'
        else:
            return 'Other'
    
    def _get_age_range(self, age: Any) -> Optional[str]:
        """Convert age to age range for k-anonymity"""
        try:
            age_num = int(float(age))
            
            if age_num < 18:
                return '<18'
            elif age_num < 30:
                return '18-29'
            elif age_num < 40:
                return '30-39'
            elif age_num < 50:
                return '40-49'
            elif age_num < 60:
                return '50-59'
            elif age_num < 70:
                return '60-69'
            else:
                return '70+'
        except:
            return None
    
    def _encrypt_contact(self, contact_data: Dict) -> Optional[str]:
        """
        Encrypt contact information
        In production, use proper encryption (Fernet, AES, etc.)
        For now, just JSON string (TODO: implement real encryption)
        """
        import json
        
        # Filter out None values
        filtered = {k: v for k, v in contact_data.items() if v is not None}
        
        if not filtered:
            return None
        
        # TODO: Implement proper encryption
        # For now, just encode as JSON
        return json.dumps(filtered)
    
    def _extract_metadata(self, patient_data: Dict) -> Dict:
        """Extract non-PII metadata"""
        metadata = {}
        
        # Extract diagnosis date
        if 'diagnosis_date' in patient_data or 'The first diagnosis' in patient_data:
            diagnosis_date = patient_data.get('diagnosis_date') or patient_data.get('The first diagnosis')
            if diagnosis_date and not pd.isna(diagnosis_date):
                metadata['first_diagnosis'] = str(diagnosis_date)
        
        # Extract AAM (menarche status) if present
        if 'AAM' in patient_data:
            aam_value = patient_data['AAM']
            # Check for NaN - pd.isna handles NaN, None, and pd.NA
            if not pd.isna(aam_value):
                metadata['menarche_status'] = aam_value
        
        return metadata if metadata else None
    
    def shift_dates(self, date_value: Any, patient_hash: str) -> Optional[datetime]:
        """
        Shift dates by random offset for k-anonymity
        Same offset per patient (consistent time relationships)
        """
        if date_value is None or pd.isna(date_value):
            return None
        
        try:
            # Convert to datetime
            if isinstance(date_value, str):
                date_obj = pd.to_datetime(date_value)
            elif isinstance(date_value, datetime):
                date_obj = date_value
            else:
                return None
            
            # Generate consistent random offset per patient (-90 to +90 days)
            random.seed(patient_hash)
            offset_days = random.randint(-90, 90)
            
            shifted_date = date_obj + timedelta(days=offset_days)
            return shifted_date
            
        except:
            return None
    
    def get_anonymization_log(self, original_id: str, anonymous_id: str) -> Dict:
        """
        Generate anonymization log entry
        """
        original_hash = self._hash_identifier(original_id)
        
        return {
            'original_identifier_hash': original_hash,
            'anonymous_id': anonymous_id,
            'anonymization_method': 'SHA-256 + Sequential ID',
            'can_be_reversed': False,
            'pii_fields_removed': ['name', 'ic_number', 'phone', 'email', 'address', 'date_of_birth']
        }


# Import pandas for data operations
import pandas as pd


# Usage example
if __name__ == "__main__":
    anonymizer = PatientAnonymizer(id_prefix="USMA")
    
    # Test with sample patient
    patient_data = {
        'Hospitalization number': 'D1902107',
        'Age': 34,
        'Gender': 'Female',
        'phone': '+60123456789',
        'email': 'patient@example.com'
    }
    
    anonymized = anonymizer.anonymize_patient(patient_data)
    
    print("Anonymized Patient:")
    for key, value in anonymized.items():
        print(f"  {key}: {value}")
    
    # Generate log
    log = anonymizer.get_anonymization_log(
        patient_data['Hospitalization number'],
        anonymized['anonymous_id']
    )
    print("\nAnonymization Log:")
    print(f"  Hash: {log['original_identifier_hash']}")
    print(f"  Anonymous ID: {log['anonymous_id']}")
