#!/usr/bin/env python3
"""
Test script for the Online Agent Service
This script tests the basic functionality of the online agent service
"""

import requests
import json
import os
import sys
from datetime import datetime

# Configuration
ONLINE_SERVICE_URL = "http://localhost:8001"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{ONLINE_SERVICE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   Available models: {data['available_models']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_models_endpoint():
    """Test the models endpoint"""
    print("\n🔍 Testing models endpoint...")
    try:
        response = requests.get(f"{ONLINE_SERVICE_URL}/models")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Models endpoint passed")
            print(f"   Default model: {data['default_model']}")
            print(f"   Providers: {list(data['providers'].keys())}")
            return True
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Models endpoint error: {e}")
        return False

def test_workflow_execution():
    """Test a simple workflow execution"""
    print("\n🔍 Testing workflow execution...")
    
    # Check if API keys are available
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not openai_key and not anthropic_key:
        print("⚠️  No API keys found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY to test workflow execution.")
        return False
    
    # Create a simple workflow request
    workflow_request = {
        "task": "Create a simple Python function that adds two numbers",
        "agents": [
            {
                "id": "coordinator",
                "name": "Coordinator",
                "role": "coordinator",
                "model": "gpt-3.5-turbo" if openai_key else "claude-3-haiku",
                "system_prompt": "You are a coordinator agent. Delegate tasks to other agents.",
                "memory_enabled": True
            },
            {
                "id": "coder",
                "name": "Coder",
                "role": "coder",
                "model": "gpt-3.5-turbo" if openai_key else "claude-3-haiku",
                "system_prompt": "You are a coding agent. Write clean, efficient code.",
                "memory_enabled": True
            }
        ],
        "enable_streaming": False
    }
    
    try:
        response = requests.post(
            f"{ONLINE_SERVICE_URL}/run-workflow",
            headers={"Content-Type": "application/json"},
            json=workflow_request,
            timeout=60  # 60 second timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Workflow execution passed")
            print(f"   Workflow ID: {data['workflow_id']}")
            print(f"   Status: {data['status']}")
            print(f"   Total messages: {data['total_messages']}")
            print(f"   Conversation ID: {data['conversation_id']}")
            return True
        else:
            print(f"❌ Workflow execution failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Workflow execution error: {e}")
        return False

def test_conversations():
    """Test conversation endpoints"""
    print("\n🔍 Testing conversation endpoints...")
    try:
        response = requests.get(f"{ONLINE_SERVICE_URL}/conversations")
        if response.status_code == 200:
            conversations = response.json()
            print(f"✅ Conversations endpoint passed")
            print(f"   Found {len(conversations)} conversations")
            return True
        else:
            print(f"❌ Conversations endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Conversations endpoint error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Online Agent Service")
    print("=" * 50)
    
    # Check if service is running
    try:
        response = requests.get(f"{ONLINE_SERVICE_URL}/", timeout=5)
        print("✅ Online agent service is running")
    except Exception as e:
        print(f"❌ Online agent service is not running: {e}")
        print("   Please start the service with: python online_agent_service.py")
        return
    
    # Run tests
    tests = [
        test_health_check,
        test_models_endpoint,
        test_workflow_execution,
        test_conversations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Online agent service is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n📚 API Documentation available at: http://localhost:8001/docs")

if __name__ == "__main__":
    main()

