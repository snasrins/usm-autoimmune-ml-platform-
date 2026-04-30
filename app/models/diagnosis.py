"""
Diagnosis Model - Flexible disease diagnosis tracking
"""
from sqlalchemy import Column, Integer, String, Date, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Diagnosis(Base):
    """Diagnosis database model - tracks all patient diagnoses"""
    __tablename__ = "diagnoses"
    
    diagnosis_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    
    # Disease information
    disease_code = Column(String(20))  # ICD-10 code
    disease_name = Column(String(200), nullable=False)  # SLE, Sjogren, RA, etc.
    diagnosis_date = Column(Date)
    is_primary = Column(Boolean, default=False)
    severity = Column(String(20))  # Mild, Moderate, Severe
    
    # Clinical notes
    notes = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    patient = relationship("Patient", backref="diagnoses")
    
    # Indexes
    __table_args__ = (
        Index('idx_diagnosis_patient_disease', 'patient_id', 'disease_name'),
    )
    
    def __repr__(self):
        return f"<Diagnosis patient_id={self.patient_id} disease={self.disease_name}>"
