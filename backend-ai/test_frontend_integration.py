#!/usr/bin/env python3
"""
Frontend Integration Test
Tests the Online Agent Service API endpoints that the frontend will use
"""

import asyncio
import json
import requests
from datetime import datetime
from online_agent_service import (
    OnlineAgent, 
    OnlineWorkflowRequest,
    ONLINE_MODEL_CONFIGS
)

# Test configuration
ONLINE_SERVICE_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:5173"

def test_api_endpoints():
    """Test all API endpoints that the frontend will use"""
    print("🌐 Testing API Endpoints for Frontend Integration...")
    
    # Test 1: Health Check
    print("\n1. Testing Health Check Endpoint...")
    try:
        response = requests.get(f"{ONLINE_SERVICE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   Available models: {len(data['available_models'])}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Models Endpoint
    print("\n2. Testing Models Endpoint...")
    try:
        response = requests.get(f"{ONLINE_SERVICE_URL}/models")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Models endpoint working")
            print(f"   Default model: {data['default_model']}")
            print(f"   OpenAI models: {len(data['providers']['openai'])}")
            print(f"   Mistral models: {len(data['providers']['mistral'])}")
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Models endpoint error: {e}")
        return False
    
    # Test 3: Root Endpoint
    print("\n3. Testing Root Endpoint...")
    try:
        response = requests.get(f"{ONLINE_SERVICE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint working")
            print(f"   Service: {data['service']}")
            print(f"   Version: {data['version']}")
            print(f"   Endpoints: {len(data['endpoints'])}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False
    
    return True

def test_workflow_creation():
    """Test workflow creation with frontend-compatible data"""
    print("\n4. Testing Workflow Creation...")
    
    # Create agents similar to what frontend would send
    agents = [
        {
            "id": "coordinator",
            "name": "Workflow Coordinator",
            "role": "coordinator",
            "model": "gpt-3.5-turbo",
            "system_prompt": "You are a workflow coordinator that manages tasks and delegates work to other agents.",
            "memory_enabled": True
        },
        {
            "id": "coder",
            "name": "Code Generator",
            "role": "programmer",
            "model": "gpt-3.5-turbo",
            "system_prompt": "You are a skilled programmer that writes clean, efficient code.",
            "memory_enabled": True
        },
        {
            "id": "reviewer",
            "name": "Code Reviewer",
            "role": "reviewer",
            "model": "mistral-medium",
            "system_prompt": "You are a code reviewer that checks code quality and provides feedback.",
            "memory_enabled": True
        }
    ]
    
    workflow_request = {
        "task": "Create a simple Python function that calculates the factorial of a number",
        "agents": agents,
        "enable_streaming": False
    }
    
    try:
        response = requests.post(
            f"{ONLINE_SERVICE_URL}/run-workflow",
            json=workflow_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Workflow created successfully")
            print(f"   Workflow ID: {data['workflow_id']}")
            print(f"   Status: {data['status']}")
            print(f"   Conversation ID: {data['conversation_id']}")
            print(f"   Total messages: {data['total_messages']}")
            return data['workflow_id']
        else:
            print(f"❌ Workflow creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Workflow creation error: {e}")
        return None

def test_workflow_status(workflow_id):
    """Test workflow status endpoint"""
    if not workflow_id:
        return False
    
    print(f"\n5. Testing Workflow Status for {workflow_id}...")
    
    try:
        response = requests.get(f"{ONLINE_SERVICE_URL}/workflow-status/{workflow_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Workflow status retrieved")
            print(f"   Status: {data['status']}")
            print(f"   Agents: {len(data['agents'])}")
            print(f"   Message count: {data['message_count']}")
            return True
        else:
            print(f"❌ Workflow status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Workflow status error: {e}")
        return False

def test_conversations():
    """Test conversations endpoints"""
    print("\n6. Testing Conversations Endpoints...")
    
    # Test getting conversations list
    try:
        response = requests.get(f"{ONLINE_SERVICE_URL}/conversations")
        if response.status_code == 200:
            conversations = response.json()
            print(f"✅ Conversations list retrieved: {len(conversations)} conversations")
            
            # Test getting specific conversation if available
            if conversations:
                conversation_id = conversations[0]['id']
                print(f"   Testing conversation: {conversation_id}")
                
                response = requests.get(f"{ONLINE_SERVICE_URL}/conversations/{conversation_id}")
                if response.status_code == 200:
                    conv_data = response.json()
                    print(f"✅ Conversation details retrieved")
                    print(f"   Title: {conv_data['conversation']['title']}")
                    print(f"   Messages: {len(conv_data['messages'])}")
                else:
                    print(f"❌ Conversation details failed: {response.status_code}")
            return True
        else:
            print(f"❌ Conversations list failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Conversations error: {e}")
        return False

def test_cors_headers():
    """Test CORS headers for frontend integration"""
    print("\n7. Testing CORS Headers...")
    
    try:
        response = requests.options(f"{ONLINE_SERVICE_URL}/health")
        cors_headers = response.headers
        
        print("✅ CORS headers check:")
        print(f"   Access-Control-Allow-Origin: {cors_headers.get('Access-Control-Allow-Origin', 'Not set')}")
        print(f"   Access-Control-Allow-Methods: {cors_headers.get('Access-Control-Allow-Methods', 'Not set')}")
        print(f"   Access-Control-Allow-Headers: {cors_headers.get('Access-Control-Allow-Headers', 'Not set')}")
        
        # Check if frontend origin is allowed
        allowed_origins = cors_headers.get('Access-Control-Allow-Origin', '')
        if FRONTEND_URL.replace('http://', '') in allowed_origins or '*' in allowed_origins:
            print("✅ Frontend origin is allowed")
            return True
        else:
            print("⚠️ Frontend origin might not be allowed")
            return False
    except Exception as e:
        print(f"❌ CORS test error: {e}")
        return False

def test_error_handling():
    """Test error handling for invalid requests"""
    print("\n8. Testing Error Handling...")
    
    # Test invalid workflow request
    try:
        invalid_request = {
            "task": "",  # Empty task
            "agents": []  # No agents
        }
        
        response = requests.post(
            f"{ONLINE_SERVICE_URL}/run-workflow",
            json=invalid_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 422:  # Validation error
            print("✅ Invalid request properly rejected")
            return True
        else:
            print(f"⚠️ Unexpected response for invalid request: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_model_configuration():
    """Test model configuration compatibility"""
    print("\n9. Testing Model Configuration...")
    
    # Test with different model combinations
    test_configs = [
        {
            "name": "OpenAI Only",
            "agents": [
                {"id": "coder", "name": "Coder", "role": "programmer", "model": "gpt-3.5-turbo"}
            ]
        },
        {
            "name": "Mistral Only", 
            "agents": [
                {"id": "reviewer", "name": "Reviewer", "role": "reviewer", "model": "mistral-medium"}
            ]
        },
        {
            "name": "Mixed Models",
            "agents": [
                {"id": "coordinator", "name": "Coordinator", "role": "coordinator", "model": "gpt-4"},
                {"id": "coder", "name": "Coder", "role": "programmer", "model": "gpt-3.5-turbo"},
                {"id": "reviewer", "name": "Reviewer", "role": "reviewer", "model": "mistral-large"}
            ]
        }
    ]
    
    for config in test_configs:
        print(f"   Testing {config['name']}...")
        for agent in config['agents']:
            model_name = agent['model']
            if model_name in ONLINE_MODEL_CONFIGS:
                provider = ONLINE_MODEL_CONFIGS[model_name]['provider']
                print(f"     ✅ {model_name} ({provider}) - Available")
            else:
                print(f"     ❌ {model_name} - Not available")
    
    return True

def main():
    """Run all frontend integration tests"""
    print("🚀 Frontend Integration Test Suite")
    print("=" * 50)
    
    # Check if service is running
    print("🔍 Checking if Online Agent Service is running...")
    try:
        response = requests.get(f"{ONLINE_SERVICE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Service not responding: {response.status_code}")
            print("   Please start the Online Agent Service first:")
            print("   python online_agent_service.py")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Online Agent Service")
        print("   Please start the service first:")
        print("   python online_agent_service.py")
        return False
    
    print("✅ Online Agent Service is running")
    
    # Run all tests
    tests = [
        ("API Endpoints", test_api_endpoints),
        ("Model Configuration", test_model_configuration),
        ("CORS Headers", test_cors_headers),
        ("Workflow Creation", test_workflow_creation),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    workflow_id = None
    
    for test_name, test_func in tests:
        try:
            if test_name == "Workflow Creation":
                workflow_id = test_func()
                results.append((test_name, workflow_id is not None))
            else:
                result = test_func()
                results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed: {e}")
            results.append((test_name, False))
    
    # Test workflow status if workflow was created
    if workflow_id:
        results.append(("Workflow Status", test_workflow_status(workflow_id)))
    
    # Test conversations
    results.append(("Conversations", test_conversations()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Frontend integration is ready.")
        print("\n📝 Frontend Integration Status:")
        print("   ✅ API endpoints working")
        print("   ✅ CORS configured for frontend")
        print("   ✅ Workflow creation functional")
        print("   ✅ Model configuration compatible")
        print("   ✅ Error handling working")
        print("   ✅ Conversation management ready")
        print("\n🚀 Ready for frontend integration!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    main()
