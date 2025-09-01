#!/usr/bin/env python3
"""
Simplified GitHub Integration Server
This server provides only the GitHub integration functionality
without the complex AI agent dependencies.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import GitHub components
from github_agent import GitHubAgent, GitHubConfig, GitHubRepository, GitHubWorkflow, validate_github_token, get_github_user_info

# Create FastAPI app
app = FastAPI(
    title="GitHub Integration Server",
    description="Server for GitHub integration functionality",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for GitHub requests
class GitHubConfigRequest(BaseModel):
    token: str
    username: str

class GitHubRepositoryRequest(BaseModel):
    name: str
    description: str = ""
    private: bool = False
    auto_init: bool = True
    gitignore_template: str = "Python"

class GitHubExtractRequest(BaseModel):
    source_dir: str
    repo_name: str
    description: str = ""
    private: bool = False
    include_patterns: List[str] = None
    exclude_patterns: List[str] = None

class GitHubUpdateRequest(BaseModel):
    repo_name: str
    source_dir: str
    include_patterns: List[str] = None
    exclude_patterns: List[str] = None

# Initialize GitHub components
github_config = GitHubConfig()
github_agent_instance = GitHubAgent(github_config) if github_config.is_configured() else None
github_workflow = GitHubWorkflow(github_agent_instance) if github_agent_instance else None

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "GitHub Integration Server"
    }

@app.post("/github/configure")
async def configure_github(request: GitHubConfigRequest):
    """Configure GitHub integration with token and username"""
    try:
        # Validate the token
        if not validate_github_token(request.token):
            raise HTTPException(status_code=400, detail="Invalid GitHub token")
        
        # Get user info
        user_info = get_github_user_info(request.token)
        if not user_info["success"]:
            raise HTTPException(status_code=400, detail="Failed to validate GitHub user")
        
        # Update global configuration
        global github_config, github_agent_instance, github_workflow
        github_config = GitHubConfig(token=request.token, username=request.username)
        github_agent_instance = GitHubAgent(github_config)
        github_workflow = GitHubWorkflow(github_agent_instance)
        
        return {
            "success": True,
            "message": "GitHub configured successfully",
            "user": user_info["user"]["login"],
            "username": request.username
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure GitHub: {str(e)}")

@app.get("/github/status")
async def get_github_status():
    """Get GitHub integration status"""
    try:
        if not github_config.is_configured():
            return {
                "configured": False,
                "message": "GitHub not configured. Use /github/configure to set up."
            }
        
        # Test connection
        user_info = get_github_user_info(github_config.token)
        if user_info["success"]:
            return {
                "configured": True,
                "username": github_config.username,
                "user": user_info["user"]["login"],
                "message": "GitHub integration is active"
            }
        else:
            return {
                "configured": False,
                "message": "GitHub token is invalid or expired"
            }
    except Exception as e:
        return {
            "configured": False,
            "error": str(e)
        }

@app.post("/github/repositories")
async def create_github_repository(request: GitHubRepositoryRequest):
    """Create a new GitHub repository"""
    try:
        if not github_agent_instance:
            raise HTTPException(status_code=400, detail="GitHub not configured")
        
        repo = GitHubRepository(
            name=request.name,
            description=request.description,
            private=request.private,
            auto_init=request.auto_init,
            gitignore_template=request.gitignore_template
        )
        
        result = github_agent_instance.create_repository(repo)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create repository: {str(e)}")

@app.get("/github/repositories")
async def list_github_repositories():
    """List all GitHub repositories for the authenticated user"""
    try:
        if not github_agent_instance:
            raise HTTPException(status_code=400, detail="GitHub not configured")
        
        result = github_agent_instance.list_user_repositories()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list repositories: {str(e)}")

@app.get("/github/repositories/{repo_name}")
async def get_github_repository(repo_name: str):
    """Get information about a specific GitHub repository"""
    try:
        if not github_agent_instance:
            raise HTTPException(status_code=400, detail="GitHub not configured")
        
        result = github_agent_instance.get_repository_info(repo_name)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get repository: {str(e)}")

@app.post("/github/extract-and-push")
async def extract_and_push_to_github(request: GitHubExtractRequest):
    """Extract code from a directory and push to a new GitHub repository"""
    try:
        if not github_workflow:
            raise HTTPException(status_code=400, detail="GitHub not configured")
        
        # Set default patterns if not provided
        if request.include_patterns is None:
            request.include_patterns = ["*.py", "*.js", "*.ts", "*.tsx", "*.jsx", "*.html", "*.css", "*.json", "*.md", "*.txt"]
        
        if request.exclude_patterns is None:
            request.exclude_patterns = ["__pycache__", "*.log", "*.tmp", ".DS_Store", "node_modules", ".git"]
        
        result = github_workflow.extract_and_push_project(
            source_dir=request.source_dir,
            repo_name=request.repo_name,
            description=request.description,
            private=request.private,
            include_patterns=request.include_patterns,
            exclude_patterns=request.exclude_patterns
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract and push: {str(e)}")

@app.post("/github/update-repository")
async def update_github_repository(request: GitHubUpdateRequest):
    """Update an existing GitHub repository with new code"""
    try:
        if not github_workflow:
            raise HTTPException(status_code=400, detail="GitHub not configured")
        
        # Set default patterns if not provided
        if request.include_patterns is None:
            request.include_patterns = ["*.py", "*.js", "*.ts", "*.tsx", "*.jsx", "*.html", "*.css", "*.json", "*.md", "*.txt"]
        
        if request.exclude_patterns is None:
            request.exclude_patterns = ["__pycache__", "*.log", "*.tmp", ".DS_Store", "node_modules", ".git"]
        
        result = github_workflow.update_existing_repository(
            repo_name=request.repo_name,
            source_dir=request.source_dir,
            include_patterns=request.include_patterns,
            exclude_patterns=request.exclude_patterns
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update repository: {str(e)}")

@app.delete("/github/repositories/{repo_name}")
async def delete_github_repository(repo_name: str):
    """Delete a GitHub repository (use with caution!)"""
    try:
        if not github_agent_instance:
            raise HTTPException(status_code=400, detail="GitHub not configured")
        
        result = github_agent_instance.delete_repository(repo_name)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete repository: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting GitHub Integration Server...")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔗 Health Check: http://localhost:8000/health")
    print("🐙 GitHub Status: http://localhost:8000/github/status")
    uvicorn.run(app, host="0.0.0.0", port=8000)
