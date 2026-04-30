"""
Disease-Specific Data Model - Pure JSONB storage for maximum flexibility
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class DiseaseSpecificData(Base):
    """Flexible storage for disease-specific data that doesn't fit standard schema"""
    __tablename__ = "disease_specific_data"
    
    data_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    disease_name = Column(String(100), nullable=False, index=True)  # SLE, Sjogren, RA, etc.
    data_category = Column(String(100), index=True)  # clinical_scores, imaging, genetics, medications, etc.
    
    # Completely flexible storage
    data = Column(JSONB, nullable=False)
    # Examples:
    # For SLE:
    # {
    #   "SLEDAI": {"score": 8, "category": "moderate", "date": "2026-03-01"},
    #   "kidney_biopsy": {"class": "III", "activity": 5, "chronicity": 2, "date": "2025-12-15"}
    # }
    #
    # For Sjogren's:
    # {
    #   "ESSDAI": {"score": 12, "date": "2026-02-15"},
    #   "salivary_flow": {"unstimulated": 0.05, "stimulated": 0.3, "unit": "ml/min"}
    # }
    #
    # For Medications:
    # {
    #   "medications": [
    #     {"name": "Hydroxychloroquine", "dose": "200mg", "frequency": "BID", "start_date": "2025-01-15"},
    #     {"name": "Prednisone", "dose": "10mg", "frequency": "OD", "start_date": "2025-03-01"}
    #   ]
    # }
    
    collection_date = Column(Date)
    notes = Column(Text)
    
    # Audit fields
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", backref="disease_data")
    
    # Indexes
    __table_args__ = (
        Index('idx_disease_data_patient_disease', 'patient_id', 'disease_name'),
        Index('idx_data_category', 'data_category'),
        Index('idx_data_gin', 'data', postgresql_using='gin'),  # Fast JSON queries
    )
    
    def __repr__(self):
        return f"<DiseaseData patient_id={self.patient_id} disease={self.disease_name} category={self.data_category}>"
