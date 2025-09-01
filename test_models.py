#!/usr/bin/env python3
"""
Quick test to check available models and fix the gemini-pro-vision issue
"""

import requests
import json

def test_models():
    """Test which models are actually available"""
    try:
        response = requests.get("http://localhost:8001/models", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Available models:")
            models = data.get('available_models', {})
            for model_name, model_info in models.items():
                print(f"   - {model_name}")
            return models
        else:
            print(f"❌ Failed to get models: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Error testing models: {e}")
        return {}

def test_simple_workflow():
    """Test a simple workflow with working models"""
    workflow_request = {
        "task": "Say hello and introduce yourself briefly",
        "agents": [
            {
                "id": "coordinator",
                "name": "Coordinator",
                "role": "coordinator",
                "model": "gemini-pro",  # Use gemini-pro instead of gemini-pro-vision
                "system_prompt": "You are a helpful coordinator agent. Respond briefly and clearly.",
                "memory_enabled": True
            }
        ],
        "enable_streaming": True,
        "conversation_id": None
    }
    
    try:
        print("🔄 Testing simple workflow with gemini-pro...")
        response = requests.post(
            "http://localhost:8001/run-workflow",
            json=workflow_request,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Simple workflow test passed")
            print(f"   Workflow ID: {data.get('workflow_id', 'Unknown')}")
            print(f"   Status: {data.get('status', 'Unknown')}")
            print(f"   Messages: {len(data.get('message_history', []))}")
            
            # Show messages
            messages = data.get('message_history', [])
            for i, msg in enumerate(messages[:3]):  # Show first 3 messages
                print(f"   Message {i+1}: {msg.get('from_agent', 'Unknown')} → {msg.get('to_agent', 'Unknown')}")
                print(f"   Content: {msg.get('content', '')[:100]}...")
            
            return True
        else:
            print(f"❌ Simple workflow test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Simple workflow test error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Available Models")
    print("=" * 40)
    
    models = test_models()
    print()
    
    if models:
        test_simple_workflow()
    else:
        print("⚠️  Cannot test workflow without available models")
