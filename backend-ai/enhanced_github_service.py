import os
import json
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import requests
from pydantic import BaseModel, validator
import logging
import fnmatch

logger = logging.getLogger(__name__)

class EnhancedGitHubConfig(BaseModel):
    token: str
    username: str
    email: Optional[str] = None
    default_branch: str = "main"
    
    @validator('token')
    def validate_token(cls, v):
        if not v or len(v) < 20:
            raise ValueError('Invalid GitHub token format')
        return v
    
    def is_configured(self) -> bool:
        return bool(self.token and self.username)

class EnhancedCodeFile(BaseModel):
    path: str
    content: str
    language: str
    size: int
    encoding: str = "utf-8"

class EnhancedGitHubService:
    def __init__(self, config: EnhancedGitHubConfig, generated_dir: Path):
        self.config = config
        self.generated_dir = generated_dir
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "LilySmokes-AI-Assistant/2.0"
        }
        
        self.language_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.html': 'html', '.css': 'css', '.json': 'json',
            '.md': 'markdown', '.txt': 'text', '.yaml': 'yaml', '.yml': 'yaml'
        }
    
    def validate_and_get_user_info(self) -> Dict[str, Any]:
        try:
            response = requests.get(f"{self.base_url}/user", headers=self.headers)
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "success": True,
                    "user": {
                        "login": user_data.get("login"),
                        "name": user_data.get("name"),
                        "email": user_data.get("email"),
                        "public_repos": user_data.get("public_repos", 0),
                        "private_repos": user_data.get("total_private_repos", 0)
                    }
                }
            else:
                return {"success": False, "error": f"GitHub API error: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def extract_and_organize_generated_code(self) -> Dict[str, Any]:
        try:
            if not self.generated_dir.exists():
                return {"success": False, "error": "Generated directory does not exist"}
            
            files = self._scan_directory()
            if not files:
                return {"success": False, "error": "No files found to extract"}
            
            # Organize files by type
            organized = {"code_files": [], "test_files": [], "documentation": [], "configuration": [], "other": []}
            
            for file in files:
                if file.path.startswith("test_") or "test" in file.path.lower():
                    organized["test_files"].append(file)
                elif file.path.startswith("code_") or file.language == "python":
                    organized["code_files"].append(file)
                elif file.language in ["markdown", "text"]:
                    organized["documentation"].append(file)
                elif file.language in ["json", "yaml"]:
                    organized["configuration"].append(file)
                else:
                    organized["other"].append(file)
            
            # Generate README
            readme_content = self._generate_readme(organized)
            readme_file = EnhancedCodeFile(
                path="README.md", content=readme_content, language="markdown", size=len(readme_content)
            )
            organized["documentation"].append(readme_file)
            
            # Flatten all files
            all_files = []
            for file_list in organized.values():
                all_files.extend(file_list)
            
            return {
                "success": True, "files": all_files, "organization": organized,
                "stats": {
                    "total_files": len(all_files), "code_files": len(organized["code_files"]),
                    "test_files": len(organized["test_files"]), "documentation": len(organized["documentation"]),
                    "total_size": sum(f.size for f in all_files)
                }
            }
            
        except Exception as e:
            logger.error(f"Code extraction error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _scan_directory(self) -> List[EnhancedCodeFile]:
        files = []
        include_patterns = ["*.py", "*.js", "*.ts", "*.html", "*.css", "*.json", "*.md", "*.txt"]
        exclude_patterns = ["__pycache__", "*.log", "*.tmp", ".DS_Store"]
        
        for file_path in self.generated_dir.rglob('*'):
            if not file_path.is_file():
                continue
                
            try:
                relative_path = file_path.relative_to(self.generated_dir)
                if not any(fnmatch.fnmatch(relative_path.name, pattern) for pattern in include_patterns):
                    continue
                if any(fnmatch.fnmatch(str(relative_path), pattern) for pattern in exclude_patterns):
                    continue
                
                content = file_path.read_text(encoding='utf-8')
                extension = file_path.suffix.lower()
                language = self.language_map.get(extension, 'text')
                
                files.append(EnhancedCodeFile(
                    path=str(relative_path), content=content, language=language, size=len(content)
                ))
                
            except Exception as e:
                logger.warning(f"Error reading {file_path}: {str(e)}")
                continue
        
        return files
    
    def _generate_readme(self, organized: Dict) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        readme = f"""# AI Generated Project

Generated by LilySmokes AI Assistant on {timestamp}

## Project Overview
This project contains AI-generated code with comprehensive testing and documentation.

## Files Summary
- **Code Files**: {len(organized.get('code_files', []))}
- **Test Files**: {len(organized.get('test_files', []))}
- **Documentation**: {len(organized.get('documentation', []))}

## Getting Started

### Prerequisites
- Python 3.8+

### Installation
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the main code files

### Testing
```bash
python -m unittest discover -s . -p "test_*.py"