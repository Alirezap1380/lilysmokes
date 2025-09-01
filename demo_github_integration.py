#!/usr/bin/env python3
"""
Demo script to showcase GitHub Integration functionality
This script demonstrates the GitHub API endpoints working
"""

import requests
import json
import time

# Base URL for the GitHub integration server
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data['status']}")
            print(f"   Service: {data['service']}")
            print(f"   Timestamp: {data['timestamp']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_github_status():
    """Test the GitHub status endpoint"""
    print("\n🔍 Testing GitHub Status...")
    try:
        response = requests.get(f"{BASE_URL}/github/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ GitHub Status: {data['configured']}")
            print(f"   Message: {data['message']}")
        else:
            print(f"❌ GitHub status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ GitHub status error: {e}")

def test_github_configure():
    """Test GitHub configuration (this will fail without a real token)"""
    print("\n🔍 Testing GitHub Configuration...")
    try:
        # This will fail because we don't have a real GitHub token
        response = requests.post(f"{BASE_URL}/github/configure", json={
            "token": "test_token",
            "username": "test_user"
        })
        if response.status_code == 400:
            data = response.json()
            print(f"✅ Configuration validation working: {data['detail']}")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Configuration test error: {e}")

def test_github_repositories():
    """Test GitHub repositories endpoint (will fail without configuration)"""
    print("\n🔍 Testing GitHub Repositories...")
    try:
        response = requests.get(f"{BASE_URL}/github/repositories")
        if response.status_code == 400:
            data = response.json()
            print(f"✅ Repository endpoint working: {data['detail']}")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Repository test error: {e}")

def test_github_extract():
    """Test GitHub extract endpoint (will fail without configuration)"""
    print("\n🔍 Testing GitHub Extract and Push...")
    try:
        response = requests.post(f"{BASE_URL}/github/extract-and-push", json={
            "source_dir": "./test",
            "repo_name": "test-repo",
            "description": "Test repository",
            "private": False
        })
        if response.status_code == 400:
            data = response.json()
            print(f"✅ Extract endpoint working: {data['detail']}")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Extract test error: {e}")

def show_api_documentation():
    """Show available API endpoints"""
    print("\n📚 Available GitHub Integration API Endpoints:")
    print("=" * 60)
    print("🔗 Health Check: GET /health")
    print("🐙 GitHub Status: GET /github/status")
    print("⚙️  Configure GitHub: POST /github/configure")
    print("📁 Create Repository: POST /github/repositories")
    print("📋 List Repositories: GET /github/repositories")
    print("🔍 Get Repository: GET /github/repositories/{name}")
    print("🚀 Extract & Push: POST /github/extract-and-push")
    print("📝 Update Repository: POST /github/update-repository")
    print("🗑️  Delete Repository: DELETE /github/repositories/{name}")
    print("\n🌐 Interactive API Documentation: http://localhost:8000/docs")

def main():
    """Run all tests"""
    print("🚀 GitHub Integration Demo")
    print("=" * 40)
    print(f"Testing server at: {BASE_URL}")
    
    # Test all endpoints
    test_health()
    test_github_status()
    test_github_configure()
    test_github_repositories()
    test_github_extract()
    
    # Show API documentation
    show_api_documentation()
    
    print("\n" + "=" * 40)
    print("🎉 Demo completed!")
    print("\n💡 To use the GitHub integration:")
    print("1. Get a GitHub Personal Access Token")
    print("2. Configure it using POST /github/configure")
    print("3. Start extracting and pushing code!")
    print("\n🌐 View full API docs at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()

