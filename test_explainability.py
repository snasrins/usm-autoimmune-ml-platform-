"""
Test SHAP Explainability + Gemma-4-E4B Conversational AI
Tests explainability endpoints (USMA-50)

Usage:
    # Test SHAP explanation
    python test_explainability.py --test shap --model xgboost
    
    # Test Gemma chat
    python test_explainability.py --test chat --question "What is SLE?"
    
    # Test prediction explanation
    python test_explainability.py --test explain-prediction
    
    # Test all features
    python test_explainability.py --test all
"""
import requests
import json
import argparse
from typing import Dict
import base64
from pathlib import Path


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


def test_shap_explanation(token: str, model_name: str = "xgboost", version: str = "v1"):
    """Test SHAP explainability endpoint"""
    
    print(f"\n{'='*60}")
    print(f"🔍 Testing SHAP Explanation - {model_name}/{version}")
    print(f"{'='*60}\n")
    
    endpoint = f"{API_BASE_URL}/api/v1/ml/explain"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    patient_data = create_sample_patient_data()
    
    request_data = {
        "model_name": model_name,
        "version": version,
        "patient_data": patient_data,
        "top_k": 10,
        "generate_plot": True
    }
    
    print("📤 Requesting SHAP explanation...")
    response = requests.post(endpoint, json=request_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n✅ SHAP Explanation Generated!\n")
        print(f"{'─'*60}")
        print(f"Model: {result['model_name']} ({result['version']})")
        print(f"Predicted Class: {result['predicted_class']}")
        print(f"Base Value: {result['base_value']:.4f}")
        
        print(f"\n📊 Top Contributing Features:\n")
        for i, feat in enumerate(result['top_features'], 1):
            feature_name = feat['feature'].replace('_', ' ').title()
            shap_val = feat['shap_value']
            feat_val = feat['feature_value']
            contribution = feat['contribution']
            
            symbol = '📈' if contribution == 'positive' else '📉'
            sign = '+' if shap_val > 0 else ''
            
            print(f"{i:2}. {symbol} {feature_name:40} | SHAP: {sign}{shap_val:7.4f} | Value: {feat_val:7.2f}")
        
        print(f"\n💬 Natural Language Explanation:\n")
        print(result['explanation_text'])
        
        # Save waterfall plot if available
        if result.get('waterfall_plot'):
            print(f"\n📊 Waterfall plot generated (base64 encoded)")
            
            # Save to file
            plot_data = base64.b64decode(result['waterfall_plot'])
            output_path = Path(f"shap_waterfall_{model_name}_{version}.png")
            output_path.write_bytes(plot_data)
            print(f"   Saved to: {output_path}")
        
        print(f"{'─'*60}\n")
        return result
    
    else:
        print(f"\n❌ SHAP Explanation Failed!")
        print(f"Status Code: {response.status_code}")
        print(f"Error: {response.text}\n")
        return None


def test_gemma_chat(token: str, question: str):
    """Test Gemma conversational AI"""
    
    print(f"\n{'='*60}")
    print(f"💬 Testing Gemma-4-E4B Conversational AI")
    print(f"{'='*60}\n")
    
    endpoint = f"{API_BASE_URL}/api/v1/ml/chat"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    request_data = {
        "message": question,
        "temperature": 0.7
    }
    
    print(f"❓ Question: {question}\n")
    print("🤖 Gemma is thinking...\n")
    
    response = requests.post(endpoint, json=request_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"✅ Response Generated!\n")
        print(f"{'─'*60}")
        print(f"{result['response']}")
        print(f"{'─'*60}")
        print(f"\nModel: {result['model']}")
        print(f"Device: {result['device']}")
        print(f"Tokens: {result['tokens_generated']}\n")
        
        return result
    
    else:
        print(f"\n❌ Chat Failed!")
        print(f"Status Code: {response.status_code}")
        print(f"Error: {response.text}\n")
        return None


def test_prediction_explanation(token: str):
    """Test natural language prediction explanation"""
    
    print(f"\n{'='*60}")
    print(f"📝 Testing Prediction Explanation with Gemma")
    print(f"{'='*60}\n")
    
    endpoint = f"{API_BASE_URL}/api/v1/ml/explain-prediction-nl"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Sample prediction result
    prediction_result = {
        "prediction": "Moderate",
        "confidence": 0.65,
        "probabilities": {
            "Mild": 0.25,
            "Moderate": 0.65,
            "Severe": 0.10
        }
    }
    
    # Sample SHAP explanation
    shap_explanation = {
        "top_features": [
            {"feature": "disease_activity_SLEDAI_score", "shap_value": 0.45, "feature_value": 8.0},
            {"feature": "demographics_age", "shap_value": 0.12, "feature_value": 35.0},
            {"feature": "lab_results_CRP_ESR_ratio", "shap_value": 0.08, "feature_value": 0.28}
        ]
    }
    
    request_data = {
        "prediction_result": prediction_result,
        "shap_explanation": shap_explanation
    }
    
    print("📊 Prediction Details:")
    print(f"   Severity: {prediction_result['prediction']}")
    print(f"   Confidence: {prediction_result['confidence']*100:.1f}%\n")
    
    print("🤖 Generating clinical explanation...\n")
    
    response = requests.post(endpoint, json=request_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"✅ Clinical Explanation:\n")
        print(f"{'─'*60}")
        print(result['response'])
        print(f"{'─'*60}\n")
        
        return result
    
    else:
        print(f"\n❌ Explanation Failed!")
        print(f"Error: {response.text}\n")
        return None


def test_clinical_question(token: str, question: str):
    """Test clinical question answering"""
    
    print(f"\n{'='*60}")
    print(f"🏥 Testing Clinical Question Answering")
    print(f"{'='*60}\n")
    
    endpoint = f"{API_BASE_URL}/api/v1/ml/ask-clinical"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    request_data = {
        "question": question,
        "patient_context": {
            "lab_results_Anti_dsDNA": 1.8,
            "disease_activity_SLEDAI_score": 10
        }
    }
    
    print(f"❓ Clinical Question: {question}\n")
    print("🤖 Consulting medical knowledge base...\n")
    
    response = requests.post(endpoint, json=request_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"✅ Clinical Answer:\n")
        print(f"{'─'*60}")
        print(result['response'])
        print(f"{'─'*60}\n")
        
        return result
    
    else:
        print(f"\n❌ Question Answering Failed!")
        print(f"Error: {response.text}\n")
        return None


def main():
    parser = argparse.ArgumentParser(description="Test ML Explainability & Conversational AI")
    parser.add_argument("--test", default="all", choices=["shap", "chat", "explain-prediction", "clinical", "all"],
                       help="Test type")
    parser.add_argument("--model", default="xgboost", help="Model name for SHAP test")
    parser.add_argument("--version", default="v1", help="Model version")
    parser.add_argument("--question", default="What is Systemic Lupus Erythematosus?",
                       help="Question for chat test")
    parser.add_argument("--username", default=USERNAME, help="API username")
    parser.add_argument("--password", default=PASSWORD, help="API password")
    
    args = parser.parse_args()
    
    try:
        # Authenticate
        print("🔐 Authenticating...")
        token = get_auth_token(args.username, args.password)
        print(f"✅ Authentication successful!\n")
        
        # Run tests
        if args.test in ["shap", "all"]:
            test_shap_explanation(token, args.model, args.version)
        
        if args.test in ["chat", "all"]:
            test_gemma_chat(token, args.question)
        
        if args.test in ["explain-prediction", "all"]:
            test_prediction_explanation(token)
        
        if args.test in ["clinical", "all"]:
            test_clinical_question(token, "What is the significance of elevated Anti-dsDNA antibodies?")
        
        print("\n✅ All tests completed!\n")
    
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        raise


if __name__ == "__main__":
    main()
