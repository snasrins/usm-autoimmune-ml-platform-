"""
Query Service
Advanced query helpers for patient and lab result data
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, cast, String, desc, asc, case
from sqlalchemy.dialects.postgresql import JSONB

from app.models import (
    Patient,
    Diagnosis,
    LabTestDefinition,
    LabResultFlexible,
    DiseaseSpecificData
)


class QueryService:
    """Advanced query service for patient and lab data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========================================================================
    # Patient Queries
    # ========================================================================
    
    def get_patient_with_labs(
        self,
        patient_id: int,
        include_inactive: bool = False
    ) -> Optional[Dict]:
        """
        Get complete patient record with all lab results
        
        Args:
            patient_id: Patient ID
            include_inactive: Include inactive lab results
            
        Returns:
            Dict with patient info, diagnoses, and lab results
        """
        # Get patient with relationships
        query = self.db.query(Patient).options(
            joinedload(Patient.lab_results).joinedload(LabResultFlexible.test_definition),
            joinedload(Patient.diagnoses)
        ).filter(Patient.id == patient_id)
        
        if not include_inactive:
            query = query.filter(Patient.is_active == True)
        
        patient = query.first()
        
        if not patient:
            return None
        
        # Build response
        return {
            'patient': {
                'id': patient.id,
                'anonymous_id': patient.anonymous_id,
                'age': patient.age,
                'age_range': patient.age_range,
                'gender': patient.gender,
                'ethnicity': patient.ethnicity,
                'is_active': patient.is_active,
                'created_at': patient.created_at.isoformat() if patient.created_at else None
            },
            'diagnoses': [
                {
                    'diagnosis_id': d.diagnosis_id,
                    'disease_code': d.disease_code,
                    'disease_name': d.disease_name,
                    'diagnosis_date': d.diagnosis_date.isoformat() if d.diagnosis_date else None,
                    'is_primary': d.is_primary,
                    'severity': d.severity
                }
                for d in patient.diagnoses
            ],
            'lab_results': [
                {
                    'result_id': r.result_id,
                    'test_code': r.test_definition.test_code if r.test_definition else None,
                    'test_name': r.test_definition.test_name if r.test_definition else None,
                    'test_date': r.test_date.isoformat() if r.test_date else None,
                    'value_numeric': float(r.value_numeric) if r.value_numeric else None,
                    'value_text': r.value_text,
                    'unit': r.unit,
                    'is_abnormal': r.is_abnormal,
                    'abnormal_flag': r.abnormal_flag
                }
                for r in patient.lab_results
            ]
        }
    
    def search_patients(
        self,
        disease_name: Optional[str] = None,
        disease_code: Optional[str] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        gender: Optional[str] = None,
        test_code: Optional[str] = None,
        test_abnormal: Optional[bool] = None,
        batch_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """
        Search patients with filters
        
        Args:
            disease_name: Filter by disease name (e.g., 'Lupus', 'Sjogren')
            disease_code: Filter by ICD-10 code
            age_min: Minimum age
            age_max: Maximum age
            gender: Filter by gender
            test_code: Filter patients with specific test
            test_abnormal: Filter by abnormal test results
            batch_id: Filter by import batch ID (UUID)
            limit: Results per page
            offset: Page offset
            
        Returns:
            Dict with patients list and total count
        """
        query = self.db.query(Patient).filter(Patient.is_active == True)
        
        # Batch ID filter (import batch)
        if batch_id:
            query = query.filter(Patient.import_batch_id == batch_id)
        
        # Disease filters
        if disease_name or disease_code:
            query = query.join(Patient.diagnoses)
            
            if disease_name:
                query = query.filter(
                    Diagnosis.disease_name.ilike(f'%{disease_name}%')
                )
            
            if disease_code:
                query = query.filter(Diagnosis.disease_code == disease_code)
        
        # Age filters
        if age_min is not None:
            query = query.filter(Patient.age >= age_min)
        
        if age_max is not None:
            query = query.filter(Patient.age <= age_max)
        
        # Gender filter
        if gender:
            query = query.filter(Patient.gender == gender)
        
        # Test filters
        if test_code or test_abnormal is not None:
            query = query.join(Patient.lab_results)
            
            if test_code:
                query = query.join(LabResultFlexible.test_definition).filter(
                    LabTestDefinition.test_code == test_code
                )
            
            if test_abnormal is not None:
                query = query.filter(LabResultFlexible.is_abnormal == test_abnormal)
        
        # Get total count
        total = query.distinct().count()
        
        # Get paginated results
        patients = query.distinct().order_by(
            Patient.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        return {
            'patients': [
                {
                    'id': p.id,
                    'patient_id': p.additional_data.get('original_patient_id') if p.additional_data else p.anonymous_id,  # Show original ID
                    'anonymous_id': p.anonymous_id,
                    'age': p.age,
                    'age_range': p.age_range,
                    'gender': p.gender,
                    'ethnicity': p.ethnicity,
                    'data_source': p.data_source,
                    'created_at': p.created_at.isoformat() if p.created_at else None
                }
                for p in patients
            ],
            'total': total,
            'limit': limit,
            'offset': offset
        }
    
    # ========================================================================
    # Lab Result Queries
    # ========================================================================
    
    def get_lab_trends(
        self,
        patient_id: int,
        test_code: Optional[str] = None,
        test_category: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get lab result trends over time for a patient
        
        Args:
            patient_id: Patient ID
            test_code: Filter by specific test
            test_category: Filter by test category
            date_from: Start date
            date_to: End date
            limit: Maximum results
            
        Returns:
            List of lab results ordered by date
        """
        query = self.db.query(LabResultFlexible).join(
            LabResultFlexible.test_definition
        ).filter(
            LabResultFlexible.patient_id == patient_id
        )
        
        # Test filters
        if test_code:
            query = query.filter(LabTestDefinition.test_code == test_code)
        
        if test_category:
            query = query.filter(LabTestDefinition.test_category == test_category)
        
        # Date filters
        if date_from:
            query = query.filter(LabResultFlexible.test_date >= date_from)
        
        if date_to:
            query = query.filter(LabResultFlexible.test_date <= date_to)
        
        # Order by date
        results = query.order_by(
            LabResultFlexible.test_date.asc()
        ).limit(limit).all()
        
        return [
            {
                'result_id': r.result_id,
                'test_code': r.test_definition.test_code,
                'test_name': r.test_definition.test_name,
                'test_category': r.test_definition.test_category,
                'test_date': r.test_date.isoformat() if r.test_date else None,
                'value_numeric': float(r.value_numeric) if r.value_numeric else None,
                'value_text': r.value_text,
                'unit': r.unit,
                'is_abnormal': r.is_abnormal,
                'abnormal_flag': r.abnormal_flag,
                'reference_range': r.reference_range
            }
            for r in results
        ]
    
    def get_abnormal_results(
        self,
        patient_id: int,
        severity: Optional[str] = None  # 'H', 'HH', 'L', 'LL'
    ) -> List[Dict]:
        """
        Get all abnormal lab results for a patient
        
        Args:
            patient_id: Patient ID
            severity: Filter by severity flag
            
        Returns:
            List of abnormal results
        """
        query = self.db.query(LabResultFlexible).join(
            LabResultFlexible.test_definition
        ).filter(
            LabResultFlexible.patient_id == patient_id,
            LabResultFlexible.is_abnormal == True
        )
        
        if severity:
            query = query.filter(LabResultFlexible.abnormal_flag == severity)
        
        results = query.order_by(
            LabResultFlexible.test_date.desc()
        ).all()
        
        return [
            {
                'result_id': r.result_id,
                'test_code': r.test_definition.test_code,
                'test_name': r.test_definition.test_name,
                'test_date': r.test_date.isoformat() if r.test_date else None,
                'value_numeric': float(r.value_numeric) if r.value_numeric else None,
                'value_text': r.value_text,
                'unit': r.unit,
                'abnormal_flag': r.abnormal_flag,
                'reference_range': r.reference_range
            }
            for r in results
        ]
    
    def compare_test_results(
        self,
        patient_ids: List[int],
        test_code: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict:
        """
        Compare test results across multiple patients
        
        Args:
            patient_ids: List of patient IDs
            test_code: Test to compare
            date_from: Start date
            date_to: End date
            
        Returns:
            Dict with comparison data
        """
        query = self.db.query(
            LabResultFlexible.patient_id,
            Patient.anonymous_id,
            LabResultFlexible.test_date,
            LabResultFlexible.value_numeric,
            LabResultFlexible.value_text,
            LabResultFlexible.is_abnormal
        ).join(
            LabResultFlexible.test_definition
        ).join(
            LabResultFlexible.patient
        ).filter(
            LabResultFlexible.patient_id.in_(patient_ids),
            LabTestDefinition.test_code == test_code
        )
        
        if date_from:
            query = query.filter(LabResultFlexible.test_date >= date_from)
        
        if date_to:
            query = query.filter(LabResultFlexible.test_date <= date_to)
        
        results = query.order_by(
            LabResultFlexible.patient_id,
            LabResultFlexible.test_date
        ).all()
        
        # Group by patient
        comparison = {}
        for r in results:
            if r.anonymous_id not in comparison:
                comparison[r.anonymous_id] = []
            
            comparison[r.anonymous_id].append({
                'test_date': r.test_date.isoformat() if r.test_date else None,
                'value_numeric': float(r.value_numeric) if r.value_numeric else None,
                'value_text': r.value_text,
                'is_abnormal': r.is_abnormal
            })
        
        return comparison
    
    # ========================================================================
    # JSONB Queries
    # ========================================================================
    
    def query_disease_data(
        self,
        disease_name: str,
        data_category: Optional[str] = None,
        jsonb_filter: Optional[Dict] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Query disease-specific JSONB data
        
        Args:
            disease_name: Disease name
            data_category: Data category filter
            jsonb_filter: JSONB key-value filters (e.g., {'symptom': 'fever'})
            limit: Maximum results
            
        Returns:
            List of disease data records
        """
        query = self.db.query(DiseaseSpecificData).filter(
            DiseaseSpecificData.disease_name.ilike(f'%{disease_name}%')
        )
        
        if data_category:
            query = query.filter(DiseaseSpecificData.data_category == data_category)
        
        # JSONB filters
        if jsonb_filter:
            for key, value in jsonb_filter.items():
                query = query.filter(
                    DiseaseSpecificData.data[key].astext == str(value)
                )
        
        results = query.limit(limit).all()
        
        return [
            {
                'data_id': r.data_id,
                'patient_id': r.patient_id,
                'disease_name': r.disease_name,
                'data_category': r.data_category,
                'data': r.data,
                'collection_date': r.collection_date.isoformat() if r.collection_date else None
            }
            for r in results
        ]
    
    # ========================================================================
    # Statistics & Aggregations
    # ========================================================================
    
    def get_test_statistics(
        self,
        test_code: str,
        disease_name: Optional[str] = None
    ) -> Dict:
        """
        Get statistics for a specific test across all patients
        
        Args:
            test_code: Test code
            disease_name: Filter by disease (optional)
            
        Returns:
            Dict with mean, median, std, min, max, abnormal_rate
        """
        query = self.db.query(
            func.avg(LabResultFlexible.value_numeric).label('mean'),
            func.percentile_cont(0.5).within_group(
                LabResultFlexible.value_numeric
            ).label('median'),
            func.stddev(LabResultFlexible.value_numeric).label('std'),
            func.min(LabResultFlexible.value_numeric).label('min'),
            func.max(LabResultFlexible.value_numeric).label('max'),
            func.count(LabResultFlexible.result_id).label('total'),
            func.sum(
                case((LabResultFlexible.is_abnormal == True, 1), else_=0)
            ).label('abnormal_count')
        ).join(
            LabResultFlexible.test_definition
        ).filter(
            LabTestDefinition.test_code == test_code,
            LabResultFlexible.value_numeric.isnot(None)
        )
        
        # Filter by disease if specified
        if disease_name:
            query = query.join(
                LabResultFlexible.patient
            ).join(
                Patient.diagnoses
            ).filter(
                Diagnosis.disease_name.ilike(f'%{disease_name}%')
            )
        
        result = query.first()
        
        if not result or result.total == 0:
            return None
        
        abnormal_rate = (result.abnormal_count / result.total * 100) if result.abnormal_count else 0
        
        return {
            'test_code': test_code,
            'statistics': {
                'mean': float(result.mean) if result.mean else None,
                'median': float(result.median) if result.median else None,
                'std': float(result.std) if result.std else None,
                'min': float(result.min) if result.min else None,
                'max': float(result.max) if result.max else None,
                'total_results': result.total,
                'abnormal_count': result.abnormal_count or 0,
                'abnormal_rate': round(abnormal_rate, 2)
            }
        }
    
    def get_patient_summary(self, patient_id: int) -> Dict:
        """
        Get comprehensive patient summary
        
        Args:
            patient_id: Patient ID
            
        Returns:
            Dict with patient overview statistics
        """
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        
        if not patient:
            return None
        
        # Count diagnoses
        diagnosis_count = self.db.query(func.count(Diagnosis.diagnosis_id)).filter(
            Diagnosis.patient_id == patient_id
        ).scalar()
        
        # Count lab results
        total_results = self.db.query(func.count(LabResultFlexible.result_id)).filter(
            LabResultFlexible.patient_id == patient_id
        ).scalar()
        
        abnormal_results = self.db.query(func.count(LabResultFlexible.result_id)).filter(
            LabResultFlexible.patient_id == patient_id,
            LabResultFlexible.is_abnormal == True
        ).scalar()
        
        # Get date range
        date_range = self.db.query(
            func.min(LabResultFlexible.test_date),
            func.max(LabResultFlexible.test_date)
        ).filter(
            LabResultFlexible.patient_id == patient_id
        ).first()
        
        # Get unique test types
        unique_tests = self.db.query(
            func.count(func.distinct(LabResultFlexible.test_id))
        ).filter(
            LabResultFlexible.patient_id == patient_id
        ).scalar()
        
        return {
            'patient_id': patient.id,
            'anonymous_id': patient.anonymous_id,
            'age': patient.age,
            'gender': patient.gender,
            'summary': {
                'total_diagnoses': diagnosis_count,
                'total_lab_results': total_results,
                'abnormal_results': abnormal_results,
                'abnormal_rate': round((abnormal_results / total_results * 100), 2) if total_results > 0 else 0,
                'unique_tests': unique_tests,
                'first_test_date': date_range[0].isoformat() if date_range[0] else None,
                'last_test_date': date_range[1].isoformat() if date_range[1] else None
            }
        }
