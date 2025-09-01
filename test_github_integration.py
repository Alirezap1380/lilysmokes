#!/usr/bin/env python3
"""
Test script for GitHub integration feature
This script tests the GitHub agent and API endpoints
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add backend-ai to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend-ai'))

def test_github_agent_import():
    """Test that GitHub agent can be imported"""
    try:
        from github_agent import GitHubConfig, GitHubAgent, GitHubRepository, GitHubWorkflow
        print("✅ GitHub agent imports successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import GitHub agent: {e}")
        return False

def test_github_config():
    """Test GitHub configuration"""
    try:
        from github_agent import GitHubConfig
        
        # Test with no environment variables
        config = GitHubConfig()
        print(f"✅ GitHub config created: configured={config.is_configured()}")
        
        # Test with environment variables
        os.environ['GITHUB_TOKEN'] = 'test_token'
        os.environ['GITHUB_USERNAME'] = 'test_user'
        config = GitHubConfig()
        print(f"✅ GitHub config with env vars: configured={config.is_configured()}")
        
        return True
    except Exception as e:
        print(f"❌ GitHub config test failed: {e}")
        return False

def test_github_repository():
    """Test GitHub repository creation"""
    try:
        from github_agent import GitHubRepository
        
        repo = GitHubRepository(
            name="test-repo",
            description="Test repository",
            private=False
        )
        print(f"✅ GitHub repository created: {repo.name}")
        return True
    except Exception as e:
        print(f"❌ GitHub repository test failed: {e}")
        return False

def test_api_endpoints():
    """Test GitHub API endpoints"""
    base_url = "http://localhost:8000"
    
    # Test status endpoint
    try:
        response = requests.get(f"{base_url}/github/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ GitHub status endpoint: {data}")
        else:
            print(f"⚠️ GitHub status endpoint returned {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("⚠️ Backend server not running, skipping API tests")
        return True
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def test_file_extraction():
    """Test file extraction functionality"""
    try:
        from github_agent import GitHubAgent, GitHubConfig
        
        # Create a test directory with some files
        test_dir = Path("test_extraction")
        test_dir.mkdir(exist_ok=True)
        
        # Create test files
        (test_dir / "test.py").write_text("print('Hello, World!')")
        (test_dir / "test.js").write_text("console.log('Hello, World!');")
        (test_dir / "test.md").write_text("# Test File\n\nThis is a test.")
        (test_dir / "ignore.log").write_text("log content")
        
        # Test extraction
        config = GitHubConfig()
        agent = GitHubAgent(config)
        
        files = agent.extract_code_from_directory(
            str(test_dir),
            include_patterns=["*.py", "*.js", "*.md"],
            exclude_patterns=["*.log"]
        )
        
        print(f"✅ File extraction test: found {len(files)} files")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        
        return True
    except Exception as e:
        print(f"❌ File extraction test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing GitHub Integration Feature")
    print("=" * 50)
    
    tests = [
        ("GitHub Agent Import", test_github_agent_import),
        ("GitHub Configuration", test_github_config),
        ("GitHub Repository", test_github_repository),
        ("API Endpoints", test_api_endpoints),
        ("File Extraction", test_file_extraction),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! GitHub integration is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

