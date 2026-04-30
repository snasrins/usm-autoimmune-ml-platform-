"""
Complete Training Pipeline - Generate Dataset + Train Models + Test Explainability
One-command solution to get the full ML pipeline running

Usage:
    python3 complete_training_pipeline.py
    python3 complete_training_pipeline.py --quick  # Fast testing (10 trials)
"""
import requests
import json
import argparse
import time


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


def generate_dataset(token: str, batch_id: str = "9161cd88-e7bb-4ec7-9577-a129cde949ae"):
    """Generate ML training dataset"""
    
    print(f"\n{'='*60}")
    print(f"📊 Step 1: Generating Dataset")
    print(f"{'='*60}\n")
    
    endpoint = f"{API_BASE_URL}/api/v1/ml/train/prepare-dataset"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    request_data = {
        "batch_id": batch_id,
        "target_column": "labels_disease_severity",
        "test_size": 0.35,
        "use_lasso_feature_selection": True,
        "lasso_alpha": 0.01,
        "create_separate_feature_sets": False,
        "scaling_strategy": "standard",
        "skip_preprocessing": False
    }
    
    print(f"  Batch ID: {batch_id}")
    print(f"  Target: labels_disease_severity")
    print(f"  Test split: 65/35")
    print(f"  LASSO: Enabled (alpha=0.01)\n")
    
    response = requests.post(endpoint, json=request_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        job_id = result['job_id']
        
        print(f"✅ Dataset generation started!")
        print(f"   Job ID: {job_id}\n")
        
        # Wait for completion
        print(f"⏳ Waiting for dataset generation...")
        
        for i in range(60):  # 5 minutes timeout
            time.sleep(5)
            
            status_endpoint = f"{API_BASE_URL}/api/v1/ml/jobs/{job_id}"
            status_response = requests.get(status_endpoint, headers={"Authorization": f"Bearer {token}"})
            
            if status_response.status_code == 200:
                status = status_response.json()
                
                if status['status'] == 'completed':
                    result = status['result']
                    dataset_id = result['dataset_id']
                    
                    print(f"\n✅ Dataset Generated Successfully!\n")
                    print(f"   Dataset ID: {dataset_id}")
                    print(f"   Train samples: {result['metadata']['train_samples']}")
                    print(f"   Test samples: {result['metadata']['test_samples']}")
                    print(f"   Features: {result['metadata']['n_features']}\n")
                    
                    return dataset_id
                
                elif status['status'] == 'failed':
                    raise Exception(f"Dataset generation failed: {status.get('error')}")
        
        raise Exception("Dataset generation timeout")
    
    else:
        raise Exception(f"Dataset generation failed: {response.text}")


def train_model(token: str, dataset_id: str, model_name: str, optuna_trials: int = 100):
    """Train a single model"""
    
    print(f"\n🏋️ Training {model_name.upper()}...")
    
    endpoint = f"{API_BASE_URL}/api/v1/ml/train/base-model"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    request_data = {
        "dataset_id": dataset_id,
        "model_name": model_name,
        "n_folds": 5,
        "optuna_trials": optuna_trials
    }
    
    response = requests.post(endpoint, json=request_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Job ID: {result['job_id']}")
        return result['job_id']
    else:
        raise Exception(f"{model_name} training failed: {response.text}")


def wait_for_training(token: str, job_id: str, model_name: str):
    """Wait for model training to complete"""
    
    for i in range(240):  # 20 minutes timeout
        time.sleep(5)
        
        endpoint = f"{API_BASE_URL}/api/v1/ml/jobs/{job_id}"
        response = requests.get(endpoint, headers={"Authorization": f"Bearer {token}"})
        
        if response.status_code == 200:
            status = response.json()
            
            if status['status'] == 'completed':
                result = status['result']
                print(f"\n✅ {model_name.upper()} Complete!")
                print(f"   CV AUC: {result.get('cv_auc', 0):.4f}")
                print(f"   Test AUC: {result.get('test_auc', 0):.4f}")
                print(f"   MinIO: {result.get('minio_path', 'N/A')}\n")
                return True
            
            elif status['status'] == 'failed':
                print(f"❌ {model_name.upper()} failed: {status.get('error')}")
                return False
    
    print(f"⏰ {model_name.upper()} timeout")
    return False


def main():
    parser = argparse.ArgumentParser(description="Complete ML Training Pipeline")
    parser.add_argument("--quick", action="store_true", help="Quick mode (10 trials instead of 100)")
    parser.add_argument("--batch-id", default="9161cd88-e7bb-4ec7-9577-a129cde949ae", help="Batch ID")
    args = parser.parse_args()
    
    trials = 10 if args.quick else 100
    
    try:
        print(f"\n{'='*60}")
        print(f"🚀 COMPLETE ML TRAINING PIPELINE")
        print(f"{'='*60}\n")
        print(f"Mode: {'QUICK TEST' if args.quick else 'PRODUCTION'}")
        print(f"Optuna Trials: {trials}")
        print()
        
        # Step 1: Authenticate
        print("🔐 Authenticating...")
        token = get_auth_token(USERNAME, PASSWORD)
        print("✅ Authenticated!\n")
        
        # Step 2: Generate Dataset
        dataset_id = generate_dataset(token, args.batch_id)
        
        # Step 3: Train Models
        print(f"{'='*60}")
        print(f"🏋️ Step 2: Training Models")
        print(f"{'='*60}\n")
        
        models = ["xgboost", "lightgbm", "random_forest"]
        job_ids = {}
        
        for model_name in models:
            job_id = train_model(token, dataset_id, model_name, trials)
            job_ids[model_name] = job_id
        
        # Step 4: Wait for completion
        print(f"\n{'='*60}")
        print(f"⏳ Step 3: Monitoring Training")
        print(f"{'='*60}\n")
        
        for model_name, job_id in job_ids.items():
            wait_for_training(token, job_id, model_name)
        
        # Step 5: Verify MinIO
        print(f"{'='*60}")
        print(f"✅ PIPELINE COMPLETE!")
        print(f"{'='*60}\n")
        
        print(f"Next steps:\n")
        print(f"1. Test SHAP Explainability:")
        print(f"   python3 test_explainability.py --test shap --model xgboost\n")
        print(f"2. Test Gemma Conversational AI:")
        print(f"   python3 test_explainability.py --test chat\n")
        print(f"3. Test Complete Suite:")
        print(f"   python3 test_explainability.py --test all\n")
    
    except Exception as e:
        print(f"\n❌ Pipeline Error: {e}\n")
        raise


if __name__ == "__main__":
    main()
