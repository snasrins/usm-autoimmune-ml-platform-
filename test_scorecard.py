"""
Test Scorecard & Model Comparison (USMA-47 + USMA-43)
Tests clinical scorecard generation and model comparison dashboard

Usage:
    # Test scorecard
    python3 test_scorecard.py --test scorecard --model xgboost
    
    # Test model comparison
    python3 test_scorecard.py --test compare
    
    # Test all features
    python3 test_scorecard.py --test all
"""
import requests
import json
import argparse
from typing import Dict


# API Configuration
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


def create_sample_patient_data() -> Dict:
    """Create sample patient data for testing"""
    return {
        "demographics_age": 35.0,
        "demographics_gender": "Female",
        "lab_results_ANA": 1.5,
        "lab_results_Anti_dsDNA": 0.8,
        "lab_results_ESR": 45.0,
        "lab_results_CRP": 12.5,
        "lab_results_C3": 85.0,
        "lab_results_C4": 15.0,
        "clinical_manifestations_Malar_Rash": 1,
        "clinical_manifestations_Arthritis": 1,
        "clinical_manifestations_Hematologic": 1,
        "immunologic_Anti_RNP": 1,
        "immunologic_Anti_Ro_SSA": 1,
        "medications_Hydroxychloroquine": 1,
        "medications_Corticosteroids": 1,
        "disease_activity_SLEDAI_score": 8.0,
        "disease_activity_flare_history": 2.0,
    }


def test_scorecard(token: str, model_name: str = "xgboost", version: str = "v1"):
    """Test clinical scorecard generation"""
    
    print(f"\n{'='*70}")
    print(f"🏥 Testing Clinical Scorecard - {model_name}/{version}")
    print(f"{'='*70}\n")
    
    endpoint = f"{API_BASE_URL}/api/v1/ml/scorecard"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    patient_data = create_sample_patient_data()
    
    request_data = {
        "model_name": model_name,
        "version": version,
        "patient_data": patient_data,
        "include_feature_scores": True
    }
    
    print("📤 Generating scorecard...")
    response = requests.post(endpoint, json=request_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n✅ Scorecard Generated!\n")
        print(f"{'─'*70}")
        print(f"Model: {result['model_name']} ({result['version']})")
        print(f"\n📊 RISK ASSESSMENT")
        print(f"{'─'*70}")
        print(f"Risk Score:       {result['risk_score']:.1f}/100")
        print(f"Risk Group:       {result['risk_group']} (Level {result['risk_level']})")
        print(f"Predicted Class:  {result['predicted_class']}")
        print(f"Confidence:       {result['confidence']:.1%}")
        
        print(f"\n📋 CLINICAL INTERPRETATION")
        print(f"{'─'*70}")
        print(f"{result['risk_description']}")
        
        print(f"\n💊 RECOMMENDATION")
        print(f"{'─'*70}")
        print(f"{result['clinical_recommendation']}")
        
        print(f"\n📈 PROBABILITY DISTRIBUTION")
        print(f"{'─'*70}")
        for class_name, prob in result['probability_distribution'].items():
            bar = '█' * int(prob * 50)
            print(f"  {class_name:12} {prob:.1%} {bar}")
        
        if result.get('top_contributing_features'):
            print(f"\n🔬 TOP CONTRIBUTING FEATURES")
            print(f"{'─'*70}")
            for i, feat in enumerate(result['top_contributing_features'], 1):
                feature_name = feat['feature'].replace('_', ' ').title()
                score = feat['score']
                value = feat.get('value', 0.0)
                print(f"{i}. {feature_name:40} | Score: {score:5.1f} | Value: {value:7.2f}")
        
        print(f"{'─'*70}\n")
        
        return result
    
    else:
        print(f"\n❌ Scorecard Generation Failed!")
        print(f"Status Code: {response.status_code}")
        print(f"Error: {response.text}\n")
        return None


def test_model_comparison(token: str):
    """Test model comparison dashboard"""
    
    print(f"\n{'='*70}")
    print(f"📊 Testing Model Comparison Dashboard")
    print(f"{'='*70}\n")
    
    # First, list available models
    list_endpoint = f"{API_BASE_URL}/api/v1/ml/models/available"
    headers = {"Authorization": f"Bearer {token}"}
    
    print("📋 Fetching available models...")
    list_response = requests.get(list_endpoint, headers=headers)
    
    if list_response.status_code == 200:
        available = list_response.json()
        print(f"✅ Found {available['total_models']} trained models\n")
        
        model_names = [m['model_name'] for m in available['models'] if m.get('available', False)]
        
        if not model_names:
            print("❌ No models available for comparison")
            return None
        
        print(f"Available models: {', '.join(model_names)}\n")
    else:
        print("⚠️ Could not fetch model list, using defaults")
        model_names = ["xgboost", "lightgbm", "random_forest"]
    
    # Compare models
    compare_endpoint = f"{API_BASE_URL}/api/v1/ml/compare"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    request_data = {
        "model_names": model_names[:5],  # Compare up to 5 models
        "version": "v1",
        "metric": "test_auc"
    }
    
    print(f"📊 Comparing {len(request_data['model_names'])} models...")
    response = requests.post(compare_endpoint, json=request_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n✅ Model Comparison Complete!\n")
        print(f"{'─'*70}")
        print(f"Comparison Metric: {result['comparison_metric'].upper()}")
        print(f"Best Model: {result['best_model']}")
        print(f"\n📊 MODEL RANKING")
        print(f"{'─'*70}")
        print(f"{'Rank':<6} {'Model':<20} {'Test AUC':<12} {'Test F1':<12} {'CV AUC':<12}")
        print(f"{'─'*70}")
        
        for rank, model in enumerate(result['models'], 1):
            print(f"{rank:<6} {model['model_name']:<20} "
                  f"{model['test_auc']:>10.4f}  "
                  f"{model['test_f1']:>10.4f}  "
                  f"{model['cv_auc']:>10.4f}")
        
        print(f"{'─'*70}")
        
        # Get detailed info for best model
        print(f"\n🏆 BEST MODEL DETAILS: {result['best_model']}")
        print(f"{'─'*70}")
        
        detail_endpoint = f"{API_BASE_URL}/api/v1/ml/compare/detailed/{result['best_model']}"
        detail_response = requests.get(f"{detail_endpoint}?version=v1", headers={"Authorization": f"Bearer {token}"})
        
        if detail_response.status_code == 200:
            details = detail_response.json()
            
            print(f"\nTest Set Metrics:")
            for metric, value in details['metrics']['test_set'].items():
                print(f"  {metric:20}: {value:.4f}")
            
            print(f"\nConfiguration:")
            print(f"  N Folds:      {details['configuration']['n_folds']}")
            print(f"  N Features:   {details['configuration']['n_features']}")
            print(f"  Training Time: {details['configuration']['training_time_seconds']:.1f}s")
            
            if details['hyperparameters']:
                print(f"\nBest Hyperparameters:")
                for param, value in list(details['hyperparameters'].items())[:5]:
                    print(f"  {param:20}: {value}")
        
        print(f"{'─'*70}\n")
        
        return result
    
    else:
        print(f"\n❌ Model Comparison Failed!")
        print(f"Status Code: {response.status_code}")
        print(f"Error: {response.text}\n")
        return None


def main():
    parser = argparse.ArgumentParser(description="Test Scorecard & Model Comparison")
    parser.add_argument("--test", default="all", choices=["scorecard", "compare", "all"],
                       help="Test type")
    parser.add_argument("--model", default="xgboost", help="Model name for scorecard test")
    parser.add_argument("--version", default="v1", help="Model version")
    parser.add_argument("--username", default=USERNAME, help="API username")
    parser.add_argument("--password", default=PASSWORD, help="API password")
    
    args = parser.parse_args()
    
    try:
        # Authenticate
        print("🔐 Authenticating...")
        token = get_auth_token(args.username, args.password)
        print(f"✅ Authentication successful!\n")
        
        # Run tests
        if args.test in ["scorecard", "all"]:
            test_scorecard(token, args.model, args.version)
        
        if args.test in ["compare", "all"]:
            test_model_comparison(token)
        
        print("\n✅ All tests completed!\n")
    
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        raise


if __name__ == "__main__":
    main()
