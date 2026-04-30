"""
List available datasets for training
Shows dataset IDs that can be used for model training

Usage:
    python3 list_datasets.py
"""
import requests
import json


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


def list_datasets(token: str):
    """List available datasets"""
    
    # Try to get dataset list from API
    endpoint = f"{API_BASE_URL}/api/v1/ml/datasets"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(endpoint, headers=headers)
    
    if response.status_code == 200:
        datasets = response.json()
        
        if datasets:
            print(f"\n{'='*60}")
            print(f"📊 Available Datasets")
            print(f"{'='*60}\n")
            
            for ds in datasets:
                print(f"Dataset ID: {ds['id']}")
                print(f"  Created: {ds.get('created_at', 'N/A')}")
                print(f"  Samples: {ds.get('n_samples', 'N/A')}")
                print(f"  Features: {ds.get('n_features', 'N/A')}")
                print()
        else:
            print("\n❌ No datasets found")
            print("\nGenerate a dataset first:")
            print("  POST /api/v1/ml/generate-dataset")
    else:
        print(f"\n⚠️ Could not retrieve datasets (Status {response.status_code})")
        print("\nTry checking training jobs to find dataset IDs:")
        print("  python3 check_job_status.py")


def main():
    try:
        print("🔐 Authenticating...")
        token = get_auth_token(USERNAME, PASSWORD)
        print("✅ Authenticated!\n")
        
        list_datasets(token)
    
    except Exception as e:
        print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
