#!/usr/bin/env python3
"""
Quick Test Script for SHAP + Gemma AI (USMA-50)
Tests explainability features end-to-end
"""
import requests
import json
import sys
import time

# Configuration
BASE_URL = "http://172.24.175.24:8000/api/v1"
TOKEN = "YOUR_JWT_TOKEN_HERE"  # Replace with actual token

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Sample patient data
SAMPLE_PATIENT = {
    "demographics_age": 35,
    "lab_results_CRP": 1.5,
    "lab_results_ESR": 45,
    "lab_results_C3": 0.45,
    "lab_results_C4": 0.08,
    "lab_results_PLT": 230,
    "lab_results_WBC": 5.2,
    "lab_results_HGB": 11.5,
    "disease_activity_SLEDAI_score": 8
}


def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def test_shap_explanation():
    """Test SHAP explanation endpoint"""
    print_header("TEST 1: SHAP Explanation")
    
    payload = {
        "model_name": "xgboost",
        "version": "v1",
        "patient_data": SAMPLE_PATIENT,
        "top_k": 10,
        "generate_plot": True
    }
    
    print("📤 Requesting SHAP explanation...")
    print(f"Endpoint: POST {BASE_URL}/ml/explain")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/ml/explain",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS ({elapsed:.2f}s)")
            print(f"\n📊 Results:")
            print(f"   Model: {result['model_name']}")
            print(f"   Predicted Class: {result.get('predicted_class', 'N/A')}")
            print(f"   Base Value: {result['base_value']:.4f}")
            print(f"   Top Features: {len(result['top_features'])}")
            print(f"   Waterfall Plot: {'✅ Generated' if result.get('waterfall_plot') else '❌ None'}")
            
            print(f"\n🔝 Top 5 Contributing Features:")
            for i, feat in enumerate(result['top_features'][:5], 1):
                direction = "↑" if feat['contribution'] == 'positive' else "↓"
                print(f"   {i}. {feat['feature']}: {feat['shap_value']:+.4f} {direction}")
            
            return True
        else:
            print(f"❌ FAILED (Status {response.status_code})")
            print(f"   Error: {response.json().get('detail', 'Unknown error')}")
            return False
    
    except requests.exceptions.Timeout:
        print(f"❌ FAILED (Timeout after 30s)")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_gemma_chat():
    """Test Gemma conversational AI"""
    print_header("TEST 2: Gemma AI Chat")
    
    payload = {
        "message": "What does a SLEDAI score of 8 indicate?",
        "temperature": 0.7
    }
    
    print("💬 Sending message to Dr. Myra...")
    print(f"Endpoint: POST {BASE_URL}/ml/chat")
    print(f"Message: \"{payload['message']}\"")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/ml/chat",
            headers=HEADERS,
            json=payload,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS ({elapsed:.2f}s)")
            print(f"\n🤖 Dr. Myra's Response:")
            print(f"   {result['response'][:200]}...")
            print(f"\n📈 Metadata:")
            print(f"   Model: {result['model']}")
            print(f"   Device: {result['device']}")
            print(f"   Tokens: {result['tokens_generated']}")
            
            return True
        else:
            print(f"❌ FAILED (Status {response.status_code})")
            print(f"   Error: {response.json().get('detail', 'Unknown error')}")
            return False
    
    except requests.exceptions.Timeout:
        print(f"❌ FAILED (Timeout after 60s)")
        print(f"   Note: First Gemma request may take 2+ minutes (model loading)")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_chat_with_context():
    """Test Gemma chat with SHAP context"""
    print_header("TEST 3: Gemma AI with SHAP Context")
    
    # First get SHAP explanation
    shap_payload = {
        "model_name": "xgboost",
        "version": "v1",
        "patient_data": SAMPLE_PATIENT,
        "top_k": 5,
        "generate_plot": False
    }
    
    print("📊 Getting SHAP context...")
    
    try:
        shap_response = requests.post(
            f"{BASE_URL}/ml/explain",
            headers=HEADERS,
            json=shap_payload,
            timeout=30
        )
        
        if shap_response.status_code != 200:
            print(f"❌ SHAP request failed, skipping context test")
            return False
        
        shap_result = shap_response.json()
        
        # Now chat with SHAP context
        chat_payload = {
            "message": "Why is CRP the most important feature in this prediction?",
            "context": {
                "prediction": {
                    "predicted_class": shap_result.get('predicted_class'),
                    "base_value": shap_result['base_value']
                },
                "shap": shap_result
            },
            "temperature": 0.7
        }
        
        print("💬 Asking about SHAP results...")
        print(f"Message: \"{chat_payload['message']}\"")
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/ml/chat",
            headers=HEADERS,
            json=chat_payload,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS ({elapsed:.2f}s)")
            print(f"\n🤖 Dr. Myra's Context-Aware Response:")
            print(f"   {result['response'][:300]}...")
            
            return True
        else:
            print(f"❌ FAILED (Status {response.status_code})")
            print(f"   Error: {response.json().get('detail', 'Unknown error')}")
            return False
    
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_clinical_question():
    """Test clinical question answering"""
    print_header("TEST 4: Clinical Question Answering")
    
    payload = {
        "question": "What is the significance of elevated Anti-dsDNA antibodies in SLE?",
        "patient_context": {
            "lab_results_Anti_dsDNA": 1.8,
            "disease_activity_SLEDAI_score": 10
        }
    }
    
    print("🩺 Asking clinical question...")
    print(f"Endpoint: POST {BASE_URL}/ml/ask-clinical")
    print(f"Question: \"{payload['question']}\"")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/ml/ask-clinical",
            headers=HEADERS,
            json=payload,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS ({elapsed:.2f}s)")
            print(f"\n🤖 Clinical Answer:")
            print(f"   {result['response'][:250]}...")
            
            return True
        else:
            print(f"❌ FAILED (Status {response.status_code})")
            print(f"   Error: {response.json().get('detail', 'Unknown error')}")
            return False
    
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  SHAP + GEMMA AI TEST SUITE (USMA-50)")
    print("  USM Autoimmune ML Platform")
    print("="*60)
    
    if TOKEN == "YOUR_JWT_TOKEN_HERE":
        print("\n❌ ERROR: Please set TOKEN variable with your JWT token")
        print("\nTo get token:")
        print("1. Login at http://172.24.175.24:5173")
        print("2. Open browser DevTools > Network")
        print("3. Look for Authorization header in any API request")
        print("4. Copy the token (after 'Bearer ')")
        sys.exit(1)
    
    results = []
    
    # Run tests
    results.append(("SHAP Explanation", test_shap_explanation()))
    time.sleep(2)
    
    results.append(("Gemma AI Chat", test_gemma_chat()))
    time.sleep(2)
    
    results.append(("Chat with SHAP Context", test_chat_with_context()))
    time.sleep(2)
    
    results.append(("Clinical Question", test_clinical_question()))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}  {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! USMA-50 is working correctly.")
    else:
        print(f"\n⚠️  {total-passed} test(s) failed. Check logs for details.")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
