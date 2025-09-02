from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

from enhanced_github_agent import EnhancedGitHubAgent

enhanced_github_router = APIRouter(prefix="/github/enhanced", tags=["Enhanced GitHub"])

class GitHubConfigRequest(BaseModel):
    token: str
    username: str
    email: Optional[str] = None

class ExtractAndPushRequest(BaseModel):
    repository_name: str
    commit_message: Optional[str] = None
    auto_create_repo: bool = True

enhanced_agent = None

def get_enhanced_agent():
    global enhanced_agent
    if enhanced_agent is None:
        enhanced_agent = EnhancedGitHubAgent(Path(__file__).parent / "generated")
    return enhanced_agent

@enhanced_github_router.post("/configure")
async def configure_enhanced_github(request: GitHubConfigRequest):
    agent = get_enhanced_agent()
    result = agent.configure_github(token=request.token, username=request.username, email=request.email or "")
    if result["success"]:
        return {"success": True, "message": "GitHub configured", "user": result["user"]}
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@enhanced_github_router.get("/status")
async def get_enhanced_status():
    agent = get_enhanced_agent()
    if not agent.is_configured():
        return {"configured": False, "message": "Not configured"}
    return {"configured": True, "message": "GitHub configured and ready"}

@enhanced_github_router.get("/preview")
async def preview_extractable_code():
    agent = get_enhanced_agent()
    if not agent.is_configured():
        raise HTTPException(status_code=400, detail="GitHub not configured")
    return agent.preview_extractable_code()

@enhanced_github_router.post("/extract-and-push")
async def enhanced_extract_and_push(request: ExtractAndPushRequest):
    agent = get_enhanced_agent()
    if not agent.is_configured():
        raise HTTPException(status_code=400, detail="GitHub not configured")
    
    result = agent.extract_and_push_code(
        repo_name=request.repository_name,
        commit_message=request.commit_message,
        auto_create_repo=request.auto_create_repo
    )
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result["error"])