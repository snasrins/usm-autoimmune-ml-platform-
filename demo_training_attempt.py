"""
ML Training Attempt Script
Simulates clicking the "Run Training" button and shows the validation failure
This demonstrates the complete flow: Start Training → Validation → Block/Approve
"""
import sys
import uuid
from datetime import datetime
from app.services.ml_data_validator import MLDataValidator
from app.core.database import SessionLocal
from app.models.flexible_data import FlexibleDatasetWide
from sqlalchemy import func

def print_separator():
    print("\n" + "─" * 80 + "\n")

def print_box(title):
    print("\n╔" + "═" * 78 + "╗")
    print(f"║ {title.center(76)} ║")
    print("╚" + "═" * 78 + "╝")

def main():
    print_box("ML TRAINING PIPELINE - AUTOIMMUNE DISEASE CLASSIFIER")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Initialize
    print("\n[1/5] 🔧 INITIALIZING TRAINING PIPELINE")
    print("      ├─ Loading ML training service...")
    print("      ├─ Connecting to database...")
    db = SessionLocal()
    print("      └─ ✓ Initialization complete")
    
    # Step 2: Load Dataset
    print("\n[2/5] 📊 LOADING TRAINING DATASET")
    print("      ├─ Querying for latest dataset...")
    
    batch_query = db.query(
        FlexibleDatasetWide.import_batch_id,
        func.count(FlexibleDatasetWide.id).label('record_count')
    ).group_by(
        FlexibleDatasetWide.import_batch_id
    ).order_by(
        func.max(FlexibleDatasetWide.created_at).desc()
    ).first()
    
    if not batch_query:
        print("      └─ ❌ ERROR: No datasets found")
        return
    
    batch_id = batch_query[0]
    record_count = batch_query[1]
    
    print(f"      ├─ Dataset found: {batch_id}")
    print(f"      ├─ Total records: {record_count}")
    print("      └─ ✓ Dataset loaded successfully")
    
    # Step 3: Pre-Training Validation
    print("\n[3/5] 🔍 PRE-TRAINING DATA VALIDATION")
    print("      ├─ Validating data quality...")
    print("      ├─ Checking minimum sample requirements...")
    print("      └─ Running ML-specific checks...")
    
    validator = MLDataValidator(db)
    
    try:
        result = validator.validate_for_ml_training(
            batch_id=batch_id,
            target_column='labels_disease_classification',
            min_samples_per_class=30
        )
        
        print_separator()
        print_box("VALIDATION RESULTS")
        
        # Display each check
        for check in result['checks']:
            status_icon = {
                'pass': '✅ PASS',
                'fail': '❌ FAIL',
                'warn': '⚠️  WARN'
            }.get(check['status'], '❓ UNKNOWN')
            
            print(f"\n▸ {check['check_name']}")
            print(f"  Status: {status_icon}")
            
            if check.get('details'):
                print(f"  Details: {check['details']}")
            
            if check.get('recommendation'):
                print(f"  💡 Action: {check['recommendation']}")
        
        print_separator()
        
        # Step 4: Training Decision
        print("\n[4/5] 🎯 TRAINING DECISION ENGINE")
        print(f"      ├─ Overall validation status: {result['overall_status'].upper()}")
        print(f"      ├─ Ready for training: {result['ready_for_training']}")
        
        if result['ready_for_training']:
            print("      └─ ✓ All checks passed - proceeding to training")
            
            print("\n[5/5] 🚀 STARTING MODEL TRAINING")
            print("      ├─ Preparing training dataset...")
            print("      ├─ Initializing XGBoost model...")
            print("      ├─ Starting hyperparameter optimization...")
            print("      └─ Training in progress...")
            
            print_box("✓ TRAINING STARTED SUCCESSFULLY")
            
        else:
            print("      └─ ⛔ Training blocked - requirements not met")
            
            print("\n[5/5] 🚫 TRAINING REJECTED")
            
            failed_checks = [c for c in result['checks'] if c['status'] == 'fail']
            warn_checks = [c for c in result['checks'] if c['status'] == 'warn']
            
            print("\n      ┌─ BLOCKING ISSUES:")
            for check in failed_checks:
                print(f"      │  ❌ {check['check_name']}")
                print(f"      │     └─ {check.get('details', 'Validation failed')}")
            
            if warn_checks:
                print("\n      ├─ WARNINGS:")
                for check in warn_checks:
                    print(f"      │  ⚠️  {check['check_name']}")
                    print(f"      │     └─ {check.get('details', 'Needs attention')}")
            
            print("\n      └─ REQUIRED ACTIONS:")
            for i, check in enumerate(failed_checks, 1):
                if 'recommendation' in check:
                    print(f"         {i}. {check['recommendation']}")
            
            print_box("⛔ TRAINING BLOCKED - DATA VALIDATION FAILED")
            
            print("\n📋 SUMMARY:")
            print(f"   • Total records: {record_count}")
            print(f"   • Validation checks run: {len(result['checks'])}")
            print(f"   • Checks passed: {len([c for c in result['checks'] if c['status'] == 'pass'])}")
            print(f"   • Checks failed: {len(failed_checks)}")
            print(f"   • Training status: BLOCKED")
            
            print("\n💡 WHY THIS MATTERS:")
            print("   Training a model on insufficient or poor-quality data would result in:")
            print("   • Overfitting and poor generalization")
            print("   • Unreliable predictions on new patients")
            print("   • Potential medical misdiagnosis")
            print("   • Wasted computational resources")
            
            print("\n✓ This validation system ensures safe, reliable ML model development")
    
    except Exception as e:
        print_separator()
        print_box("❌ VALIDATION ERROR")
        print(f"\nError Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        
        import traceback
        print("\nStack Trace:")
        print("─" * 80)
        traceback.print_exc()
    
    finally:
        db.close()
        print_separator()
        print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print_separator()

if __name__ == "__main__":
    main()
