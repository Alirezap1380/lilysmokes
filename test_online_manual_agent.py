#!/usr/bin/env python3
"""
Test script for Online Manual Agent functionality
This script tests the key components needed for the online manual agent system.
"""

import requests
import json
import time
import os
from typing import Dict, Any

# Configuration
ONLINE_SERVICE_URL = "http://localhost:8001"
MAIN_SERVICE_URL = "http://localhost:8000"

def test_online_service_health():
    """Test if the online agent service is running and healthy"""
    try:
        response = requests.get(f"{ONLINE_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Online service health check passed")
            print(f"   Service: {data.get('service', 'Unknown')}")
            print(f"   Status: {data.get('status', 'Unknown')}")
            return True
        else:
            print(f"❌ Online service health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Online service health check error: {e}")
        return False

def test_online_models():
    """Test if online models are available"""
    try:
        response = requests.get(f"{ONLINE_SERVICE_URL}/models", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Online models check passed")
            print(f"   Available models: {len(data.get('available_models', {}))}")
            
            # Check for specific model providers
            models = data.get('available_models', {})
            if 'mistral-small' in models:
                print("   ✅ Mistral models available")
            if 'gemini-pro' in models:
                print("   ✅ Gemini models available")
            if 'gpt-3.5-turbo' in models:
                print("   ✅ OpenAI models available")
                
            return True
        else:
            print(f"❌ Online models check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Online models check error: {e}")
        return False

def test_simple_workflow():
    """Test a simple online workflow"""
    workflow_request = {
        "task": "Say hello and introduce yourself",
        "agents": [
            {
                "id": "coordinator",
                "name": "Coordinator",
                "role": "coordinator",
                "model": "mistral-small",
                "system_prompt": "You are a helpful coordinator agent. Respond briefly and clearly.",
                "memory_enabled": True
            }
        ],
        "enable_streaming": True,
        "conversation_id": None
    }
    
    try:
        print("🔄 Testing simple workflow...")
        response = requests.post(
            f"{ONLINE_SERVICE_URL}/run-workflow",
            json=workflow_request,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Simple workflow test passed")
            print(f"   Workflow ID: {data.get('workflow_id', 'Unknown')}")
            print(f"   Status: {data.get('status', 'Unknown')}")
            print(f"   Messages: {len(data.get('message_history', []))}")
            
            # Show first message if available
            messages = data.get('message_history', [])
            if messages:
                first_msg = messages[0]
                print(f"   First message: {first_msg.get('from_agent', 'Unknown')} → {first_msg.get('to_agent', 'Unknown')}")
                print(f"   Content: {first_msg.get('content', '')[:100]}...")
            
            return True
        else:
            print(f"❌ Simple workflow test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Simple workflow test error: {e}")
        return False

def test_workflow_status_polling():
    """Test workflow status polling (simulates frontend behavior)"""
    # First run a workflow
    workflow_request = {
        "task": "Count from 1 to 3",
        "agents": [
            {
                "id": "counter",
                "name": "Counter",
                "role": "counter",
                "model": "mistral-small",
                "system_prompt": "You are a counting agent. Count the requested numbers.",
                "memory_enabled": True
            }
        ],
        "enable_streaming": True,
        "conversation_id": None
    }
    
    try:
        print("🔄 Testing workflow status polling...")
        response = requests.post(
            f"{ONLINE_SERVICE_URL}/run-workflow",
            json=workflow_request,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            workflow_id = data.get('workflow_id')
            
            if workflow_id:
                print(f"   Workflow ID: {workflow_id}")
                
                # Poll for status updates
                max_polls = 5
                for i in range(max_polls):
                    time.sleep(2)  # Wait 2 seconds between polls
                    
                    status_response = requests.get(
                        f"{ONLINE_SERVICE_URL}/workflow-status/{workflow_id}",
                        timeout=5
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', 'unknown')
                        message_count = len(status_data.get('message_history', []))
                        
                        print(f"   Poll {i+1}: Status={status}, Messages={message_count}")
                        
                        if status in ['completed', 'error']:
                            print("✅ Workflow completed")
                            return True
                    else:
                        print(f"   Poll {i+1}: Status check failed")
                
                print("⚠️  Workflow did not complete within expected time")
                return False
            else:
                print("❌ No workflow ID returned")
                return False
        else:
            print(f"❌ Workflow creation failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Workflow polling test error: {e}")
        return False

def check_api_keys():
    """Check if API keys are configured"""
    print("🔑 Checking API key configuration...")
    
    # Try to load .env file from backend-ai directory
    try:
        from dotenv import load_dotenv
        env_path = os.path.join('backend-ai', '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"   📁 Loaded .env file from: {env_path}")
        else:
            print(f"   ⚠️  .env file not found at: {env_path}")
    except ImportError:
        print("   ⚠️  python-dotenv not installed, trying environment variables only")
    
    # Check environment variables
    keys = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'MISTRAL_API_KEY': os.getenv('MISTRAL_API_KEY'),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY')
    }
    
    configured_keys = []
    for key_name, key_value in keys.items():
        if key_value and key_value != 'your_openai_api_key_here':
            configured_keys.append(key_name)
            print(f"   ✅ {key_name}: Configured")
        else:
            print(f"   ❌ {key_name}: Not configured")
    
    if configured_keys:
        print(f"   📊 Total configured keys: {len(configured_keys)}")
        return True
    else:
        print("   ⚠️  No API keys configured - online mode will not work")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Online Manual Agent System")
    print("=" * 50)
    
    # Check API keys first
    api_keys_ok = check_api_keys()
    print()
    
    # Test online service
    health_ok = test_online_service_health()
    print()
    
    if health_ok:
        models_ok = test_online_models()
        print()
        
        if api_keys_ok:
            workflow_ok = test_simple_workflow()
            print()
            
            if workflow_ok:
                polling_ok = test_workflow_status_polling()
                print()
            else:
                polling_ok = False
        else:
            workflow_ok = False
            polling_ok = False
            print("⚠️  Skipping workflow tests due to missing API keys")
    else:
        models_ok = False
        workflow_ok = False
        polling_ok = False
        print("⚠️  Skipping remaining tests due to service not running")
    
    # Summary
    print("=" * 50)
    print("📊 Test Summary:")
    print(f"   API Keys: {'✅' if api_keys_ok else '❌'}")
    print(f"   Service Health: {'✅' if health_ok else '❌'}")
    print(f"   Models Available: {'✅' if models_ok else '❌'}")
    print(f"   Simple Workflow: {'✅' if workflow_ok else '❌'}")
    print(f"   Status Polling: {'✅' if polling_ok else '❌'}")
    
    if all([api_keys_ok, health_ok, models_ok, workflow_ok, polling_ok]):
        print("\n🎉 All tests passed! Online manual agent system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the configuration and try again.")
        
        if not api_keys_ok:
            print("   💡 Set up API keys in the .env file")
        if not health_ok:
            print("   💡 Start the online agent service: python online_agent_service.py")
        if not models_ok:
            print("   💡 Check API key validity and service configuration")

if __name__ == "__main__":
    main()
