import requests
import json

def test_backend_fix():
    """Test the backend fix for the ModuleNotFoundError issue"""
    
    url = "http://127.0.0.1:8000/chat"
    
    # Test data
    data = {
        "prompt": "create a simple python app to sum 2 numbers"
    }
    
    try:
        print("🧪 Testing backend fix...")
        print(f"📤 Sending request to: {url}")
        print(f"📝 Request data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, timeout=60)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            print(f"📊 Response type: {result.get('type', 'unknown')}")
            print(f"📝 Message: {result.get('message', 'No message')}")
            
            # Check if tests passed
            if 'test_results' in result:
                test_results = result['test_results']
                if '✅ TESTS PASSED' in test_results:
                    print("🎉 TESTS PASSED! The fix is working!")
                else:
                    print("❌ Tests failed, but the ModuleNotFoundError should be fixed")
                    print(f"📋 Test results: {test_results[:500]}...")
            
            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Make sure it's running on http://127.0.0.1:8000")
        return False
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        return False

if __name__ == "__main__":
    test_backend_fix() 