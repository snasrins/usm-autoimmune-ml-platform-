"""
Dr. Myra Backend Test Script
Tests the Gemma LLM chat endpoint to verify natural language understanding

Usage:
    python test_dr_myra.py
"""
import requests
import json
import time

# Configuration
BACKEND_URL = "http://100.106.132.15:8001"
API_ENDPOINT = f"{BACKEND_URL}/api/v1/ml/chat"

# Test credentials (replace with actual user)
TEST_USERNAME = "test@usm.my"
TEST_PASSWORD = "test123"

def get_auth_token():
    """Login and get JWT token"""
    print("🔐 Logging in...")
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Authentication successful")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None


def test_dr_myra_chat(token, message):
    """Test Dr. Myra chat endpoint"""
    print(f"\n🤖 Testing Dr. Myra with: '{message}'")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": message,
        "context": {
            "current_page": "/dashboard",
            "page_context": "Testing from script"
        },
        "conversation_history": None,
        "temperature": 0.7
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(
            API_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=60  # Gemma can take time on first load
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response received in {elapsed:.2f}s")
            print(f"\n📊 Model: {data.get('model')}")
            print(f"📊 Device: {data.get('device')}")
            print(f"📊 Tokens: {data.get('tokens_generated')}")
            print(f"\n💬 Response:\n{data.get('response')}\n")
            
            # Check if using real LLM or fallback
            if data.get('model') == 'gemma-4-E4B':
                print("🎉 SUCCESS: Using Gemma LLM!")
                return True
            elif data.get('model') == 'fallback-rules':
                print("⚠️  WARNING: Using fallback mode (Gemma not loaded)")
                return False
            else:
                print(f"🤔 Unknown model: {data.get('model')}")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (Gemma might be loading for first time)")
        print("💡 Try again - subsequent calls will be faster")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run Dr. Myra tests"""
    print("=" * 60)
    print("Dr. Myra Backend Test")
    print("=" * 60)
    
    # Step 1: Authenticate
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without authentication")
        print("💡 Update TEST_USERNAME and TEST_PASSWORD in this script")
        return
    
    # Step 2: Test various queries
    test_queries = [
        "explain the platform to me",
        "How do I preprocess my data?",
        "What is SHAP?",
        "Tell me about SLE disease severity",
    ]
    
    results = []
    for query in test_queries:
        success = test_dr_myra_chat(token, query)
        results.append((query, success))
        time.sleep(1)  # Pause between requests
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for query, success in results:
        status = "✅ LLM" if success else "⚠️  Fallback"
        print(f"{status}: {query[:50]}")
    
    print(f"\nResults: {success_count}/{total_count} using Gemma LLM")
    
    if success_count == 0:
        print("\n💡 Troubleshooting Tips:")
        print("1. Check backend logs for Gemma loading errors")
        print("2. Verify HUGGINGFACE_TOKEN environment variable")
        print("3. Ensure GPU has enough memory (nvidia-smi)")
        print("4. Check transformers library version (pip list | grep transformers)")
    elif success_count == total_count:
        print("\n🎉 All tests passed! Dr. Myra is working perfectly!")
    else:
        print("\n⚠️  Mixed results - some queries using LLM, others fallback")


if __name__ == "__main__":
    main()
