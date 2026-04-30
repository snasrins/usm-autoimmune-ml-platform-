"""
Test Prediction API (USMA-46)
Tests ML inference endpoint with trained models from MinIO

Usage:
    python test_prediction_api.py --model xgboost --version v1
    python test_prediction_api.py --model ensemble --version v1
"""
import requests
import json
import argparse
from typing import Dict


# API Configuration
API_BASE_URL = "http://100.106.132.15:8001"
API_ENDPOINT = f"{API_BASE_URL}/api/v1/ml/predict"
USERNAME = "s.nasrin"
PASSWORD = "USM@22"


def get_auth_token(username: str, password: str) -> str:
    """Get JWT authentication token"""
    auth_url = f"{API_BASE_URL}/api/v1/auth/login"
    
    # Use form data for OAuth2 login
    response = requests.post(
        auth_url,
        data={
            "username": username,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        token_data = response.json()
        return token_data["access_token"]
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        raise Exception("Authentication failed")


def create_sample_patient_data() -> Dict:
    """
    Create sample patient data for prediction
    
    Note: Only LASSO-selected features are required:
    - demographics_age
    - lab_results_CRP_ESR_ratio (derived feature)
    - lab_results_complement_ratio (derived feature)
    
    But we provide more features so the feature engineering pipeline
    can calculate the derived features.
    """
    return {
        # Demographics
        "demographics_age": 35.0,
        "demographics_gender": "Female",
        
        # Lab Results (needed to calculate ratios)
        "lab_results_ANA": 1.5,
        "lab_results_Anti_dsDNA": 0.8,
        "lab_results_ESR": 45.0,
        "lab_results_CRP": 12.5,
        "lab_results_C3": 85.0,
        "lab_results_C4": 15.0,
        
        # Clinical Manifestations
        "clinical_manifestations_Malar_Rash": 1,
        "clinical_manifestations_Discoid_Rash": 0,
        "clinical_manifestations_Photosensitivity": 1,
        "clinical_manifestations_Oral_Ulcers": 0,
        "clinical_manifestations_Arthritis": 1,
        "clinical_manifestations_Serositis": 0,
        "clinical_manifestations_Renal": 0,
        "clinical_manifestations_Neurologic": 0,
        "clinical_manifestations_Hematologic": 1,
        
        # Immunologic
        "immunologic_Anti_Sm": 0,
        "immunologic_Anti_RNP": 1,
        "immunologic_Anti_Ro_SSA": 1,
        "immunologic_Anti_La_SSB": 0,
        "immunologic_Antiphospholipid": 0,
        
        # Medications (Treatment Info)
        "medications_Hydroxychloroquine": 1,
        "medications_Corticosteroids": 1,
        "medications_Immunosuppressants": 0,
        "medications_Biologics": 0,
        
        # Disease Activity
        "disease_activity_SLEDAI_score": 8.0,
        "disease_activity_flare_history": 2.0,
    }


def test_single_prediction(
    model_name: str = "xgboost",
    version: str = "v1",
    token: str = None
):
    """Test single patient prediction"""
    
    print(f"\n{'='*60}")
    print(f"🧪 Testing Prediction API - Model: {model_name}/{version}")
    print(f"{'='*60}\n")
    
    # Create sample patient data
    patient_data = create_sample_patient_data()
    
    # Prepare request
    request_data = {
        "model_name": model_name,
        "version": version,
        "patient_data": patient_data,
        "return_probability": True
    }
    
    # Make API request
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("📤 Sending prediction request...")
    print(f"   Model: {model_name}/{version}")
    print(f"   Patient Age: {patient_data['demographics_age']}")
    print(f"   SLEDAI Score: {patient_data['disease_activity_SLEDAI_score']}")
    
    response = requests.post(
        API_ENDPOINT,
        json=request_data,
        headers=headers
    )
    
    # Parse response
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n✅ Prediction Successful!\n")
        print(f"{'─'*60}")
        print(f"Predicted Severity: {result['prediction']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Predicted Class Index: {result['predicted_class_index']}")
        print(f"\nClass Probabilities:")
        for class_name, prob in result['probabilities'].items():
            bar = '█' * int(prob * 50)
            print(f"  {class_name:12} {prob:.2%} {bar}")
        
        print(f"\nModel Info:")
        print(f"  Model Name: {result['model_name']}")
        print(f"  Version: {result['version']}")
        print(f"  Severity Category: {result['severity_category']}")
        
        print(f"\nClass Mapping:")
        for class_name, idx in result['class_mapping'].items():
            print(f"  {class_name}: {idx}")
        
        print(f"{'─'*60}\n")
        
        return result
    
    else:
        print(f"\n❌ Prediction Failed!")
        print(f"Status Code: {response.status_code}")
        print(f"Error: {response.text}\n")
        return None


def test_ensemble_prediction(token: str, version: str = "v1"):
    """Test ensemble prediction (convenience endpoint)"""
    
    print(f"\n{'='*60}")
    print(f"🎯 Testing Ensemble Prediction (Most Accurate)")
    print(f"{'='*60}\n")
    
    patient_data = create_sample_patient_data()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Use the ensemble convenience endpoint
    ensemble_url = f"{API_BASE_URL}/api/v1/ml/predict/ensemble"
    
    response = requests.post(
        ensemble_url,
        json=patient_data,
        params={"version": version},
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"✅ Ensemble Prediction Successful!\n")
        print(f"Predicted Severity: {result['prediction']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"\nProbabilities:")
        for class_name, prob in result['probabilities'].items():
            print(f"  {class_name}: {prob:.2%}")
        
        return result
    
    else:
        print(f"❌ Ensemble Prediction Failed!")
        print(f"Error: {response.text}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Test ML Prediction API")
    parser.add_argument("--model", default="xgboost", help="Model name (xgboost, lightgbm, random_forest, ensemble)")
    parser.add_argument("--version", default="v1", help="Model version")
    parser.add_argument("--test-ensemble", action="store_true", help="Test ensemble endpoint")
    parser.add_argument("--username", default=USERNAME, help="API username")
    parser.add_argument("--password", default=PASSWORD, help="API password")
    
    args = parser.parse_args()
    
    try:
        # Authenticate
        print("🔐 Authenticating...")
        token = get_auth_token(args.username, args.password)
        print(f"✅ Authentication successful!\n")
        
        # Test predictions
        if args.test_ensemble:
            test_ensemble_prediction(token, args.version)
        else:
            test_single_prediction(args.model, args.version, token)
        
        print("\n✅ All tests completed!\n")
    
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        raise


if __name__ == "__main__":
    main()
