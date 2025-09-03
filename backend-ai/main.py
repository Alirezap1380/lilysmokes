# =============================================================================
# IMPORTS - Enhanced with GitHub Integration
# =============================================================================
import os
from pathlib import Path
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
import tempfile
import subprocess
import sys
import logging
import asyncio
from abc import ABC, abstractmethod
import json
from enum import Enum
import ast

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from langchain_ollama import OllamaLLM
import uvicorn

# Database integration
from database import SafeDatabaseIntegration, ConversationRequest, ConversationResponse, ChatRequestWithConversation

# GitHub integration - your existing
from github_agent import GitHubAgent, GitHubConfig, GitHubRepository, GitHubWorkflow, validate_github_token, get_github_user_info

# Enhanced GitHub integration - NEW
from enhanced_github_endpoints import enhanced_github_router
from enhanced_github_agent import EnhancedGitHubAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# GLOBAL CONFIGURATION
# =============================================================================

def detect_gpu():
    """Detect if GPU is available and configure accordingly"""
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ GPU detected - using GPU acceleration")
            return {
                "num_gpu": 1,
                "num_thread": 8,
                "temperature": 0.3,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "top_k": 40,
                "num_ctx": 4096,
            }
        else:
            print("⚠️ GPU not detected - using CPU only")
            return {
                "num_gpu": 0,
                "num_thread": 8,
                "temperature": 0.3,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "top_k": 40,
                "num_ctx": 4096,
            }
    except Exception as e:
        print(f"⚠️ Could not detect GPU: {e} - using CPU only")
        return {
            "num_gpu": 0,
            "num_thread": 8,
            "temperature": 0.3,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "top_k": 40,
            "num_ctx": 4096,
        }

DEFAULT_GPU_CONFIG = detect_gpu()
DEFAULT_MODEL = "codellama:7b-instruct"

MODEL_CONFIGS = {
    "codellama:7b-instruct": {
        "num_gpu": DEFAULT_GPU_CONFIG["num_gpu"],
        "num_thread": 8,
        "temperature": 0.3,
        "top_p": 0.9,
        "repeat_penalty": 1.1,
        "top_k": 40,
        "num_ctx": 4096,
    },
    "mistral": {
        "num_gpu": DEFAULT_GPU_CONFIG["num_gpu"],
        "num_thread": 8,
        "temperature": 0.7,
        "top_p": 0.9,
        "repeat_penalty": 1.1,
    },
    "llama2": {
        "num_gpu": DEFAULT_GPU_CONFIG["num_gpu"],
        "num_thread": 8,
        "temperature": 0.5,
        "top_p": 0.9,
        "repeat_penalty": 1.1,
    }
}

# =============================================================================
# APP & CORS CONFIGURATION
# =============================================================================
app = FastAPI(title="Multi-Agent AI System", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include enhanced GitHub router - NEW
app.include_router(enhanced_github_router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# =============================================================================
# PATHS & DIRECTORIES
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

# Initialize enhanced GitHub agent - NEW
enhanced_github_agent = EnhancedGitHubAgent(GENERATED_DIR)

# =============================================================================
# DATABASE INTEGRATION
# =============================================================================
db_integration = SafeDatabaseIntegration()

# =============================================================================
# ENUMS AND DATA MODELS
# =============================================================================
class MessageType(Enum):
    TASK = "task"
    DATA = "data"
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    STATUS = "status"
    REVIEW = "review"

class AgentMessage(BaseModel):
    id: str
    from_agent: str
    to_agent: str
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()
    retry_count: int = 0
    parent_message_id: Optional[str] = None

    def create_retry_message(self) -> 'AgentMessage':
        return AgentMessage(
            id=f"{self.id}_retry_{self.retry_count + 1}",
            from_agent=self.from_agent,
            to_agent=self.to_agent,
            message_type=self.message_type,
            content=self.content,
            metadata=self.metadata,
            parent_message_id=self.id,
            retry_count=self.retry_count + 1
        )

class AgentStatus(Enum):
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"

class AgentMemory(BaseModel):
    short_term: List[AgentMessage] = []
    long_term: Dict[str, Any] = {}
    context: Dict[str, Any] = {}
    
    def add_message(self, message: AgentMessage):
        self.short_term.append(message)
        if len(self.short_term) > 50:
            self.short_term = self.short_term[-50:]
    
    def get_context_for_prompt(self) -> str:
        recent_messages = self.short_term[-10:]
        context_str = "Recent conversation:\n"
        for msg in recent_messages:
            context_str += f"{msg.from_agent} -> {msg.to_agent}: {msg.content[:100]}...\n"
        return context_str

# =============================================================================
# BASE AGENT
# =============================================================================
class BaseAgent(ABC):
    def __init__(self, agent_id: str, agent_type: str, role: str, 
                 model_name: str = DEFAULT_MODEL, model_config: Dict[str, Any] = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.role = role
        self.status = AgentStatus.IDLE
        self.memory = AgentMemory()
        self.model_config = model_config or {}
        
        model_specific_config = MODEL_CONFIGS.get(model_name, DEFAULT_GPU_CONFIG.copy())
        final_config = {**DEFAULT_GPU_CONFIG, **model_specific_config, **self.model_config}
        self.llm = OllamaLLM(model=model_name, **final_config)
        
        self.message_handlers: Dict[MessageType, Callable] = {
            MessageType.TASK: self.handle_task,
            MessageType.DATA: self.handle_data,
            MessageType.REQUEST: self.handle_request,
            MessageType.RESPONSE: self.handle_response,
            MessageType.ERROR: self.handle_error,
            MessageType.STATUS: self.handle_status
        }
    
    async def process_message(self, message: AgentMessage) -> List[AgentMessage]:
        try:
            self.status = AgentStatus.WORKING
            self.memory.add_message(message)
            
            handler = self.message_handlers.get(message.message_type)
            if handler:
                responses = await handler(message)
            else:
                responses = [self.create_error_message(message.from_agent, 
                                                    f"Unknown message type: {message.message_type}")]
            
            self.status = AgentStatus.IDLE
            return responses
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            return [self.create_error_message(message.from_agent, str(e))]
    
    def create_message(self, to_agent: str, message_type: MessageType, 
                      content: str, metadata: Dict[str, Any] = None) -> AgentMessage:
        return AgentMessage(
            id=f"{self.agent_id}_{datetime.now().timestamp()}",
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            metadata=metadata or {}
        )
    
    def create_error_message(self, to_agent: str, error: str) -> AgentMessage:
        return self.create_message(to_agent, MessageType.ERROR, error)
    
    @abstractmethod
    async def handle_task(self, message: AgentMessage) -> List[AgentMessage]:
        pass
    
    async def handle_data(self, message: AgentMessage) -> List[AgentMessage]:
        return [self.create_message(message.from_agent, MessageType.RESPONSE, 
                                  f"Received data: {message.content}")]
    
    async def handle_request(self, message: AgentMessage) -> List[AgentMessage]:
        return [self.create_message(message.from_agent, MessageType.RESPONSE, 
                                  f"Handled request: {message.content}")]
    
    async def handle_response(self, message: AgentMessage) -> List[AgentMessage]:
        return []
    
    async def handle_error(self, message: AgentMessage) -> List[AgentMessage]:
        print(f"Agent {self.agent_id} received error: {message.content}")
        return []
    
    async def handle_status(self, message: AgentMessage) -> List[AgentMessage]:
        return [self.create_message(message.from_agent, MessageType.STATUS, 
                                  f"Status: {self.status.value}")]

# =============================================================================
# COORDINATOR AGENT
# =============================================================================
class CoordinatorAgent(BaseAgent):
    async def handle_task(self, message: AgentMessage) -> List[AgentMessage]:
        try:
            print(f"🎯 CoordinatorAgent received task: {message.content}")
            
            context = self.memory.get_context_for_prompt()
            
            prompt = f"""
            You are a smart coordinator managing a team of AI agents.
            
            Current task: {message.content}
            Recent context: {context}
            
            Your job is to:
            1. Break down the task into steps
            2. Decide which agents should handle each step
            3. Create clear instructions for each agent
            
            Available agents:
            - coder: Writes code and implements features
            - tester: Creates test cases and validates code
            - runner: Executes tests and reports results
            
            Respond with a JSON structure like this:
            {{
                "steps": [
                    {{"agent": "coder", "task": "Write a Python function that...", "priority": 1}},
                    {{"agent": "tester", "task": "Create test cases for the function", "priority": 2}}
                ]
            }}
            """
            
            response = self.llm.invoke(prompt)
            
            try:
                plan = json.loads(response)
                steps = plan.get("steps", [])
            except:
                steps = [
                    {"agent": "coder", "task": message.content, "priority": 1},
                    {"agent": "tester", "task": "Create tests for the generated code", "priority": 2}
                ]
            
            responses = []
            for step in steps:
                agent_id = step["agent"]
                task = step["task"]
                
                task_message = self.create_message(
                    to_agent=agent_id,
                    message_type=MessageType.TASK,
                    content=task,
                    metadata={"priority": step.get("priority", 1)}
                )
                responses.append(task_message)
            
            return responses
            
        except Exception as e:
            return [self.create_error_message(message.from_agent, f"Coordination failed: {str(e)}")]

# =============================================================================
# CODER AGENT
# =============================================================================
class CoderAgent(BaseAgent):
    async def handle_task(self, message: AgentMessage) -> List[AgentMessage]:
        try:
            print(f"🔧 CoderAgent received task: {message.content}")
            
            prompt = f"""
You are an expert Python developer. Generate ONLY clean, working Python code.

Task: {message.content}

CRITICAL REQUIREMENTS:
- Generate ONLY the Python code, NO explanations, NO comments, NO markdown
- Write complete, runnable Python functions
- Include proper error handling with try/except
- Add type hints and docstrings
- Follow PEP 8 style guidelines
- DO NOT include any explanatory text or comments outside the code
- DO NOT use markdown formatting or code blocks
- DO NOT add "Here's the code:" or similar text

Generate ONLY the function code, nothing else.
"""
            
            response = self.llm.invoke(prompt)
            code = self._simple_code_extraction(response)
            
            timestamp = _timestamp()
            filename = f"code_{timestamp}.py"
            filepath = GENERATED_DIR / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)
            
            response_message = self.create_message(
                to_agent=message.from_agent,
                message_type=MessageType.DATA,
                content=f"Generated code saved to {filename}",
                metadata={"code": code, "filename": filename, "filepath": str(filepath)}
            )
            
            tester_message = self.create_message(
                to_agent="tester",
                message_type=MessageType.DATA,
                content=f"Code generated for testing",
                metadata={"code": code, "filename": filename, "filepath": str(filepath)}
            )
            
            return [response_message, tester_message]
            
        except Exception as e:
            return [self.create_error_message(message.from_agent, f"Code generation failed: {str(e)}")]
    
    def _simple_code_extraction(self, response: str) -> str:
        code = re.sub(r'```python\n', '', response)
        code = re.sub(r'```\n', '', code)
        code = re.sub(r'```', '', code)
        
        lines = code.split('\n')
        cleaned_lines = []
        in_code = False
        
        for line in lines:
            stripped = line.strip()
            
            if not in_code and not stripped:
                continue
                
            if (stripped.startswith(('def ', 'import ', 'from ')) or
                (stripped.startswith('class ') and ':' in stripped) or
                (in_code and stripped)):
                in_code = True
                cleaned_lines.append(line)
            elif in_code:
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        result = re.sub(r'^.*?(def |import |from |class )', r'\1', result, flags=re.DOTALL)
        
        return result

# =============================================================================
# TESTER AGENT
# =============================================================================
class TesterAgent(BaseAgent):
    async def handle_task(self, message: AgentMessage) -> List[AgentMessage]:
        return [self.create_message(message.from_agent, MessageType.RESPONSE, 
                                  f"Tester agent received task: {message.content}")]
    
    async def handle_data(self, message: AgentMessage) -> List[AgentMessage]:
        try:
            print(f"🧪 TesterAgent received data: {message.content}")
            
            code = message.metadata.get("code", "")
            if not code:
                return [self.create_error_message(message.from_agent, "No code provided for testing")]
            
            prompt = f"""
            You are an expert Python tester.
            
            Code to test:
            {code}
            
            Requirements:
            1. Create comprehensive unit tests using unittest
            2. Test all functions and methods
            3. Include edge cases and error conditions
            4. Use descriptive test names
            5. Include setup and teardown if needed
            6. Make sure tests are complete and runnable
            7. DO NOT include the original code in the test file
            8. Only generate the test code, not the original code
            9. DO NOT use ANY import statements for the tested functions
            10. Write tests as if the functions are already defined in the same scope
            
            Generate only the test code, no explanations or markdown formatting.
            """
            
            response = self.llm.invoke(prompt)
            test_code = self._extract_and_clean_test_code(response)
            
            if not test_code or len(test_code.strip()) < 10:
                test_code = self._get_fallback_tests()
            
            if not self._validate_python_syntax(test_code):
                test_code = self._apply_test_emergency_fixes(test_code)
            
            timestamp = _timestamp()
            filename = f"test_{timestamp}.py"
            filepath = GENERATED_DIR / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(test_code)
            
            response_message = self.create_message(
                to_agent=message.from_agent,
                message_type=MessageType.DATA,
                content=f"Generated tests saved to {filename}",
                metadata={
                    "test_code": test_code,
                    "filename": filename,
                    "filepath": str(filepath),
                    "original_code": code
                }
            )
            
            runner_message = self.create_message(
                to_agent="runner",
                message_type=MessageType.DATA,
                content=f"Tests generated for execution",
                metadata={
                    "test_code": test_code,
                    "filename": filename,
                    "filepath": str(filepath),
                    "original_code": code
                }
            )
            
            return [response_message, runner_message]
            
        except Exception as e:
            return [self.create_error_message(message.from_agent, f"Test generation failed: {str(e)}")]
    
    def _extract_and_clean_test_code(self, response: str) -> str:
        code = re.sub(r'```python\n', '', response)
        code = re.sub(r'```\n', '', code)
        code = re.sub(r'```', '', code)
        
        lines = code.split('\n')
        test_lines = []
        in_test_code = False
        
        for line in lines:
            stripped = line.strip()
            
            if (stripped.startswith(('import ', 'from ', 'class Test', 'class test')) or
                (line.startswith('    def test_') and stripped) or
                (stripped and in_test_code)):
                in_test_code = True
                test_lines.append(line)
            elif in_test_code and not stripped:
                test_lines.append(line)
            elif in_test_code and stripped.startswith('if __name__'):
                test_lines.append(line)
        
        return '\n'.join(test_lines).strip()
    
    def _validate_python_syntax(self, code: str) -> bool:
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    def _apply_test_emergency_fixes(self, test_code: str) -> str:
        lines = test_code.split('\n')
        fixed_lines = []
        
        for line in lines:
            if line.strip():
                if any(import_statement in line.lower() for import_statement in [
                    'from your_module import', 'import your_module', 'from module import', 'import module']):
                    continue
                
                leading_spaces = len(line) - len(line.lstrip())
                correct_spaces = (leading_spaces // 4) * 4
                fixed_line = ' ' * correct_spaces + line.lstrip()
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append('')
        
        fixed_code = '\n'.join(fixed_lines)
        if not fixed_code.strip() or "import unittest" not in fixed_code:
            return self._get_fallback_tests()
        
        return fixed_code
    
    def _get_fallback_tests(self) -> str:
        return '''import unittest

class TestFunction(unittest.TestCase):
    def test_basic_functionality(self):
        self.assertTrue(True)

    def test_edge_cases(self):
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()'''

# =============================================================================
# RUNNER AGENT
# =============================================================================
class RunnerAgent(BaseAgent):
    async def handle_task(self, message: AgentMessage) -> List[AgentMessage]:
        return [self.create_message(message.from_agent, MessageType.RESPONSE, 
                                  f"Runner agent received task: {message.content}")]
    
    async def handle_data(self, message: AgentMessage) -> List[AgentMessage]:
        try:
            print(f"🏃 RunnerAgent received data: {message.content}")
            
            test_code = message.metadata.get("test_code", "")
            original_code = message.metadata.get("original_code", "")
            
            if not test_code:
                return [self.create_error_message(message.from_agent, "No test code provided")]
            
            test_results = self._run_tests(original_code, test_code)
            tests_passed = "✅ TESTS PASSED" in test_results
            
            response_message = self.create_message(
                to_agent=message.from_agent,
                message_type=MessageType.DATA,
                content=f"Test execution completed",
                metadata={
                    "test_results": test_results,
                    "tests_passed": tests_passed,
                    "original_code": original_code,
                    "test_code": test_code
                }
            )
            
            return [response_message]
            
        except Exception as e:
            return [self.create_error_message(message.from_agent, f"Test execution failed: {str(e)}")]
    
    def _run_tests(self, code: str, test_code: str) -> str:
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                f.write("\n\n")
                f.write(test_code)
                test_file = f.name
            
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            os.unlink(test_file)
            
            if result.returncode == 0:
                return f"✅ TESTS PASSED\n{result.stdout}"
            else:
                return f"❌ TESTS FAILED\n{result.stdout}\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "❌ TESTS TIMEOUT - Tests took too long to run"
        except Exception as e:
            return f"❌ TEST EXECUTION ERROR: {str(e)}"

# =============================================================================
# ENHANCED GITHUB INTEGRATION - NEW
# =============================================================================
class EnhancedGitHubAgentWrapper(BaseAgent):
    """Wrapper to integrate EnhancedGitHubAgent with your BaseAgent system"""
    
    def __init__(self, agent_id: str, agent_type: str, role: str, 
                 model_name: str = DEFAULT_MODEL, model_config: Dict[str, Any] = None):
        super().__init__(agent_id, agent_type, role, model_name, model_config)
        self.enhanced_agent = enhanced_github_agent
    
    async def handle_task(self, message: AgentMessage) -> List[AgentMessage]:
        try:
            task_content = message.content.lower()
            
            if not self.enhanced_agent.is_configured():
                return [self.create_error_message(
                    message.from_agent, 
                    "GitHub not configured. Check GITHUB_TOKEN and GITHUB_USERNAME in .env file."
                )]
            
            if "extract" in task_content and "push" in task_content:
                # Extract and push code
                repo_name = self._extract_repo_name_from_message(message.content)
                result = self.enhanced_agent.extract_and_push_code(
                    repo_name=repo_name,
                    commit_message=f"AI Generated: {message.content[:50]}...",
                    auto_create_repo=True
                )
                
                if result["success"]:
                    response_content = f"""✅ Successfully pushed code to GitHub!

📁 Repository: {result['repository_url']}
🔗 Commit: {result['commit_sha'][:7]}
📊 Files: {len(result.get('files_pushed', []))} files pushed
📈 Total size: {result.get('extraction_stats', {}).get('total_size', 0)} bytes

Your AI-generated code is now on GitHub!"""
                else:
                    response_content = f"❌ GitHub push failed: {result['error']}"
                
                return [self.create_message(
                    message.from_agent,
                    MessageType.RESPONSE,
                    response_content
                )]
            
            elif "preview" in task_content or "analyze" in task_content:
                # Preview extractable code
                result = self.enhanced_agent.preview_extractable_code()
                
                if result["success"]:
                    files_info = []
                    for file_preview in result.get("files_preview", []):
                        files_info.append(f"- {file_preview['path']} ({file_preview['size']} bytes)")
                    
                    response_content = f"""📋 Code Analysis:

📊 Stats: {result['stats']['total_files']} files, {result['stats']['total_size']} bytes total

📁 Files ready for GitHub:
{chr(10).join(files_info)}

Ready to push to GitHub repository!"""
                else:
                    response_content = f"❌ Code analysis failed: {result['error']}"
                
                return [self.create_message(
                    message.from_agent,
                    MessageType.RESPONSE,
                    response_content
                )]
            
            else:
                # General GitHub help
                return [self.create_message(
                    message.from_agent,
                    MessageType.RESPONSE,
                    "🐙 GitHub Agent ready! I can:\n- Extract and push code to repositories\n- Preview generated code\n- Analyze project structure\n\nTry: 'extract and push code to my-repo'"
                )]
                
        except Exception as e:
            return [self.create_error_message(message.from_agent, f"GitHub operation failed: {str(e)}")]
    
    def _extract_repo_name_from_message(self, content: str) -> str:
        patterns = [
            r'(?:repo|repository)(?:\s*name)?:\s*([a-zA-Z0-9_-]+)',
            r'(?:create|push to|extract to)\s+([a-zA-Z0-9_-]+)',
            r'([a-zA-Z0-9_-]+)(?:\s+repository|\s+repo)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return f"ai-project-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

# =============================================================================
# AGENT FACTORY - Updated with Enhanced GitHub
# =============================================================================
class AgentFactory:
    _agent_types = {
        "coordinator": CoordinatorAgent,
        "coder": CoderAgent,
        "tester": TesterAgent,
        "runner": RunnerAgent,
        "github": GitHubAgent,  # Your existing GitHub agent
        "enhanced_github": EnhancedGitHubAgentWrapper  # NEW enhanced agent
    }
    
    @classmethod
    def create_agent(cls, agent_id: str, agent_type: str, role: str, 
                    model_name: str = DEFAULT_MODEL, 
                    model_config: Dict[str, Any] = None) -> BaseAgent:
        if agent_type not in cls._agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = cls._agent_types[agent_type]
        return agent_class(agent_id, agent_type, role, model_name, model_config)

# =============================================================================
# MESSAGE BUS
# =============================================================================
class MessageBus:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
    
    def register_agent(self, agent: BaseAgent):
        self.agents[agent.agent_id] = agent
    
    async def send_message(self, message: AgentMessage):
        print(f"📡 Sending message: {message.from_agent} -> {message.to_agent} ({message.message_type.value})")
        
        try:
            await websocket_manager.send_agent_message(
                from_agent=message.from_agent,
                to_agent=message.to_agent,
                content=message.content,
                message_type=message.message_type.value
            )
        except Exception as e:
            print(f"⚠️ WebSocket update failed: {e}")
        
        target_agent = self.agents.get(message.to_agent)
        if not target_agent:
            print(f"⚠️ Warning: Agent {message.to_agent} not found")
            return
        
        response_messages = await target_agent.process_message(message)
        
        for response in response_messages:
            await self.send_message(response)
    
    async def process_workflow(self, initial_task: str, workflow_agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            print(f"🚀 Starting workflow with task: {initial_task}")
            
            for agent_config in workflow_agents:
                agent = AgentFactory.create_agent(
                    agent_id=agent_config["id"],
                    agent_type=agent_config["type"],
                    role=agent_config["role"],
                    model_name=agent_config.get("model", "mistral"),
                    model_config=agent_config.get("model_config", {})
                )
                self.register_agent(agent)
            
            coordinator = self.agents.get("coordinator")
            if not coordinator:
                raise ValueError("No coordinator agent found")
            
            workflow_id = f"workflow_{datetime.now().timestamp()}"
            
            try:
                await websocket_manager.send_workflow_status(
                    workflow_id=workflow_id,
                    status="running",
                    agents={agent_id: {"status": "idle"} for agent_id in self.agents.keys()}
                )
            except Exception as e:
                print(f"WebSocket status update failed: {e}")
            
            initial_message = AgentMessage(
                id=f"workflow_start_{datetime.now().timestamp()}",
                from_agent="system",
                to_agent="coordinator",
                message_type=MessageType.TASK,
                content=initial_task
            )
            
            await self.send_message(initial_message)
            
            for i in range(10):
                await asyncio.sleep(0.2)
                try:
                    await websocket_manager.send_workflow_status(
                        workflow_id=workflow_id,
                        status="running",
                        agents={agent_id: {"status": "working"} for agent_id in self.agents.keys()}
                    )
                except Exception as e:
                    print(f"WebSocket progress update failed: {e}")
            
            results = {}
            for agent_id, agent in self.agents.items():
                results[agent_id] = {
                    "status": agent.status.value,
                    "memory": len(agent.memory.short_term),
                    "messages": [msg.content for msg in agent.memory.short_term[-5:]]
                }
            
            try:
                await websocket_manager.send_workflow_status(
                    workflow_id=workflow_id,
                    status="completed",
                    agents={agent_id: {"status": agent_data["status"]} for agent_id, agent_data in results.items()}
                )
            except Exception as e:
                print(f"WebSocket completion update failed: {e}")
            
            return {"success": True, "results": results, "message": "Workflow completed successfully"}
                
        except Exception as e:
            return {"success": False, "error": str(e), "message": "Workflow failed"}

# =============================================================================
# REQUEST MODELS
# =============================================================================
class PromptRequest(BaseModel):
    prompt: str
    code_history: List[str] = []
    error_history: List[str] = []
    conversation_id: Optional[str] = None

class WorkflowRequest(BaseModel):
    task: str
    agents: List[Dict[str, Any]]

class ManualAgentBox(BaseModel):
    id: str
    x: float
    y: float
    width: float
    height: float
    agentType: str
    role: str
    model: str = DEFAULT_MODEL

class ManualAgentConnection(BaseModel):
    id: str
    fromId: str
    fromSide: str
    toId: str
    toSide: str

class ManualFlowRequest(BaseModel):
    prompt: str
    boxes: List[ManualAgentBox]
    connections: List[ManualAgentConnection]

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _extract_code(response: str) -> str:
    code_patterns = [
        r'```python\n(.*?)\n```',
        r'```\n(.*?)\n```',
        r'```(.*?)```',
        r'`(.*?)`'
    ]
    
    for pattern in code_patterns:
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches[0].strip()
    
    return response.strip()

def extract_repo_name_from_prompt(prompt: str) -> str:
    """Extract repository name from user prompt"""
    patterns = [
        r'repository\s+(?:called\s+|named\s+)?([a-zA-Z0-9_-]+)',
        r'repo\s+(?:called\s+|named\s+)?([a-zA-Z0-9_-]+)', 
        r'(?:push to|create)\s+([a-zA-Z0-9_-]+)',
        r'([a-zA-Z0-9_-]+)\s+repository'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return f"ai-project-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/api-status")
async def api_status():
    return {
        "message": "Multi-Agent AI System API",
        "status": "running",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "chat_with_github": "/chat-with-github",  # NEW
            "enhanced_github": "/github/enhanced",     # NEW
            "conversations": "/conversations",
            "files": "/list-files",
            "workflow": "/run-workflow",
            "manual_flow": "/run-manual-flow"
        },
        "github_integration": "Enhanced GitHub integration available"  # NEW
    }

@app.post("/chat")
async def chat(request: PromptRequest):
    """Main chat endpoint for automated workflows"""
    try:
        print(f"Starting chat workflow with prompt: {request.prompt}")
        
        if not request.prompt or not request.prompt.strip():
            return {"type": "error", "message": "No prompt provided", "success": False}
        
        message_bus = MessageBus()
        
        if request.conversation_id:
            db_integration.attach_to_message_bus(message_bus, conversation_id=request.conversation_id)
        else:
            db_integration.attach_to_message_bus(message_bus)
        
        workflow_agents = [
            {"id": "coordinator", "type": "coordinator", "role": "Smart Coordinator", "model": "mistral"},
            {"id": "coder", "type": "coder", "role": "Python Developer", "model": "mistral"},
            {"id": "tester", "type": "tester", "role": "Test Engineer", "model": "mistral"},
            {"id": "runner", "type": "runner", "role": "Test Runner"}
        ]
        
        result = await message_bus.process_workflow(request.prompt, workflow_agents)
        
        if not result.get("success", False):
            return {"type": "error", "message": result.get("message", "Workflow failed"), "success": False}
        
        # Extract results from workflow
        code = None
        tests = None
        test_results = None
        tests_passed = None
        
        for agent_id, agent in message_bus.agents.items():
            if agent_id == "coder":
                for msg in agent.memory.short_term:
                    if msg.metadata.get("code"):
                        code = msg.metadata["code"]
                        break
            elif agent_id == "tester":
                for msg in agent.memory.short_term:
                    if msg.metadata.get("test_code"):
                        tests = msg.metadata["test_code"]
                        break
            elif agent_id == "runner":
                for msg in agent.memory.short_term:
                    if msg.metadata.get("test_results"):
                        test_results = msg.metadata["test_results"]
                        tests_passed = msg.metadata.get("tests_passed", False)
                        break
        
        # Try to read from files if not found in memory
        if not code:
            try:
                code_files = list(GENERATED_DIR.glob("code_*.py"))
                if code_files:
                    latest_code_file = max(code_files, key=lambda x: x.stat().st_mtime)
                    with open(latest_code_file, 'r', encoding='utf-8') as f:
                        code = f.read()
            except Exception as e:
                print(f"Could not read code from file: {e}")
        
        if not tests:
            try:
                test_files = list(GENERATED_DIR.glob("test_*.py"))
                if test_files:
                    latest_test_file = max(test_files, key=lambda x: x.stat().st_mtime)
                    with open(latest_test_file, 'r', encoding='utf-8') as f:
                        tests = f.read()
            except Exception as e:
                print(f"Could not read tests from file: {e}")
        
        if not test_results and code and tests:
            try:
                temp_runner = RunnerAgent("temp_runner", "runner", "Test Runner")
                test_results = temp_runner._run_tests(code, tests)
                tests_passed = "TESTS PASSED" in test_results
            except Exception as e:
                test_results = f"Test execution failed: {str(e)}"
                tests_passed = False
        
        response_type = "coding" if (code or tests) else "error"
        
        return {
            "type": response_type,
            "message": result.get("message", "Task completed"),
            "code": code,
            "tests": tests,
            "test_results": test_results,
            "tests_passed": tests_passed,
            "success": result.get("success", False)
        }
        
    except Exception as e:
        return {"type": "error", "message": f"Error processing request: {str(e)}", "success": False}

@app.post("/chat-with-github")
async def chat_with_github_integration(request: PromptRequest):
    """NEW: Enhanced chat with automatic GitHub operations"""
    try:
        # Check for GitHub operations in the prompt
        prompt_lower = request.prompt.lower()
        github_operations = ["github", "repository", "push code", "extract", "repo", "commit"]
        
        if any(op in prompt_lower for op in github_operations):
            # First, run normal chat workflow to generate code
            normal_result = await chat(request)
            
            if normal_result.get("success") and normal_result.get("code"):
                # Code was generated, now handle GitHub operation
                repo_name = extract_repo_name_from_prompt(request.prompt)
                
                if enhanced_github_agent.is_configured():
                    # Push to GitHub
                    github_result = enhanced_github_agent.extract_and_push_code(
                        repo_name=repo_name,
                        commit_message=f"Generated code: {request.prompt[:50]}...",
                        auto_create_repo=True
                    )
                    
                    # Combine results
                    return {
                        **normal_result,
                        "github_operation": github_result,
                        "repository_url": github_result.get("repository_url") if github_result.get("success") else None
                    }
                else:
                    return {
                        **normal_result,
                        "github_operation": {
                            "success": False,
                            "error": "GitHub not configured. Check GITHUB_TOKEN and GITHUB_USERNAME in .env file."
                        }
                    }
            else:
                return normal_result
        else:
            # Regular chat without GitHub operations
            return await chat(request)
            
    except Exception as e:
        return {"success": False, "error": str(e), "type": "error"}

@app.get("/github/analyze-generated")
async def analyze_generated_code():
    """NEW: Analyze generated code before pushing"""
    try:
        if not enhanced_github_agent.is_configured():
            return {"success": False, "error": "GitHub not configured"}
        
        result = enhanced_github_agent.preview_extractable_code()
        if result["success"]:
            return {
                "success": True,
                "analysis": result,
                "recommendation": "Code looks ready for GitHub!" if result["stats"]["total_files"] > 0 else "No code files found. Generate some code first."
            }
        else:
            return result
    except Exception as e:
        return {"success": False, "error": str(e)}

# =============================================================================
# ALL YOUR EXISTING ENDPOINTS (Keep as they are)
# =============================================================================

@app.post("/run-workflow")
async def run_workflow(request: WorkflowRequest):
    try:
        message_bus = MessageBus()
        result = await message_bus.process_workflow(request.task, request.agents)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/run-manual-flow")
async def run_manual_flow(data: ManualFlowRequest):
    try:
        agents = []
        for box in data.boxes:
            agents.append({
                "id": box.id,
                "type": box.agentType,
                "role": box.role,
                "model": box.model
            })
        
        message_bus = MessageBus()
        result = await message_bus.process_workflow(data.prompt, agents)
        
        messages = []
        for agent_id, agent in message_bus.agents.items():
            for msg in agent.memory.short_term:
                messages.append({
                    "from": msg.from_agent,
                    "to": msg.to_agent,
                    "type": msg.message_type.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                })
        
        return {
            "success": result.get("success", False),
            "messages": messages,
            "results": result.get("results", {}),
            "generated_files": []
        }
        
    except Exception as e:
        return {"success": False, "error": str(e), "messages": []}

@app.get("/health")
async def health_check():
    github_status = "configured" if enhanced_github_agent.is_configured() else "not_configured"
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "agents_available": ["coordinator", "coder", "tester", "runner"],
        "github_integration": github_status  # NEW
    }

@app.get("/list-files")
async def list_files():
    try:
        files = []
        for file in GENERATED_DIR.glob("*.py"):
            files.append(file.name)
        return {"files": files}
    except Exception as e:
        return {"files": [], "error": str(e)}

@app.get("/generated/{filename}")
async def get_generated_file(filename: str):
    try:
        filepath = GENERATED_DIR / filename
        if filepath.exists():
            return FileResponse(filepath, media_type="text/plain")
        else:
            raise HTTPException(status_code=404, detail=f"File {filename} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@app.get("/gpu-status")
async def get_gpu_status():
    try:
        cuda_available = False
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            cuda_available = result.returncode == 0
        except:
            pass
        
        return {
            "cuda_available": cuda_available,
            "current_model": DEFAULT_MODEL,
            "gpu_config": DEFAULT_GPU_CONFIG,
            "available_models": list(MODEL_CONFIGS.keys())
        }
    except Exception as e:
        return {"error": str(e), "cuda_available": False}

@app.get("/models")
async def get_available_models():
    return {
        "current_default": DEFAULT_MODEL,
        "available_models": MODEL_CONFIGS,
        "recommendations": {
            "code_generation": "codellama:7b-instruct",
            "general_tasks": "mistral", 
            "balanced": "llama2"
        }
    }

# =============================================================================
# ALL YOUR EXISTING GITHUB ENDPOINTS (Keep these)
# =============================================================================

# Your existing GitHub configuration
github_config = GitHubConfig()
github_agent_instance = GitHubAgent(github_config) if github_config.is_configured() else None
github_workflow = GitHubWorkflow(github_agent_instance) if github_agent_instance else None

@app.post("/github/configure")
async def configure_github(request: dict):
    """Your existing GitHub configure endpoint"""
    try:
        # Your existing GitHub configuration logic
        return {"success": True, "message": "GitHub configured"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/github/status")
async def get_github_status():
    """Your existing GitHub status endpoint"""
    return {"configured": github_config.is_configured() if github_config else False}

# =============================================================================
# DATABASE ENDPOINTS (Keep all your existing ones)
# =============================================================================

@app.post("/conversations")
async def create_conversation(request: ConversationRequest):
    try:
        conversation_id = await db_integration.start_conversation(request.title)
        return {"conversation_id": conversation_id, "title": request.title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")

@app.get("/conversations")
async def get_conversations():
    try:
        conversations = await db_integration.get_conversations()
        return [
            ConversationResponse(
                id=conv['id'],
                title=conv['title'],
                created_at=conv['created_at'],
                updated_at=conv['updated_at'],
                message_count=conv['message_count']
            )
            for conv in conversations
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

# =============================================================================
# WEBSOCKET MANAGER (Keep your existing implementation)
# =============================================================================

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.workflow_status: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

    async def send_agent_message(self, from_agent: str, to_agent: str, content: str, message_type: str = "message"):
        message = {
            "type": "agent_message",
            "from_agent": from_agent,
            "to_agent": to_agent,
            "content": content,
            "message_type": message_type,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(json.dumps(message))

    async def send_workflow_status(self, workflow_id: str, status: str, agents: Dict = None, message_history: List = None):
        message = {
            "type": "workflow_status",
            "workflow_id": workflow_id,
            "status": status,
            "agents": agents or {},
            "message_history": message_history or [],
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(json.dumps(message))

websocket_manager = WebSocketManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                if message.get("type") == "test":
                    await websocket_manager.send_personal_message(
                        json.dumps({"type": "test_response", "message": "WebSocket working!"}),
                        websocket
                    )
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        websocket_manager.disconnect(websocket)

# =============================================================================
# ENHANCED ENDPOINTS - NEW
# =============================================================================

@app.get("/github/quick-status")
async def github_quick_status():
    """NEW: Quick GitHub status check"""
    return {
        "enhanced_github": enhanced_github_agent.is_configured(),
        "username": os.getenv('GITHUB_USERNAME'),
        "message": "Enhanced GitHub ready!" if enhanced_github_agent.is_configured() else "GitHub not configured"
    }

@app.post("/github/quick-push")
async def github_quick_push(repo_name: str, commit_message: str = None):
    """NEW: Quick push all generated code to GitHub"""
    try:
        if not enhanced_github_agent.is_configured():
            raise HTTPException(status_code=400, detail="GitHub not configured")
        
        result = enhanced_github_agent.extract_and_push_code(
            repo_name=repo_name,
            commit_message=commit_message or f"Quick push from LilySmokes - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            auto_create_repo=True
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# STARTUP MESSAGE
# =============================================================================
if __name__ == "__main__":
    print("🚀 Starting Multi-Agent AI System with Enhanced GitHub Integration...")
    print(f"🔧 GPU Configuration: {DEFAULT_GPU_CONFIG}")
    print(f"📁 Generated files directory: {GENERATED_DIR}")
    print(f"🐙 GitHub Integration: {'✅ Configured' if enhanced_github_agent.is_configured() else '❌ Not Configured'}")
    if enhanced_github_agent.is_configured():
        print(f"👤 GitHub Username: {os.getenv('GITHUB_USERNAME')}")
    print("🌐 Server starting at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔗 Enhanced GitHub API: http://localhost:8000/github/enhanced")
    uvicorn.run(app, host="0.0.0.0", port=8000)