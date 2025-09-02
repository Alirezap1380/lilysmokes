import os
from pathlib import Path
from typing import Dict, Any
import logging

from enhanced_github_service import EnhancedGitHubService, EnhancedGitHubConfig

logger = logging.getLogger(__name__)

class EnhancedGitHubAgent:
    def __init__(self, generated_dir: Path):
        self.generated_dir = generated_dir
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        if os.getenv('GITHUB_TOKEN') and os.getenv('GITHUB_USERNAME'):
            try:
                config = EnhancedGitHubConfig(
                    token=os.getenv('GITHUB_TOKEN'),
                    username=os.getenv('GITHUB_USERNAME'),
                    email=os.getenv('GITHUB_EMAIL', '')
                )
                self.service = EnhancedGitHubService(config, self.generated_dir)
            except Exception as e:
                logger.warning(f"GitHub service init failed: {e}")
    
    def configure_github(self, token: str, username: str, email: str = "") -> Dict[str, Any]:
        try:
            config = EnhancedGitHubConfig(token=token, username=username, email=email)
            self.service = EnhancedGitHubService(config, self.generated_dir)
            return self.service.validate_and_get_user_info()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def is_configured(self) -> bool:
        return self.service is not None
    
    def extract_and_push_code(self, repo_name: str, commit_message: str = None, auto_create_repo: bool = True) -> Dict[str, Any]:
        try:
            if not self.service:
                return {"success": False, "error": "GitHub not configured"}
            
            extraction_result = self.service.extract_and_organize_generated_code()
            if not extraction_result["success"]:
                return extraction_result
            
            files = extraction_result["files"]
            
            if auto_create_repo:
                self.service.create_repository_with_validation(name=repo_name)
            
            return self.service.push_files_to_repository(repo_name=repo_name, files=files, commit_message=commit_message)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def preview_extractable_code(self) -> Dict[str, Any]:
        if not self.service:
            return {"success": False, "error": "GitHub not configured"}