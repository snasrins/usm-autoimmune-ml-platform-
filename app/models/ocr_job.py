"""
OCR Job Model — async unstructured document processing tracker.
Uses plain String status (no PostgreSQL ENUM) so create_all auto-creates the
table without any Alembic migration.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, Float, ForeignKey, Integer, JSON, String, Text, DateTime

from app.core.database import Base


class OcrJob(Base):
    __tablename__ = "ocr_jobs"

    job_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)

    # pending → running → completed | failed
    status = Column(String(20), nullable=False, default="pending", index=True)

    filename = Column(String(500), nullable=True)
    file_type = Column(String(20), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Populated once processing completes
    validation_id = Column(Integer, nullable=True)
    result = Column(JSON, nullable=True)          # Full dict returned by upload_and_process()
    error = Column(Text, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)

    def __repr__(self):
        return f"<OcrJob {self.job_id} – {self.status}>"
