"""
Database Migration Script - Create Flexible Schema Tables
Run this to create all tables for the flexible autoimmune disease registry

Usage:
    python scripts/create_flexible_schema.py
"""
import sys
sys.path.append('.')

from app.core.database import engine, Base
from app.models import (
    User, Patient, Diagnosis,
    LabTestDefinition, LabResultFlexible, LabResultBatch,
    DiseaseSpecificData, UploadedFile, DataIngestionAudit
)


def create_tables():
    """Create all tables in the database"""
    print("Creating flexible schema tables...")
    print("=" * 80)
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Successfully created all tables:")
        print("   - users")
        print("   - patients")
        print("   - diagnoses")
        print("   - lab_test_definitions")
        print("   - lab_results_flexible")
        print("   - lab_results_batch")
        print("   - disease_specific_data")
        print("   - uploaded_files")
        print("   - data_ingestion_audit")
        print("=" * 80)
        print("✅ Database schema creation complete!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise


def drop_tables():
    """Drop all tables (use with caution!)"""
    confirm = input("⚠️  WARNING: This will drop ALL tables! Type 'yes' to confirm: ")
    if confirm.lower() == 'yes':
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped")
    else:
        print("❌ Aborted")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database migration script')
    parser.add_argument('action', choices=['create', 'drop'], help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        create_tables()
    elif args.action == 'drop':
        drop_tables()
