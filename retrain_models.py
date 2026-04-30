"""
Re-train models with MinIO persistence
Trains XGBoost, LightGBM, and RandomForest with proper MinIO storage

Usage:
    python3 retrain_models.py --dataset dataset_new_123
    python3 retrain_models.py --dataset dataset_new_123 --models xgboost lightgbm
"""
import requests
import json
import argparse
import time
from typing import List


API_BASE_URL = "http://100.106.132.15:8001"
USERNAME = "s.nasrin"
PASSWORD = "USM@22"


def get_auth_token(username: str, password: str) -> str:
    """Get JWT authentication token"""
    auth_url = f"{API_BASE_URL}/api/v1/auth/login"
    
    response = requests.post(
        auth_url,
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Authentication failed: {response.text}")


def train_base_model(
    token: str,
    dataset_id: str,
    model_name: str,
    n_folds: int = 5,
    optuna_trials: int = 10
) -> dict:
    """Train a single base model"""
    
    endpoint = f"{API_BASE_URL}/api/v1/ml/train/base-model"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    request_data = {
        "dataset_id": dataset_id,
        "model_name": model_name,
        "n_folds": n_folds,
        "optuna_trials": optuna_trials
    }
    
    print(f"\n{'='*60}")
    print(f"🏋️ Training {model_name.upper()}")
    print(f"{'='*60}\n")
    print(f"  Dataset: {dataset_id}")
    print(f"  Folds: {n_folds}")
    print(f"  Optuna Trials: {optuna_trials}\n")
    
    response = requests.post(endpoint, json=request_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        job_id = result['job_id']
        
        print(f"✅ Training started!")
        print(f"   Job ID: {job_id}")
        print(f"   Status: {result['status']}\n")
        
        return result
    else:
        print(f"❌ Training failed!")
        print(f"   Status Code: {response.status_code}")
        print(f"   Error: {response.text}\n")
        return None


def check_job_status(token: str, job_id: str) -> dict:
    """Check training job status"""
    
    endpoint = f"{API_BASE_URL}/api/v1/ml/jobs/{job_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(endpoint, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None


def wait_for_completion(token: str, job_id: str, model_name: str, timeout: int = 600):
    """Wait for training to complete"""
    
    print(f"⏳ Waiting for {model_name} training to complete...")
    
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < timeout:
        status = check_job_status(token, job_id)
        
        if status:
            current_status = status.get('status')
            
            if current_status != last_status:
                print(f"   Status: {current_status}")
                last_status = current_status
            
            if current_status == 'completed':
                result = status.get('result', {})
                
                print(f"\n✅ {model_name.upper()} Training Complete!\n")
                print(f"   CV AUC: {result.get('cv_auc', 0):.4f}")
                print(f"   Test AUC: {result.get('test_auc', 0):.4f}")
                print(f"   Test Precision: {result.get('test_precision', 0):.4f}")
                print(f"   Test Recall: {result.get('test_recall', 0):.4f}")
                print(f"   Test F1: {result.get('test_f1', 0):.4f}")
                
                if result.get('minio_path'):
                    print(f"   MinIO Path: {result['minio_path']}")
                
                return True
            
            elif current_status == 'failed':
                print(f"\n❌ {model_name.upper()} Training Failed!")
                print(f"   Error: {status.get('error')}")
                return False
        
        time.sleep(5)
    
    print(f"\n⏰ Timeout reached for {model_name}")
    return False


def main():
    parser = argparse.ArgumentParser(description="Re-train ML models with MinIO persistence")
    parser.add_argument("--dataset", required=True, help="Dataset ID")
    parser.add_argument("--models", nargs="+", default=["xgboost", "lightgbm", "random_forest"],
                       help="Models to train (default: all three)")
    parser.add_argument("--folds", type=int, default=5, help="Number of CV folds")
    parser.add_argument("--trials", type=int, default=10, help="Optuna trials (use 100 for production)")
    parser.add_argument("--username", default=USERNAME, help="API username")
    parser.add_argument("--password", default=PASSWORD, help="API password")
    parser.add_argument("--no-wait", action="store_true", help="Don't wait for completion")
    
    args = parser.parse_args()
    
    try:
        # Authenticate
        print("🔐 Authenticating...")
        token = get_auth_token(args.username, args.password)
        print(f"✅ Authentication successful!\n")
        
        job_ids = {}
        
        # Train models
        for model_name in args.models:
            result = train_base_model(
                token=token,
                dataset_id=args.dataset,
                model_name=model_name,
                n_folds=args.folds,
                optuna_trials=args.trials
            )
            
            if result:
                job_ids[model_name] = result['job_id']
        
        if not args.no_wait:
            print(f"\n{'='*60}")
            print(f"⏳ Monitoring Training Progress")
            print(f"{'='*60}\n")
            
            # Wait for all jobs to complete
            for model_name, job_id in job_ids.items():
                success = wait_for_completion(token, job_id, model_name)
                
                if not success:
                    print(f"⚠️ {model_name} did not complete successfully")
        else:
            print(f"\n✅ All training jobs submitted!")
            print(f"\nJob IDs:")
            for model_name, job_id in job_ids.items():
                print(f"  {model_name}: {job_id}")
            print(f"\nUse check_job_status.py to monitor progress")
        
        print(f"\n{'='*60}")
        print(f"✅ Training Complete!")
        print(f"{'='*60}\n")
        
        print(f"Next steps:")
        print(f"  1. Verify models in MinIO:")
        print(f"     docker compose exec fastapi python3 -c \"from app.services.minio_service import get_minio_service; minio = get_minio_service(); [print(obj.object_name) for obj in minio.client.list_objects('ml-models', recursive=True)]\"")
        print(f"\n  2. Test SHAP explainability:")
        print(f"     python3 test_explainability.py --test shap --model xgboost")
        print(f"\n  3. Test Gemma conversational AI:")
        print(f"     python3 test_explainability.py --test chat")
        print()
    
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        raise


if __name__ == "__main__":
    main()
