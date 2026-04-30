"""
Disease Category Models - Dynamic Category Management
NO hardcoding - all categories managed via admin API
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class DiseaseCategory(Base):
    """
    Lookup table for disease categories
    Managed via admin API - NO hardcoded categories
    """
    __tablename__ = "dim_disease_categories"
    
    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(100), nullable=False, unique=True)
    category_code = Column(String(50), unique=True)
    category_label = Column(String(200))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    mappings = relationship("DiagnosisCategoryMapping", back_populates="category", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_disease_cat_active', 'is_active'),
        Index('idx_disease_cat_code', 'category_code'),
    )
    
    def __repr__(self):
        return f"<DiseaseCategory {self.category_name} ({self.category_code})>"


class DiagnosisCategoryMapping(Base):
    """
    Maps diagnosis strings to categories dynamically
    Supports pattern matching (exact, contains, regex)
    """
    __tablename__ = "diagnosis_category_mappings"
    
    mapping_id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("dim_disease_categories.category_id", ondelete="CASCADE"), nullable=False)
    
    # Pattern matching
    diagnosis_pattern = Column(String(200), nullable=False)
    match_type = Column(String(20), default='exact')  # 'exact', 'contains', 'starts_with', 'regex'
    
    # Priority for overlapping patterns
    priority = Column(Integer, default=0)
    
    # Optional conditional logic
    condition_field = Column(String(100))
    condition_value = Column(String(100))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    category = relationship("DiseaseCategory", back_populates="mappings")
    
    # Indexes
    __table_args__ = (
        Index('idx_mapping_category', 'category_id'),
        Index('idx_mapping_active', 'is_active'),
        Index('idx_mapping_priority', 'priority'),
    )
    
    def __repr__(self):
        return f"<DiagnosisCategoryMapping pattern='{self.diagnosis_pattern}' type={self.match_type}>"


class CategoryAuditLog(Base):
    """
    Audit trail for category management changes
    Tracks all INSERT/UPDATE/DELETE operations
    """
    __tablename__ = "category_audit_log"
    
    audit_id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)
    old_data = Column(Text)  # JSON string
    new_data = Column(Text)  # JSON string
    changed_by = Column(Integer, ForeignKey("users.id"))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_table', 'table_name', 'record_id'),
        Index('idx_audit_time', 'changed_at'),
    )
    
    def __repr__(self):
        return f"<CategoryAuditLog {self.table_name}#{self.record_id} {self.action}>"
