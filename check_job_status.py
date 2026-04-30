"""
Quick script to check training job status without loading huge arrays
"""
import requests
import json

# Configuration
BASE_URL = "http://100.106.132.15:8001"
JOB_ID = "6ffc4c68-ecbf-4d3f-82bf-ea1b24fb15e6"

# Login to get token
login_response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data={
        "username": "s.nasrin",
        "password": "USM@22"
    }
)
token = login_response.json()["access_token"]

# Get job status
headers = {"Authorization": f"Bearer {token}"}
status_response = requests.get(
    f"{BASE_URL}/api/v1/ml/train/status/{JOB_ID}",
    headers=headers
)

if status_response.status_code == 200:
    job_data = status_response.json()
    
    print("=" * 60)
    print("JOB STATUS")
    print("=" * 60)
    print(f"Job ID: {job_data['job_id']}")
    print(f"Status: {job_data['status']}")
    print(f"Type: {job_data['job_type']}")
    print(f"Created: {job_data['created_at']}")
    print(f"Completed: {job_data.get('completed_at', 'N/A')}")
    print()
    
    # Check if this is a training job (has training metrics)
    if job_data.get('result'):
        result = job_data['result']
        
        # Base model training results
        if 'cv_auc' in result or 'test_auc' in result:
            print("=" * 60)
            print("TRAINING RESULTS")
            print("=" * 60)
            print(f"Model: {result.get('model_name', 'Unknown')}")
            print(f"Training Time: {result.get('training_time_seconds', 0):.1f} seconds")
            print()
            print("Cross-Validation Metrics:")
            print(f"  CV AUC: {result.get('cv_auc', 0):.4f}")
            print(f"  OOF AUC: {result.get('oof_auc', 0):.4f}")
            print()
            if result.get('test_auc') is not None:
                print("Test Set Metrics:")
                print(f"  Test AUC: {result.get('test_auc', 0):.4f}")
                print(f"  Test Precision: {result.get('test_precision', 0):.4f}")
                print(f"  Test Recall: {result.get('test_recall', 0):.4f}")
                print(f"  Test F1: {result.get('test_f1', 0):.4f}")
                print(f"  Test Brier Score: {result.get('test_brier_score', 0):.4f}")
                print()
            print("Best Hyperparameters:")
            print(json.dumps(result.get('best_params', {}), indent=2))
            print()
            if result.get('model_artifact_paths'):
                print(f"✅ Models saved to MinIO: {len(result['model_artifact_paths'])} fold models")
                print()
        
        # Ensemble training results
        elif 'ensemble_oof_auc' in result or 'ensemble_test_auc' in result:
            print("=" * 60)
            print("ENSEMBLE RESULTS")
            print("=" * 60)
            print(f"Base Models: {', '.join(result.get('base_models_included', []))}")
            print(f"Meta-learner: {result.get('meta_learner', 'LogisticRegression')}")
            print(f"Calibration: {result.get('calibration_method', 'None')}")
            print()
            print("Out-of-Fold Metrics:")
            print(f"  OOF AUC: {result.get('ensemble_oof_auc', 0):.4f}")
            print()
            if result.get('ensemble_test_auc') is not None:
                print("Test Set Metrics:")
                print(f"  Test AUC: {result.get('ensemble_test_auc', 0):.4f}")
                print(f"  Test Precision: {result.get('ensemble_test_precision', 0):.4f}")
                print(f"  Test Recall: {result.get('ensemble_test_recall', 0):.4f}")
                print(f"  Test F1: {result.get('ensemble_test_f1', 0):.4f}")
                print(f"  Test Brier Score: {result.get('ensemble_test_brier_score', 0):.4f}")
                print()
            print("Meta-learner Weights:")
            print(json.dumps(result.get('meta_weights', {}), indent=2))
            print()
            if result.get('model_artifact_path'):
                print(f"✅ Ensemble saved to MinIO: {result['model_artifact_path']}")
                print()
        
        # Dataset generation results
        elif 'metadata' in result:
            metadata = result['metadata']
            print("=" * 60)
            print("METADATA")
            print("=" * 60)
            print(json.dumps(metadata, indent=2))
            print()
            
            # Summary stats
            if 'X_train' in job_data['result']:
                print("=" * 60)
                print("DATASET SUMMARY")
                print("=" * 60)
                X_train = job_data['result']['X_train']
                X_test = job_data['result']['X_test']
                y_train = job_data['result']['y_train']
                y_test = job_data['result']['y_test']
                
                print(f"Training samples: {len(y_train)}")
                print(f"Test samples: {len(y_test)}")
                print(f"Features: {len(X_train[0]) if X_train else 0}")
                print(f"Feature names available: {len(job_data['result'].get('feature_names', []))}")
                print()
                
                # Label distribution
                from collections import Counter
                print("Training label distribution:")
                print(Counter(y_train))
                print("\nTest label distribution:")
                print(Counter(y_test))
    
    elif job_data.get('error_message'):
        print("=" * 60)
        print("ERROR")
        print("=" * 60)
        print(job_data['error_message'])
        
else:
    print(f"Error {status_response.status_code}: {status_response.text}")
