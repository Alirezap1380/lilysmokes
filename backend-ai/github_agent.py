# =============================================================================
# GITHUB AGENT - CODE EXTRACTION AND REPOSITORY MANAGEMENT
# =============================================================================
"""
GitHub Agent for code extraction and repository management
Features:
- Extract generated code from the system
- Create new GitHub repositories
- Push code to existing repositories
- Manage repository settings
- Handle authentication and permissions
"""

import os
import json
import base64
import requests
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from abc import ABC, abstractmethod

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"

class GitHubConfig:
    """Configuration for GitHub integration"""
    
    def __init__(self, token: str = None, username: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.username = username or os.getenv("GITHUB_USERNAME")
        self.headers = {
            "Authorization": f"token {self.token}" if self.token else None,
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Cube-AI-System"
        }
    
    def is_configured(self) -> bool:
        """Check if GitHub is properly configured"""
        return bool(self.token and self.username)
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        return {k: v for k, v in self.headers.items() if v is not None}

class GitHubRepository:
    """Represents a GitHub repository"""
    
    def __init__(self, name: str, description: str = "", private: bool = False, 
                 auto_init: bool = True, gitignore_template: str = "Python"):
        self.name = name
        self.description = description
        self.private = private
        self.auto_init = auto_init
        self.gitignore_template = gitignore_template
        self.created_at = None
        self.html_url = None
        self.clone_url = None
        self.ssh_url = None

class GitHubFile:
    """Represents a file to be committed to GitHub"""
    
    def __init__(self, path: str, content: str, message: str = "Add file"):
        self.path = path
        self.content = content
        self.message = message
        self.sha = None  # For updates

class GitHubAgent:
    """
    GitHub Agent for managing code extraction and repository operations
    """
    
    def __init__(self, config: GitHubConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def extract_code_from_directory(self, source_dir: str, include_patterns: List[str] = None, 
                                  exclude_patterns: List[str] = None) -> List[GitHubFile]:
        """
        Extract code files from a directory
        
        Args:
            source_dir: Source directory to extract from
            include_patterns: File patterns to include (e.g., ["*.py", "*.js"])
            exclude_patterns: File patterns to exclude (e.g., ["__pycache__", "*.log"])
            
        Returns:
            List of GitHubFile objects
        """
        files = []
        source_path = Path(source_dir)
        
        if not source_path.exists():
            raise ValueError(f"Source directory does not exist: {source_dir}")
        
        # Default patterns
        if include_patterns is None:
            include_patterns = ["*.py", "*.js", "*.ts", "*.tsx", "*.jsx", "*.html", "*.css", "*.json", "*.md", "*.txt"]
        
        if exclude_patterns is None:
            exclude_patterns = ["__pycache__", "*.log", "*.tmp", ".DS_Store", "node_modules", ".git"]
        
        # Walk through directory
        for file_path in source_path.rglob("*"):
            if file_path.is_file():
                # Check if file should be included
                should_include = any(file_path.match(pattern) for pattern in include_patterns)
                should_exclude = any(file_path.match(pattern) for pattern in exclude_patterns)
                
                if should_include and not should_exclude:
                    try:
                        # Read file content
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Create relative path
                        relative_path = str(file_path.relative_to(source_path))
                        
                        # Create GitHub file
                        github_file = GitHubFile(
                            path=relative_path,
                            content=content,
                            message=f"Add {relative_path}"
                        )
                        files.append(github_file)
                        
                    except Exception as e:
                        self.logger.warning(f"Could not read file {file_path}: {e}")
        
        return files
    
    def create_repository(self, repo: GitHubRepository) -> Dict[str, Any]:
        """
        Create a new GitHub repository
        
        Args:
            repo: GitHubRepository object with repository details
            
        Returns:
            Repository creation response
        """
        if not self.config.is_configured():
            raise ValueError("GitHub not configured. Please set GITHUB_TOKEN and GITHUB_USERNAME")
        
        url = f"{GITHUB_API_BASE}/user/repos"
        data = {
            "name": repo.name,
            "description": repo.description,
            "private": repo.private,
            "auto_init": repo.auto_init,
            "gitignore_template": repo.gitignore_template
        }
        
        response = requests.post(url, headers=self.config.get_auth_headers(), json=data)
        
        if response.status_code == 201:
            repo_data = response.json()
            repo.created_at = repo_data.get("created_at")
            repo.html_url = repo_data.get("html_url")
            repo.clone_url = repo_data.get("clone_url")
            repo.ssh_url = repo_data.get("ssh_url")
            
            return {
                "success": True,
                "repository": repo_data,
                "message": f"Repository '{repo.name}' created successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to create repository: {response.text}",
                "status_code": response.status_code
            }
    
    def push_files_to_repository(self, repo_name: str, files: List[GitHubFile], 
                                branch: str = "main") -> Dict[str, Any]:
        """
        Push files to a GitHub repository
        
        Args:
            repo_name: Name of the repository (with username if needed)
            files: List of GitHubFile objects to push
            branch: Target branch name
            
        Returns:
            Push operation result
        """
        if not self.config.is_configured():
            raise ValueError("GitHub not configured. Please set GITHUB_TOKEN and GITHUB_USERNAME")
        
        # Ensure repo_name includes username if not already present
        if "/" not in repo_name:
            repo_name = f"{self.config.username}/{repo_name}"
        
        results = []
        
        for file in files:
            try:
                # Encode content
                content_bytes = file.content.encode('utf-8')
                content_b64 = base64.b64encode(content_bytes).decode('utf-8')
                
                # Prepare request data
                data = {
                    "message": file.message,
                    "content": content_b64,
                    "branch": branch
                }
                
                # If updating existing file, include SHA
                if file.sha:
                    data["sha"] = file.sha
                
                url = f"{GITHUB_API_BASE}/repos/{repo_name}/contents/{file.path}"
                response = requests.put(url, headers=self.config.get_auth_headers(), json=data)
                
                if response.status_code in [201, 200]:
                    file_data = response.json()
                    results.append({
                        "file": file.path,
                        "success": True,
                        "sha": file_data.get("content", {}).get("sha"),
                        "message": f"File '{file.path}' pushed successfully"
                    })
                else:
                    results.append({
                        "file": file.path,
                        "success": False,
                        "error": response.text,
                        "status_code": response.status_code
                    })
                    
            except Exception as e:
                results.append({
                    "file": file.path,
                    "success": False,
                    "error": str(e)
                })
        
        # Summary
        successful = sum(1 for r in results if r["success"])
        total = len(results)
        
        return {
            "success": successful == total,
            "total_files": total,
            "successful_files": successful,
            "failed_files": total - successful,
            "results": results,
            "message": f"Pushed {successful}/{total} files successfully"
        }
    
    def get_repository_info(self, repo_name: str) -> Dict[str, Any]:
        """
        Get information about a repository
        
        Args:
            repo_name: Name of the repository (with username if needed)
            
        Returns:
            Repository information
        """
        if not self.config.is_configured():
            raise ValueError("GitHub not configured. Please set GITHUB_TOKEN and GITHUB_USERNAME")
        
        if "/" not in repo_name:
            repo_name = f"{self.config.username}/{repo_name}"
        
        url = f"{GITHUB_API_BASE}/repos/{repo_name}"
        response = requests.get(url, headers=self.config.get_auth_headers())
        
        if response.status_code == 200:
            return {
                "success": True,
                "repository": response.json()
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }
    
    def list_user_repositories(self) -> Dict[str, Any]:
        """
        List all repositories for the authenticated user
        
        Returns:
            List of repositories
        """
        if not self.config.is_configured():
            raise ValueError("GitHub not configured. Please set GITHUB_TOKEN and GITHUB_USERNAME")
        
        url = f"{GITHUB_API_BASE}/user/repos"
        response = requests.get(url, headers=self.config.get_auth_headers())
        
        if response.status_code == 200:
            return {
                "success": True,
                "repositories": response.json()
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }
    
    def delete_repository(self, repo_name: str) -> Dict[str, Any]:
        """
        Delete a repository (use with caution!)
        
        Args:
            repo_name: Name of the repository (with username if needed)
            
        Returns:
            Deletion result
        """
        if not self.config.is_configured():
            raise ValueError("GitHub not configured. Please set GITHUB_TOKEN and GITHUB_USERNAME")
        
        if "/" not in repo_name:
            repo_name = f"{self.config.username}/{repo_name}"
        
        url = f"{GITHUB_API_BASE}/repos/{repo_name}"
        response = requests.delete(url, headers=self.config.get_auth_headers())
        
        if response.status_code == 204:
            return {
                "success": True,
                "message": f"Repository '{repo_name}' deleted successfully"
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }

class GitHubWorkflow:
    """
    Workflow for extracting and pushing code to GitHub
    """
    
    def __init__(self, github_agent: GitHubAgent):
        self.github_agent = github_agent
        self.logger = logging.getLogger(__name__)
    
    def extract_and_push_project(self, source_dir: str, repo_name: str, 
                                description: str = "", private: bool = False,
                                include_patterns: List[str] = None,
                                exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """
        Complete workflow: extract code and push to new repository
        
        Args:
            source_dir: Source directory to extract from
            repo_name: Name for the new repository
            description: Repository description
            private: Whether repository should be private
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            
        Returns:
            Complete workflow result
        """
        try:
            # Step 1: Extract files
            self.logger.info(f"Extracting files from {source_dir}")
            files = self.github_agent.extract_code_from_directory(
                source_dir, include_patterns, exclude_patterns
            )
            
            if not files:
                return {
                    "success": False,
                    "error": "No files found to extract"
                }
            
            # Step 2: Create repository
            self.logger.info(f"Creating repository: {repo_name}")
            repo = GitHubRepository(
                name=repo_name,
                description=description,
                private=private
            )
            
            create_result = self.github_agent.create_repository(repo)
            if not create_result["success"]:
                return create_result
            
            # Step 3: Push files
            self.logger.info(f"Pushing {len(files)} files to repository")
            push_result = self.github_agent.push_files_to_repository(repo_name, files)
            
            return {
                "success": push_result["success"],
                "repository": create_result["repository"],
                "files_pushed": push_result,
                "message": f"Project extracted and pushed to {repo_name}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_existing_repository(self, repo_name: str, source_dir: str,
                                  include_patterns: List[str] = None,
                                  exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """
        Update an existing repository with new code
        
        Args:
            repo_name: Name of the existing repository
            source_dir: Source directory to extract from
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            
        Returns:
            Update result
        """
        try:
            # Extract files
            files = self.github_agent.extract_code_from_directory(
                source_dir, include_patterns, exclude_patterns
            )
            
            if not files:
                return {
                    "success": False,
                    "error": "No files found to extract"
                }
            
            # Push to existing repository
            push_result = self.github_agent.push_files_to_repository(repo_name, files)
            
            return {
                "success": push_result["success"],
                "files_pushed": push_result,
                "message": f"Repository {repo_name} updated with {len(files)} files"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_github_config_from_env() -> GitHubConfig:
    """Create GitHub configuration from environment variables"""
    return GitHubConfig()

def validate_github_token(token: str) -> bool:
    """Validate GitHub token by making a test API call"""
    config = GitHubConfig(token=token)
    if not config.token:
        return False
    
    response = requests.get(f"{GITHUB_API_BASE}/user", headers=config.get_auth_headers())
    return response.status_code == 200

def get_github_user_info(token: str) -> Dict[str, Any]:
    """Get GitHub user information"""
    config = GitHubConfig(token=token)
    if not config.token:
        return {"success": False, "error": "No token provided"}
    
    response = requests.get(f"{GITHUB_API_BASE}/user", headers=config.get_auth_headers())
    if response.status_code == 200:
        return {"success": True, "user": response.json()}
    else:
        return {"success": False, "error": response.text}

