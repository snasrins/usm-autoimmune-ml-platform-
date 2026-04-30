"""
ML Validation Test Script
Demonstrates ML pipeline validation with detailed terminal output
Run this to show proof that ML training validates data before proceeding
"""
import sys
import uuid
from datetime import datetime
from app.services.ml_data_validator import MLDataValidator
from app.core.database import SessionLocal

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_check(name, status, details=None, recommendation=None):
    """Print a formatted validation check result"""
    icons = {
        'pass': '✅',
        'fail': '❌',
        'warn': '⚠️'
    }
    icon = icons.get(status, '❓')
    
    print(f"\n{icon} {name}: {status.upper()}")
    if details:
        print(f"   Details: {details}")
    if recommendation:
        print(f"   💡 Recommendation: {recommendation}")

def main():
    print_header("ML TRAINING VALIDATION SYSTEM")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Status: RUNNING\n")
    
    # Initialize database connection
    print("🔌 Connecting to database...")
    db = SessionLocal()
    print("✓ Database connection established")
    
    # Initialize ML validator
    print("🤖 Initializing ML Data Validator...")
    validator = MLDataValidator(db)
    print("✓ Validator initialized")
    
    # Get the most recent batch from database
    print("\n📊 Fetching most recent dataset...")
    from app.models.flexible_data import FlexibleDatasetWide
    from sqlalchemy import func
    
    batch_query = db.query(
        FlexibleDatasetWide.import_batch_id,
        func.count(FlexibleDatasetWide.id).label('record_count')
    ).group_by(
        FlexibleDatasetWide.import_batch_id
    ).order_by(
        func.max(FlexibleDatasetWide.created_at).desc()
    ).first()
    
    if not batch_query:
        print("❌ ERROR: No datasets found in database")
        return
    
    batch_id = batch_query[0]
    record_count = batch_query[1]
    
    print(f"✓ Found dataset:")
    print(f"   Batch ID: {batch_id}")
    print(f"   Total Records: {record_count}")
    
    print_header("RUNNING PRE-TRAINING VALIDATION")
    print("Checking if dataset meets minimum ML training requirements...")
    
    # Run validation
    print("\n🔍 Performing validation checks...\n")
    
    try:
        result = validator.validate_for_ml_training(
            batch_id=batch_id,
            target_column='labels_disease_classification',
            min_samples_per_class=30
        )
        
        print_header("VALIDATION RESULTS")
        print(f"Overall Status: {result['overall_status'].upper()}")
        print(f"Ready for Training: {result['ready_for_training']}")
        
        if result['checks']:
            print("\n📋 Detailed Check Results:")
            for check in result['checks']:
                print_check(
                    check['check_name'],
                    check['status'],
                    check.get('details'),
                    check.get('recommendation')
                )
        
        # Final verdict
        print_header("TRAINING DECISION")
        
        if result['ready_for_training']:
            print("✅ TRAINING APPROVED")
            print("Dataset meets all minimum requirements")
            print("Model training can proceed safely")
        else:
            print("⛔ TRAINING BLOCKED")
            print("Dataset does not meet minimum requirements")
            print("\n🚫 Reasons:")
            
            failed_checks = [c for c in result['checks'] if c['status'] == 'fail']
            for i, check in enumerate(failed_checks, 1):
                print(f"   {i}. {check['check_name']}: {check.get('details', 'Failed validation')}")
            
            print("\n💡 Next Steps:")
            for check in failed_checks:
                if 'recommendation' in check:
                    print(f"   • {check['recommendation']}")
            
            print("\n⚠️  ML training will NOT proceed until these issues are resolved")
            print("   This safeguard prevents poor model performance due to insufficient data")
        
        print_header("VALIDATION COMPLETE")
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print_header("VALIDATION ERROR")
        print(f"❌ Error during validation: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        print(f"\n📜 Stack trace:")
        traceback.print_exc()
    
    finally:
        db.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    main()
