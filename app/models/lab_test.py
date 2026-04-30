"""
Lab Test Models - Flexible lab results with EAV + JSONB pattern
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean, Numeric, Text, Index
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class LabTestDefinition(Base):
    """Catalog of all known lab tests"""
    __tablename__ = "lab_test_definitions"
    
    test_id = Column(Integer, primary_key=True, index=True)
    test_code = Column(String(50), unique=True, nullable=False, index=True)  # wbc, crp, il12_p70, etc.
    test_name = Column(String(200), nullable=False)  # "White Blood Cell Count", "IL-12 p70", etc.
    test_category = Column(String(100), index=True)  # Hematology, Immunology, Cytokine, etc.
    
    # Reference ranges (can vary by age/gender)
    default_reference_range = Column(JSONB)
    # Example: {"min": 3.5, "max": 9.5, "unit": "10^9/L", "gender": "all", "age_min": 18}
    
    unit = Column(String(50))  # 10^9/L, mg/L, AU/ml, etc.
    data_type = Column(String(20))  # numeric, qualitative, text
    
    # Related diseases
    relevant_diseases = Column(ARRAY(Text))  # ['SLE', 'Sjogren', 'RA']
    
    # Metadata
    description = Column(Text)
    alternative_names = Column(JSONB)  # ["WBC", "Leukocyte Count"]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    results = relationship("LabResultFlexible", back_populates="test_definition")
    
    def __repr__(self):
        return f"<LabTest {self.test_code}: {self.test_name}>"


class LabResultFlexible(Base):
    """Flexible lab results storage - handles any test type"""
    __tablename__ = "lab_results_flexible"
    
    result_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    test_id = Column(Integer, ForeignKey("lab_test_definitions.test_id"), nullable=False)
    test_date = Column(Date, nullable=False)
    
    # Flexible value storage - at least one must be filled
    value_numeric = Column(Numeric(15, 4))  # For numeric results
    value_text = Column(Text)  # For qualitative (+, ++, Positive, etc) or free text
    value_jsonb = Column(JSONB)  # For complex multi-part results
    
    # Metadata about this result
    unit = Column(String(50))
    reference_range = Column(JSONB)  # Store reference range at time of test
    is_abnormal = Column(Boolean)
    abnormal_flag = Column(String(10))  # H (high), L (low), HH (critically high), etc.
    
    # Quality indicators
    result_status = Column(String(20), default='final')  # preliminary, final, corrected, amended
    specimen_type = Column(String(50))  # serum, plasma, whole blood, saliva, urine, etc.
    notes = Column(Text)
    
    # Audit fields
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", backref="lab_results")
    test_definition = relationship("LabTestDefinition", back_populates="results")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_patient_test_date', 'patient_id', 'test_id', 'test_date'),
        Index('idx_test_date', 'test_date'),
    )
    
    def __repr__(self):
        return f"<LabResult patient_id={self.patient_id} test_id={self.test_id} date={self.test_date}>"


class LabResultBatch(Base):
    """Batch storage for related lab results (e.g., CBC panel, Autoantibody panel)"""
    __tablename__ = "lab_results_batch"
    
    batch_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    batch_name = Column(String(200))  # "CBC Panel", "Autoantibody Panel", "Cytokine Panel"
    test_date = Column(Date, nullable=False)
    
    # All test results in this batch stored as JSONB
    results = Column(JSONB, nullable=False)
    # Example:
    # {
    #   "WBC": {"value": 6.5, "unit": "10^9/L", "normal": true},
    #   "NEU%": {"value": 79.1, "unit": "%", "normal": true},
    #   "HGB": {"value": 149, "unit": "g/L", "normal": true}
    # }
    
    # Metadata
    panel_type = Column(String(100), index=True)  # CBC, Autoantibody, Cytokine, Immunology, etc.
    test_count = Column(Integer)  # Number of tests in this batch
    
    # Audit fields
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", backref="lab_batches")
    
    # Indexes
    __table_args__ = (
        Index('idx_patient_batch_date', 'patient_id', 'test_date'),
        Index('idx_panel_type', 'panel_type'),
        Index('idx_results_gin', 'results', postgresql_using='gin'),  # Fast JSON queries
    )
    
    def __repr__(self):
        return f"<LabBatch patient_id={self.patient_id} panel={self.panel_type} date={self.test_date}>"
