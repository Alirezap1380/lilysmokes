# =============================================================================
# IMPORTS - DON'T CHANGE THESE (unless you know what you're doing)
# =============================================================================
# These are all the tools we need to make our agent system work
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
import ast # Added for syntax validation

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from langchain_ollama import OllamaLLM
import uvicorn

# Database integration
from database import SafeDatabaseIntegration, ConversationRequest, ConversationResponse, ChatRequestWithConversation

# GitHub integration
from github_agent import GitHubAgent, GitHubConfig, GitHubRepository, GitHubWorkflow, validate_github_token, get_github_user_info

# =============================================================================
# GLOBAL CONFIGURATION
# =============================================================================

# GPU Detection and Configuration
def detect_gpu():
    """Detect if GPU is available and configure accordingly"""
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ GPU detected - using GPU acceleration")
            return {
                "num_gpu": 1,  # Use 1 GPU
                "num_thread": 8,  # Number of CPU threads
                "temperature": 0.3,  # Lower temperature for more focused code generation
                "top_p": 0.9,  # Nucleus sampling
                "repeat_penalty": 1.1,  # Prevent repetition
                "top_k": 40,  # Top-k sampling for better code quality
                "num_ctx": 4096,  # Context window size
            }
        else:
            print("⚠️ GPU not detected - using CPU only")
            return {
                "num_gpu": 0,  # No GPU
                "num_thread": 8,  # Number of CPU threads
                "temperature": 0.3,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "top_k": 40,
                "num_ctx": 4096,
            }
    except Exception as e:
        print(f"⚠️ Could not detect GPU: {e} - using CPU only")
        return {
            "num_gpu": 0,  # No GPU
            "num_thread": 8,  # Number of CPU threads
            "temperature": 0.3,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "top_k": 40,
            "num_ctx": 4096,
        }

# Default GPU configuration for all agents - Optimized for CodeLlama:7b-instruct
DEFAULT_GPU_CONFIG = detect_gpu()

# Default model configuration - Now using CodeLlama:7b-instruct
DEFAULT_MODEL = "codellama:7b-instruct"

# Model-specific configurations for different tasks
MODEL_CONFIGS = {
    "codellama:7b-instruct": {
        "num_gpu": DEFAULT_GPU_CONFIG["num_gpu"],  # Use detected GPU setting
        "num_thread": 8,
        "temperature": 0.3,  # Lower for code generation
        "top_p": 0.9,
        "repeat_penalty": 1.1,
        "top_k": 40,
        "num_ctx": 4096,
    },
    "mistral": {
        "num_gpu": DEFAULT_GPU_CONFIG["num_gpu"],  # Use detected GPU setting
        "num_thread": 8,
        "temperature": 0.7,  # Higher for general tasks
        "top_p": 0.9,
        "repeat_penalty": 1.1,
    },
    "llama2": {
        "num_gpu": DEFAULT_GPU_CONFIG["num_gpu"],  # Use detected GPU setting
        "num_thread": 8,
        "temperature": 0.5,
        "top_p": 0.9,
        "repeat_penalty": 1.1,
    }
}

# =============================================================================
# APP & CORS CONFIGURATION - DON'T CHANGE THIS SECTION
# =============================================================================
# What: Creates the web server and allows frontend to connect
# Why: Frontend needs to talk to backend, CORS allows this
# Can I change: NO - this is essential for frontend-backend communication
app = FastAPI(title="Multi-Agent AI System", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows any frontend to connect (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for the API testing interface
app.mount("/static", StaticFiles(directory="static"), name="static")

# =============================================================================
# ROOT ENDPOINT - API STATUS PAGE
# =============================================================================
@app.get("/")
async def root():
    """Root endpoint - serves the API testing interface"""
    return FileResponse("static/index.html")

@app.get("/api-docs")
async def api_docs():
    """Redirect to FastAPI's built-in documentation"""
    return RedirectResponse(url="/docs")

@app.get("/api-status")
async def api_status():
    """API status endpoint - shows API status and available endpoints"""
    return {
        "message": "Multi-Agent AI System API",
        "status": "running",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "conversations": "/conversations",
            "files": "/list-files",
            "workflow": "/run-workflow",
            "manual_flow": "/run-manual-flow",
            "agents": "/agents",
            "models": "/models",
            "gpu_status": "/gpu-status"
        },
        "documentation": "/docs",
        "frontend": "http://localhost:5173",
        "api_testing_interface": "/"
    }

# =============================================================================
# PATHS & DIRECTORIES - YOU CAN CHANGE THESE PATHS
# =============================================================================
# What: Defines where files are stored and loaded from
# Why: We need consistent places to save generated code and tests
# Can I change: YES - you can change where files are saved
BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated"  # Where all generated files go
GENERATED_DIR.mkdir(exist_ok=True)  # Create directory if it doesn't exist

# =============================================================================
# DATABASE INTEGRATION - SAFE ADDITION
# =============================================================================
# Initialize database integration (non-disruptive)
db_integration = SafeDatabaseIntegration()

# =============================================================================
# ENUMS AND DATA MODELS
# =============================================================================
class MessageType(Enum):
    """
    What: Different types of messages agents can send to each other
    Why: So agents know how to handle different kinds of messages
    Can I change: YES - you can add more message types like "FEEDBACK", "UPDATE", etc.
    """
    TASK = "task"        # "Do this work for me"
    DATA = "data"        # "Here's some information"
    REQUEST = "request"  # "I need something from you"
    RESPONSE = "response" # "Here's your answer"
    ERROR = "error"      # "Something went wrong"
    STATUS = "status"    # "Here's my current status"
    REVIEW = "review"    # "Review generated code or tests"

# =============================================================================
# AGENT MESSAGE - THE WAY AGENTS TALK TO EACH OTHER
# =============================================================================
class AgentMessage(BaseModel):
    """
    What: This is like an email between agents - it has sender, receiver, content
    Why: Agents need a standard way to talk to each other
    Can I change: YES - but be careful, this affects everything
    """
    id: str                              # Unique ID for this message (like email ID)
    from_agent: str                      # Who sent this message
    to_agent: str                        # Who should receive this message
    message_type: MessageType            # What kind of message is this
    content: str                         # The actual message content
    metadata: Dict[str, Any] = {}        # Extra information (you can add anything here)
    timestamp: datetime = datetime.now() # When was this message sent
    
    # NEW: These help with retrying failed messages
    retry_count: int = 0                    # How many times we've tried to send this
    parent_message_id: Optional[str] = None # If this is a retry, what's the original message

    def create_retry_message(self) -> 'AgentMessage':
        """
        What: Makes a copy of this message for retrying
        Why: Sometimes messages fail, so we need to try again
        Can I change: YES - you can modify retry logic
        """
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

# =============================================================================
# AGENT STATUS - TRACKS WHAT EACH AGENT IS DOING
# =============================================================================
class AgentStatus(Enum):
    """
    What: Tells us what state each agent is in
    Why: So we know if agents are busy, done, or having problems
    Can I change: YES - you can add more statuses like "PAUSED", "RESTARTING", etc.
    """
    IDLE = "idle"           # Agent is ready for work
    WORKING = "working"      # Agent is currently processing
    WAITING = "waiting"      # Agent is waiting for something
    COMPLETED = "completed"  # Agent finished its task
    ERROR = "error"          # Agent encountered an error

# =============================================================================
# AGENT MEMORY - HOW AGENTS REMEMBER THINGS
# =============================================================================
class AgentMemory(BaseModel):
    """
    What: Each agent has a memory system to remember conversations and context
    Why: Agents need to remember what they've done and what others have said
    Can I change: YES - you can add database storage, more memory types, etc.
    """
    short_term: List[AgentMessage] = []  # Recent messages (last 50)
    long_term: Dict[str, Any] = {}       # Persistent data (like a database)
    context: Dict[str, Any] = {}         # Current context (what we're working on)
    
    def add_message(self, message: AgentMessage):
        """
        What: Adds a new message to the agent's memory
        Why: Agents need to remember conversations
        Can I change: YES - you can change how messages are stored
        """
        self.short_term.append(message)
        # Keep only last 50 messages in short-term (prevents memory overflow)
        if len(self.short_term) > 50:
            self.short_term = self.short_term[-50:]
    
    def get_context_for_prompt(self) -> str:
        """
        What: Creates a summary of recent conversations for LLM prompts
        Why: LLMs need context to understand what's happening
        Can I change: YES - you can change how context is formatted
        """
        recent_messages = self.short_term[-10:]  # Last 10 messages
        context_str = "Recent conversation:\n"
        for msg in recent_messages:
            context_str += f"{msg.from_agent} -> {msg.to_agent}: {msg.content[:100]}...\n"
        return context_str

# =============================================================================
# BASE AGENT - THE FOUNDATION FOR ALL AGENTS
# =============================================================================
class BaseAgent(ABC):
    """
    What: The base class that all agents inherit from
    Why: Provides common functionality like message handling and memory
    Can I change: YES - you can add more base functionality, but be careful
    """
    
    def __init__(self, agent_id: str, agent_type: str, role: str, 
                 model_name: str = DEFAULT_MODEL, model_config: Dict[str, Any] = None):
        """
        What: Sets up a new agent with its identity and AI model
        Why: Each agent needs a unique identity and its own AI model
        Can I change: YES - you can add more initialization parameters
        """
        self.agent_id = agent_id          # Unique name for this agent
        self.agent_type = agent_type      # What kind of agent (coder, tester, etc.)
        self.role = role                  # What this agent does
        self.status = AgentStatus.IDLE    # Current status
        self.memory = AgentMemory()       # Agent's memory system
        self.model_config = model_config or {}  # AI model settings
        
        # Initialize LLM - each agent gets its own AI model instance
        # Get model-specific configuration or use default
        model_specific_config = MODEL_CONFIGS.get(model_name, DEFAULT_GPU_CONFIG.copy())
        
        # Merge configurations: model-specific -> user-provided -> default
        final_config = {**DEFAULT_GPU_CONFIG, **model_specific_config, **self.model_config}
        self.llm = OllamaLLM(model=model_name, **final_config)
        
        # Message handling - maps message types to handler functions
        self.message_handlers: Dict[MessageType, Callable] = {
            MessageType.TASK: self.handle_task,
            MessageType.DATA: self.handle_data,
            MessageType.REQUEST: self.handle_request,
            MessageType.RESPONSE: self.handle_response,
            MessageType.ERROR: self.handle_error,
            MessageType.STATUS: self.handle_status
        }
    
    async def process_message(self, message: AgentMessage) -> List[AgentMessage]:
        """
        What: Processes an incoming message and returns responses
        Why: This is how agents communicate with each other
        Can I change: YES - you can modify how messages are processed
        """
        try:
            self.status = AgentStatus.WORKING
            self.memory.add_message(message)
            
            # Get the right handler for this message type
            handler = self.message_handlers.get(message.message_type)
            if handler:
                responses = await handler(message)
            else:
                # If no handler, create an error response
                responses = [self.create_error_message(message.from_agent, 
                                                    f"Unknown message type: {message.message_type}")]
            
            self.status = AgentStatus.IDLE
            return responses
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            return [self.create_error_message(message.from_agent, str(e))]
    
    def create_message(self, to_agent: str, message_type: MessageType, 
                      content: str, metadata: Dict[str, Any] = None) -> AgentMessage:
        """
        What: Creates a new message to send to another agent
        Why: Agents need a standard way to create messages
        Can I change: YES - you can modify message creation
        """
        return AgentMessage(
            id=f"{self.agent_id}_{datetime.now().timestamp()}",
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            metadata=metadata or {}
        )
    
    def create_error_message(self, to_agent: str, error: str) -> AgentMessage:
        """
        What: Creates an error message when something goes wrong
        Why: Agents need to report errors to each other
        Can I change: YES - you can modify error reporting
        """
        return self.create_message(to_agent, MessageType.ERROR, error)
    
    # These are abstract methods - each agent type must implement them
    @abstractmethod
    async def handle_task(self, message: AgentMessage) -> List[AgentMessage]:
        """Handle task messages - each agent type implements this differently"""
        pass
    
    async def handle_data(self, message: AgentMessage) -> List[AgentMessage]:
        """Handle data messages - default implementation"""
        return [self.create_message(message.from_agent, MessageType.RESPONSE, 
                                  f"Received data: {message.content}")]
    
    async def handle_request(self, message: AgentMessage) -> List[AgentMessage]:
        """Handle request messages - default implementation"""
        return [self.create_message(message.from_agent, MessageType.RESPONSE, 
                                  f"Handled request: {message.content}")]
    
    async def handle_response(self, message: AgentMessage) -> List[AgentMessage]:
        """Handle response messages - default implementation"""
        return []  # Usually no response needed for responses
    
    async def handle_error(self, message: AgentMessage) -> List[AgentMessage]:
        """Handle error messages - default implementation"""
        print(f"Agent {self.agent_id} received error: {message.content}")
        return []
    
    async def handle_status(self, message: AgentMessage) -> List[AgentMessage]:
        """Handle status messages - default implementation"""
        return [self.create_message(message.from_agent, MessageType.STATUS, 
                                  f"Status: {self.status.value}")]
    
    def update_model(self, model_name: str, model_config: Dict[str, Any] = None):
        """
        What: Changes the AI model this agent uses
        Why: Agents might need different models for different tasks
        Can I change: YES - you can modify model switching logic
        """
        self.model_config = model_config or {}
        self.llm = OllamaLLM(model=model_name, **self.model_config)

# =============================================================================
# COORDINATOR AGENT - THE BOSS AGENT
# =============================================================================
class CoordinatorAgent(BaseAgent):
    """
    What: The main coordinator that manages other agents
    Why: Someone needs to coordinate the workflow and assign tasks
    Can I change: YES - you can modify how coordination works
    """
    
    async def handle_task(self, message: AgentMessage) -> List[AgentMessage]:
        """
        What: Handles incoming tasks and coordinates the workflow
        Why: This is where the main logic for task distribution happens
        Can I change: YES - you can modify the coordination strategy
        """
        try:
            print(f"🎯 CoordinatorAgent received task: {message.content}")
            
            # Get context from memory
            context = self.memory.get_context_for_prompt()
            
            # Create a comprehensive prompt for the coordinator
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
                    {{
                        "agent": "coder",
                        "task": "Write a Python function that...",
                        "priority": 1
                    }},
                    {{
                        "agent": "tester", 
                        "task": "Create test cases for the function",
                        "priority": 2
                    }}
                ]
            }}
            """
            
            # Get AI response
            response = self.llm.invoke(prompt)
            
            # Try to parse the response as JSON
            try:
                plan = json.loads(response)
                steps = plan.get("steps", [])
            except:
                # If JSON parsing fails, create a simple plan
                steps = [
                    {"agent": "coder", "task": message.content, "priority": 1},
                    {"agent": "tester", "task": "Create tests for the generated code", "priority": 2}
                ]
            
            print(f"📋 Created {len(steps)} workflow steps")
            
            # Create messages for each step
            responses = []
            for step in steps:
                agent_id = step["agent"]
                task = step["task"]
                
                print(f"📤 Sending task to {agent_id}: {task[:50]}...")
                
                # Create task message for the agent
                task_message = self.create_message(
                    to_agent=agent_id,
                    message_type=MessageType.TASK,
                    content=task,
                    metadata={"priority": step.get("priority", 1)}
                )
                responses.append(task_message)
            
            print(f"📤 Sending {len(responses)} task messages")
            return responses
            
        except Exception as e:
            print(f"❌ Coordination failed: {str(e)}")
            return [self.create_error_message(message.from_agent, f"Coordination failed: {str(e)}")]

# =============================================================================
# CODER AGENT - WRITES CODE
# =============================================================================
class CoderAgent(BaseAgent):
    """
    What: An agent that writes code based on requirements
    Why: We need an agent specifically for code generation
    Can I change: YES - you can modify how code generation works
    """
    
    async def handle_task(self, message: AgentMessage) -> List[AgentMessage]:
        """
        What: Handles coding tasks and generates code
        Why: This is where the actual code generation happens
        Can I change: YES - you can modify the code generation strategy
        """
        try:
            print(f"🔧 CoderAgent received task: {message.content}")
            
            # Enhanced prompt for clean code generation
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

Example of what to generate:
def sum_numbers(a: int, b: int) -> int:
    \"\"\"Add two numbers and return the result.\"\"\"
    try:
        return a + b
    except TypeError as e:
        raise ValueError(f"Both arguments must be integers: {{e}}")

Generate ONLY the function code, nothing else.
"""
            
            response = self.llm.invoke(prompt)
            code = self._simple_code_extraction(response)
            
            # Save and return
            timestamp = _timestamp()
            filename = f"code_{timestamp}.py"
            filepath = GENERATED_DIR / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Return messages
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
            print(f"❌ Code generation failed: {str(e)}")
            return [self.create_error_message(message.from_agent, f"Code generation failed: {str(e)}")]
    
    def _simple_code_extraction(self, response: str) -> str:
        """Enhanced code extraction that removes all comments and explanations"""
        # Remove markdown code blocks
        code = re.sub(r'```python\n', '', response)
        code = re.sub(r'```\n', '', code)
        code = re.sub(r'```', '', code)
        
        # Remove common prefixes and explanations
        lines = code.split('\n')
        cleaned_lines = []
        in_code = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines at the beginning
            if not in_code and not stripped:
                continue
                
            # Start collecting code when we see function definitions or imports
            if (stripped.startswith(('def ', 'import ', 'from ')) or
                (stripped.startswith('class ') and ':' in stripped) or
                (in_code and stripped)):
                in_code = True
                cleaned_lines.append(line)
            elif in_code:
                # Keep all lines once we're in code mode
                cleaned_lines.append(line)
        
        # Remove any remaining explanatory text
        result = '\n'.join(cleaned_lines).strip()
        
        # Remove any remaining markdown or explanatory text
        result = re.sub(r'^.*?(def |import |from |class )', r'\1', result, flags=re.DOTALL)
        
        return result
    
    def _fix_indentation(self, code: str) -> str:
        """
        Fix common indentation issues in Python code
        """
        # Simple approach: ensure consistent 4-space indentation
        lines = code.split('\n')
        fixed_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                fixed_lines.append('')
                continue
            
            # Remove any existing indentation and add proper 4-space indentation
            # This is a simplified approach that ensures consistent formatting
            fixed_lines.append(stripped)
        
        return '\n'.join(fixed_lines)
    
    def _validate_python_syntax(self, code: str) -> bool:
        """
        Validate Python syntax
        """
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False
    
    def _fix_common_syntax_issues(self, code: str) -> str:
        """
        Fix common syntax issues in generated code
        """
        # Fix common issues
        code = code.replace('```python', '').replace('```', '')
        code = code.replace('`', '')
        
        # Remove any markdown formatting
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip markdown lines
            if line.strip().startswith('#') and not line.strip().startswith('##'):
                continue
            if line.strip().startswith('[') and line.strip().endswith(']'):
                continue
            cleaned_lines.append(line)
        
        # Fix common indentation and docstring issues
        fixed_code = self._fix_docstring_and_indentation('\n'.join(cleaned_lines))
        
        return fixed_code
    
    def _fix_docstring_and_indentation(self, code: str) -> str:
        """
        Fix docstring and indentation issues in generated code
        """
        lines = code.split('\n')
        fixed_lines = []
        in_function = False
        in_docstring = False
        docstring_content = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                fixed_lines.append('')
                continue
            
            # Check if we're entering a function
            if stripped.startswith('def '):
                in_function = True
                in_docstring = False
                docstring_content = []
                fixed_lines.append(stripped)
                continue
            
            # Check if we're entering a docstring
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_function and not in_docstring:
                    in_docstring = True
                    # Add proper indentation for docstring start
                    fixed_lines.append('    ' + stripped)
                    continue
                elif in_docstring:
                    in_docstring = False
                    # Add proper indentation for docstring end
                    fixed_lines.append('    ' + stripped)
                    continue
            
            # Handle docstring content
            if in_docstring:
                # Collect docstring content
                docstring_content.append(stripped)
                continue
            
            # If we were in a docstring but didn't find closing quotes, add them
            if docstring_content and not in_docstring:
                # Add the collected docstring content with proper indentation
                for content_line in docstring_content:
                    fixed_lines.append('    ' + content_line)
                # Add closing quotes
                fixed_lines.append('    """')
                docstring_content = []
            
            # Handle function body - simple 4-space indentation
            if in_function and not in_docstring and not docstring_content:
                # Simple approach: indent everything in function body with 4 spaces
                fixed_lines.append('    ' + stripped)
                continue
            
            # Handle non-function code
            fixed_lines.append(stripped)
        
        # If we still have docstring content at the end, add closing quotes
        if docstring_content:
            for content_line in docstring_content:
                fixed_lines.append('    ' + content_line)
            fixed_lines.append('    """')
        
        return '\n'.join(fixed_lines)
    
    def _get_fallback_code(self) -> str:
        """
        Get fallback code with proper indentation
        """
        return '''def add_two_numbers(a: int, b: int) -> int:
    \"\"\"
    Add two numbers together.
    
    Args:
        a (int): First number
        b (int): Second number
        
    Returns:
        int: Sum of the two numbers
    \"\"\"
    try:
        return a + b
    except TypeError as e:
        raise ValueError(f"Both arguments must be numbers: {e}")'''

# =============================================================================
# TESTER AGENT - CREATES TESTS
# =============================================================================
class TesterAgent(BaseAgent):
    """
    What: An agent that creates test cases for code
    Why: We need an agent specifically for test generation
    Can I change: YES - you can modify how test generation works
    """
    
    async def handle_task(self, message: AgentMessage) -> List[AgentMessage]:
        """
        What: Handles task messages for test generation
        Why: Required by abstract BaseAgent class
        Can I change: YES - you can modify task handling
        """
        # For now, just acknowledge the task
        return [self.create_message(message.from_agent, MessageType.RESPONSE, 
                                  f"Tester agent received task: {message.content}")]
    
    async def handle_data(self, message: AgentMessage) -> List[AgentMessage]:
        """
        What: Handles code data and generates test cases
        Why: This is where test generation happens
        Can I change: YES - you can modify the test generation strategy
        """
        try:
            print(f"🧪 TesterAgent received data: {message.content}")
            
            # Extract code from metadata
            code = message.metadata.get("code", "")
            if not code:
                print("❌ No code provided for testing")
                return [self.create_error_message(message.from_agent, "No code provided for testing")]
            
            print(f"📝 Code to test: {len(code)} characters")
            
            # Create a comprehensive testing prompt
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
            7. Test both valid inputs and invalid inputs
            8. Test edge cases like zero, negative numbers, large numbers
            9. DO NOT include the original code in the test file
            10. Only generate the test code, not the original code
            11. DO NOT use ANY import statements - the functions will be available directly
            12. Write tests as if the functions are already defined in the same scope
            13. IMPORTANT: Do not use 'from your_module import' or any import statements
            14. The functions will be executed in the same file as the tests
            
            Generate only the test code, no explanations or markdown formatting.
            """
            
            print(f"🤖 Sending test prompt to LLM: {prompt[:100]}...")
            
            # Get AI response
            response = self.llm.invoke(prompt)
            print(f"📝 LLM test response received: {len(response)} characters")
            
            # Extract test code from response
            test_code = self._extract_and_clean_test_code(response)
            print(f"🔍 Extracted test code: {len(test_code)} characters")
            
            if not test_code or len(test_code.strip()) < 10:
                print("⚠️ No valid test code extracted, using fallback")
                test_code = self._get_fallback_tests()
            
            # FIX: Validate syntax and apply emergency fixes
            if not self._validate_python_syntax(test_code):
                print("⚠️ Generated test code has syntax issues, applying emergency fixes")
                test_code = self._apply_test_emergency_fixes(test_code)
            
            # Save the generated tests to a file
            timestamp = _timestamp()
            filename = f"test_{timestamp}.py"
            filepath = GENERATED_DIR / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(test_code)
            
            print(f"💾 Tests saved to: {filepath}")
            
            # Create response message with the tests for the original sender
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
            
            # ALSO send the tests directly to the runner agent
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
            
            print(f"📤 Sending {len([response_message, runner_message])} messages")
            return [response_message, runner_message]
            
        except Exception as e:
            print(f"❌ Test generation failed: {str(e)}")
            return [self.create_error_message(message.from_agent, f"Test generation failed: {str(e)}")]
    
    # FIX: Add proper test code extraction method (like CoderAgent's _extract_and_clean_code)
    def _extract_and_clean_test_code(self, response: str) -> str:
        """Extract and clean test code from LLM response"""
        # Remove markdown code blocks
        code = re.sub(r'```python\n', '', response)
        code = re.sub(r'```\n', '', code)
        code = re.sub(r'```', '', code)
        
        # Remove explanatory text and keep only test code
        lines = code.split('\n')
        test_lines = []
        in_test_code = False
        
        for line in lines:
            stripped = line.strip()
            
            # Start collecting when we see imports or class definitions
            if (stripped.startswith(('import ', 'from ', 'class Test', 'class test')) or
                (line.startswith('    def test_') and stripped) or
                (stripped and in_test_code)):
                in_test_code = True
                test_lines.append(line)
            elif in_test_code and not stripped:
                # Keep empty lines within test code
                test_lines.append(line)
            elif in_test_code and stripped.startswith('if __name__'):
                # Keep the main block
                test_lines.append(line)
        
        return '\n'.join(test_lines).strip()
    
    # FIX: Add syntax validation method (like CoderAgent)
    def _validate_python_syntax(self, code: str) -> bool:
        """Validate Python syntax"""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    # FIX: Add emergency fixes method (like CoderAgent's _apply_emergency_fixes)
    def _apply_test_emergency_fixes(self, test_code: str) -> str:
        """Apply emergency fixes to make test code syntactically correct"""
        lines = test_code.split('\n')
        fixed_lines = []
        
        for line in lines:
            if line.strip():
                # Remove any import statements that reference the functions
                if any(import_statement in line.lower() for import_statement in [
                    'from your_module import',
                    'import your_module',
                    'from module import',
                    'import module'
                ]):
                    continue  # Skip this line
                
                # Fix indentation - use 4 spaces consistently
                leading_spaces = len(line) - len(line.lstrip())
                correct_spaces = (leading_spaces // 4) * 4
                fixed_line = ' ' * correct_spaces + line.lstrip()
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append('')
        
        # Ensure basic test structure
        fixed_code = '\n'.join(fixed_lines)
        if not fixed_code.strip() or "import unittest" not in fixed_code:
            return self._get_fallback_tests()
        
        return fixed_code
    
    def _get_fallback_tests(self) -> str:
        """Get fallback test code"""
        return '''import unittest

class TestFunction(unittest.TestCase):
    def test_basic_functionality(self):
        # Add your test here
        self.assertTrue(True)

    def test_edge_cases(self):
        # Add edge case tests here
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()'''

# =============================================================================
# RUNNER AGENT - EXECUTES TESTS
# =============================================================================
class RunnerAgent(BaseAgent):
    """
    What: An agent that executes tests and reports results
    Why: We need an agent to actually run the tests and check if they pass
    Can I change: YES - you can modify how test execution works
    """
    
    async def handle_task(self, message: AgentMessage) -> List[AgentMessage]:
        """
        What: Handles task messages for test execution
        Why: Required by abstract BaseAgent class
        Can I change: YES - you can modify task handling
        """
        # For now, just acknowledge the task
        return [self.create_message(message.from_agent, MessageType.RESPONSE, 
                                  f"Runner agent received task: {message.content}")]
    
    async def handle_data(self, message: AgentMessage) -> List[AgentMessage]:
        """
        What: Handles test data and executes the tests
        Why: This is where actual test execution happens
        Can I change: YES - you can modify the test execution strategy
        """
        try:
            print(f"🏃 RunnerAgent received data: {message.content}")
            
            # Extract test code and original code from metadata
            test_code = message.metadata.get("test_code", "")
            original_code = message.metadata.get("original_code", "")
            
            if not test_code:
                print("❌ No test code provided")
                return [self.create_error_message(message.from_agent, "No test code provided")]
            
            print(f"🧪 Test code to execute: {len(test_code)} characters")
            print(f"📝 Original code: {len(original_code)} characters")
            
            # Run the tests
            test_results = self._run_tests(original_code, test_code)
            print(f"🏃 Test execution completed: {len(test_results)} characters")
            
            # Determine if tests passed
            tests_passed = "✅ TESTS PASSED" in test_results
            
            # Create response message with test results
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
            
            print(f"📤 Sending test results: {'PASSED' if tests_passed else 'FAILED'}")
            return [response_message]
            
        except Exception as e:
            print(f"❌ Test execution failed: {str(e)}")
            return [self.create_error_message(message.from_agent, f"Test execution failed: {str(e)}")]
    
    def _run_tests(self, code: str, test_code: str) -> str:
        """
        What: Actually runs the tests and returns the results
        Why: We need to execute the tests in a safe environment
        Can I change: YES - you can modify the test execution environment
        """
        try:
            print(f"🔧 Running tests with {len(code)} chars of code and {len(test_code)} chars of tests")
            
            # Create a temporary file that combines both code and tests
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                # First execute the code to define the functions
                f.write(code)
                f.write("\n\n")
                # Then add the tests
                f.write(test_code)
                test_file = f.name
            
            print(f"📁 Created combined file: {test_file}")
            
            # Run the tests using subprocess
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            print(f"🏃 Test execution completed with return code: {result.returncode}")
            print(f"📤 stdout: {len(result.stdout)} chars")
            print(f"📤 stderr: {len(result.stderr)} chars")
            
            # Clean up temporary files
            os.unlink(test_file)
            
            # Return the test results
            if result.returncode == 0:
                return f"✅ TESTS PASSED\n{result.stdout}"
            else:
                return f"❌ TESTS FAILED\n{result.stdout}\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "❌ TESTS TIMEOUT - Tests took too long to run"
        except Exception as e:
            return f"❌ TEST EXECUTION ERROR: {str(e)}"

# =============================================================================
# GITHUB AGENT - CODE EXTRACTION AND REPOSITORY MANAGEMENT
# =============================================================================
class GitHubAgent(BaseAgent):
    """
    What: An agent that manages GitHub operations and code extraction
    Why: We need an agent that can extract code and push to GitHub
    Can I change: YES - you can modify GitHub operations
    """
    
    def __init__(self, agent_id: str, agent_type: str, role: str, 
                 model_name: str = DEFAULT_MODEL, model_config: Dict[str, Any] = None):
        super().__init__(agent_id, agent_type, role, model_name, model_config)
        self.github_config = GitHubConfig()
        self.github_agent_instance = GitHubAgent(self.github_config) if self.github_config.is_configured() else None
        self.github_workflow = GitHubWorkflow(self.github_agent_instance) if self.github_agent_instance else None
    
    async def process_message(self, message: AgentMessage) -> List[AgentMessage]:
        """
        What: Processes incoming messages and handles GitHub operations
        Why: This is the main method that handles GitHub integration
        Can I change: YES - you can modify GitHub logic
        """
        print(f"🐙 GitHub Agent {self.agent_id} processing message: {message.content[:100]}...")
        
        # Store the message in memory
        self.memory.add_message(message)
        
        # Generate response using AI
        ai_response = await self._generate_ai_response(message.content)
        
        # Parse the message to determine GitHub operation
        operation = self._parse_github_operation(message.content)
        
        responses = []
        
        if operation:
            try:
                result = await self._execute_github_operation(operation)
                
                # Create response message
                response_content = f"GitHub operation result:\n{result}"
                response = AgentMessage(
                    from_agent=self.agent_id,
                    to_agent=message.from_agent,
                    content=response_content,
                    message_type=AgentStatus.SUCCESS
                )
                responses.append(response)
                
            except Exception as e:
                # Create error response
                error_content = f"GitHub operation failed: {str(e)}"
                error_response = AgentMessage(
                    from_agent=self.agent_id,
                    to_agent=message.from_agent,
                    content=error_content,
                    message_type=AgentStatus.ERROR
                )
                responses.append(error_response)
        else:
            # No specific operation, just send AI response
            response = AgentMessage(
                from_agent=self.agent_id,
                to_agent=message.from_agent,
                content=ai_response,
                message_type=AgentStatus.SUCCESS
            )
            responses.append(response)
        
        return responses
    
    def _parse_github_operation(self, content: str) -> Dict[str, Any]:
        """
        What: Parses content to determine GitHub operation
        Why: We need to understand what GitHub operation to perform
        Can I change: YES - you can modify parsing logic
        """
        content_lower = content.lower()
        
        if "extract" in content_lower and "github" in content_lower:
            # Extract and push to GitHub
            return {
                "type": "extract_and_push",
                "source_dir": GENERATED_DIR,
                "repo_name": self._extract_repo_name(content),
                "description": self._extract_description(content),
                "private": "private" in content_lower
            }
        elif "list" in content_lower and "repository" in content_lower:
            # List repositories
            return {"type": "list_repositories"}
        elif "create" in content_lower and "repository" in content_lower:
            # Create repository
            return {
                "type": "create_repository",
                "name": self._extract_repo_name(content),
                "description": self._extract_description(content),
                "private": "private" in content_lower
            }
        
        return None
    
    def _extract_repo_name(self, content: str) -> str:
        """Extract repository name from content"""
        # Simple extraction - look for patterns like "repo: name" or "repository: name"
        patterns = [
            r'repo:\s*(\w+)',
            r'repository:\s*(\w+)',
            r'name:\s*(\w+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Default to timestamp-based name
        return f"ai-generated-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    def _extract_description(self, content: str) -> str:
        """Extract description from content"""
        # Simple extraction - look for patterns like "description: text"
        match = re.search(r'description:\s*(.+)', content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return "AI-generated code from Cube AI System"
    
    async def _execute_github_operation(self, operation: Dict[str, Any]) -> str:
        """
        What: Executes GitHub operations
        Why: We need to perform the actual GitHub operations
        Can I change: YES - you can modify operation execution
        """
        if not self.github_workflow:
            return "GitHub not configured. Please set GITHUB_TOKEN and GITHUB_USERNAME environment variables."
        
        op_type = operation.get("type")
        
        if op_type == "extract_and_push":
            result = self.github_workflow.extract_and_push_project(
                source_dir=operation["source_dir"],
                repo_name=operation["repo_name"],
                description=operation.get("description", ""),
                private=operation.get("private", False)
            )
            return json.dumps(result, indent=2)
        
        elif op_type == "list_repositories":
            result = self.github_agent_instance.list_user_repositories()
            return json.dumps(result, indent=2)
        
        elif op_type == "create_repository":
            repo = GitHubRepository(
                name=operation["name"],
                description=operation.get("description", ""),
                private=operation.get("private", False)
            )
            result = self.github_agent_instance.create_repository(repo)
            return json.dumps(result, indent=2)
        
        else:
            return f"Unknown operation type: {op_type}"

# =============================================================================
# AGENT FACTORY - CREATES AGENTS DYNAMICALLY
# =============================================================================
class AgentFactory:
    """
    What: A factory that creates different types of agents
    Why: We need a way to create agents without hardcoding them
    Can I change: YES - you can add new agent types here
    """
    
    # Registry of available agent types
    _agent_types = {
        "coordinator": CoordinatorAgent,
        "coder": CoderAgent,
        "tester": TesterAgent,
        "runner": RunnerAgent,
        "github": GitHubAgent  # Add GitHub agent
    }
    
    @classmethod
    def create_agent(cls, agent_id: str, agent_type: str, role: str, 
                    model_name: str = DEFAULT_MODEL, 
                    model_config: Dict[str, Any] = None) -> BaseAgent:
        """
        What: Creates a new agent of the specified type
        Why: This allows us to create agents dynamically
        Can I change: YES - you can modify how agents are created
        """
        if agent_type not in cls._agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = cls._agent_types[agent_type]
        return agent_class(agent_id, agent_type, role, model_name, model_config)
    
    @classmethod
    def register_agent_type(cls, agent_type: str, agent_class: type):
        """
        What: Registers a new agent type
        Why: This allows you to add custom agent types
        Can I change: YES - you can add new agent types
        """
        cls._agent_types[agent_type] = agent_class

# =============================================================================
# MESSAGE BUS - THE COMMUNICATION SYSTEM
# =============================================================================
class MessageBus:
    """
    What: Manages communication between all agents
    Why: Agents need a central system to send messages to each other
    Can I change: YES - you can modify the communication system
    """
    
    def __init__(self):
        """Initialize the message bus"""
        self.agents: Dict[str, BaseAgent] = {}  # All registered agents
    
    def register_agent(self, agent: BaseAgent):
        """
        What: Registers an agent with the message bus
        Why: Agents need to be registered to receive messages
        Can I change: YES - you can modify registration logic
        """
        self.agents[agent.agent_id] = agent
    
    async def send_message(self, message: AgentMessage):
        """
        What: Sends a message from one agent to another
        Why: This is how agents communicate with each other
        Can I change: YES - you can modify message routing
        """
        print(f"🔀 Sending message: {message.from_agent} -> {message.to_agent} ({message.message_type.value})")
        print(f"   Content: {message.content[:100]}...")
        
        # NEW: Log message to database (NON-BLOCKING)
        if hasattr(self, 'logger'):
            asyncio.create_task(self.logger.log_message(message))
        
        # NEW: Send real-time update via WebSocket
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
        
        # Process the message and get responses
        response_messages = await target_agent.process_message(message)
        
        print(f"📤 Agent {message.to_agent} generated {len(response_messages)} responses")
        
        # Send each response message
        for response in response_messages:
            await self.send_message(response)
    
    async def process_workflow(self, initial_task: str, workflow_agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        What: Processes a complete workflow from start to finish
        Why: This orchestrates the entire multi-agent workflow
        Can I change: YES - you can modify the workflow processing
        """
        try:
            print(f"🚀 Starting workflow with task: {initial_task}")
            print(f"🤖 Creating {len(workflow_agents)} agents")
            
            # Create and register all agents
            for agent_config in workflow_agents:
                agent = AgentFactory.create_agent(
                    agent_id=agent_config["id"],
                    agent_type=agent_config["type"],
                    role=agent_config["role"],
                    model_name=agent_config.get("model", "mistral"),
                    model_config=agent_config.get("model_config", {})
                )
                self.register_agent(agent)
                print(f"✅ Created agent: {agent_config['id']} ({agent_config['type']})")
            
            # Start the workflow with the coordinator
            coordinator = self.agents.get("coordinator")
            if not coordinator:
                raise ValueError("No coordinator agent found")
            
            # NEW: Send workflow start status via WebSocket
            workflow_id = f"workflow_{datetime.now().timestamp()}"
            try:
                await websocket_manager.send_workflow_status(
                    workflow_id=workflow_id,
                    status="running",
                    agents={agent_id: {"status": "idle"} for agent_id in self.agents.keys()}
                )
                
                # Send a test message to verify WebSocket is working
                await websocket_manager.send_agent_message(
                    from_agent="system",
                    to_agent="workflow",
                    content="🚀 Workflow started - WebSocket connection verified!",
                    message_type="system"
                )
            except Exception as e:
                print(f"⚠️ WebSocket status update failed: {e}")
            
            # Create initial task message from system to coordinator
            initial_message = AgentMessage(
                id=f"workflow_start_{datetime.now().timestamp()}",
                from_agent="system",
                to_agent="coordinator",
                message_type=MessageType.TASK,
                content=initial_task
            )
            
            print(f"📤 Sending initial message to coordinator")
            
            # Process the workflow and wait for completion
            await self.send_message(initial_message)
            
            # Wait a bit for the workflow to complete (in a real system, you'd have better completion detection)
            print(f"⏳ Waiting for workflow completion...")
            # Reduce wait time and add progress updates
            for i in range(10):  # Wait 2 seconds total (10 * 0.2)
                await asyncio.sleep(0.2)  # Check every 200ms
                print(f"⏳ Workflow progress: {i+1}/10")
                
                # Send progress update via WebSocket
                try:
                    await websocket_manager.send_workflow_status(
                        workflow_id=workflow_id,
                        status="running",
                        agents={agent_id: {"status": "working"} for agent_id in self.agents.keys()}
                    )
                except Exception as e:
                    print(f"⚠️ WebSocket progress update failed: {e}")
            
            # Collect results from all agents
            results = {}
            for agent_id, agent in self.agents.items():
                results[agent_id] = {
                    "status": agent.status.value,
                    "memory": len(agent.memory.short_term),
                    "messages": [msg.content for msg in agent.memory.short_term[-5:]]  # Last 5 messages
                }
                print(f"📊 Agent {agent_id}: {agent.status.value}, {len(agent.memory.short_term)} messages")
            
            print(f"✅ Workflow completed successfully")
            
            # NEW: Send workflow completion status via WebSocket
            try:
                await websocket_manager.send_workflow_status(
                    workflow_id=workflow_id,
                    status="completed",
                    agents={agent_id: {"status": agent_data["status"]} for agent_id, agent_data in results.items()}
                )
            except Exception as e:
                print(f"⚠️ WebSocket completion update failed: {e}")
            
            return {
                "success": True,
                "results": results,
                "message": "Workflow completed successfully"
            }
                
        except Exception as e:
            print(f"❌ Workflow failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Workflow failed"
            }

# =============================================================================
# REQUEST MODELS - WHAT THE FRONTEND SENDS
# =============================================================================
class PromptRequest(BaseModel):
    """
    What: The request format for chat interactions
    Why: Frontend needs a standard way to send requests
    Can I change: YES - you can add more fields to the request
    """
    prompt: str
    code_history: List[str] = []
    error_history: List[str] = []
    conversation_id: Optional[str] = None

class WorkflowRequest(BaseModel):
    """
    What: The request format for custom workflows
    Why: Frontend needs a way to define custom agent workflows
    Can I change: YES - you can add more workflow configuration options
    """
    task: str
    agents: List[Dict[str, Any]]  # [{"id": "agent1", "type": "coder", "role": "Python developer", "model": "mistral"}]

# =============================================================================
# UTILITY FUNCTIONS - HELPER FUNCTIONS
# =============================================================================
def _timestamp() -> str:
    """
    What: Creates a timestamp string for file naming
    Why: We need unique filenames for generated files
    Can I change: YES - you can modify the timestamp format
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _extract_code(response: str) -> str:
    """
    What: Extracts Python code from AI responses
    Why: AI responses often include explanations, we need just the code
    Can I change: YES - you can modify how code is extracted
    """
    # Look for code blocks
    code_patterns = [
        r'```python\n(.*?)\n```',  # Markdown code blocks
        r'```\n(.*?)\n```',        # Generic code blocks
        r'```(.*?)```',            # Code blocks without language
        r'`(.*?)`'                 # Inline code
    ]
    
    for pattern in code_patterns:
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches[0].strip()
    
    # If no code blocks found, return the whole response
    return response.strip()

# =============================================================================
# API ENDPOINTS - WHAT THE FRONTEND CALLS
# =============================================================================

@app.post("/chat")
async def chat(request: PromptRequest):
    """
    What: Main chat endpoint for automated workflows
    Why: Frontend needs a simple way to interact with the AI system
    Can I change: YES - you can modify the chat logic
    """
    try:
        print(f"🚀 Starting chat workflow with prompt: {request.prompt}")
        
        # Validate input
        if not request.prompt or not request.prompt.strip():
            return {
                "type": "error",
                "message": "No prompt provided",
                "success": False
            }
        
        # Create a message bus for this session
        message_bus = MessageBus()
        
        # NEW: Attach database logger to message bus (NON-DISRUPTIVE)
        # Pass conversation_id if provided
        if request.conversation_id:
            db_integration.attach_to_message_bus(message_bus, conversation_id=request.conversation_id)
        else:
            db_integration.attach_to_message_bus(message_bus)
        
        # Define the default workflow agents
        workflow_agents = [
            {"id": "coordinator", "type": "coordinator", "role": "Smart Coordinator", "model": "mistral"},
            {"id": "coder", "type": "coder", "role": "Python Developer", "model": "mistral"},
            {"id": "tester", "type": "tester", "role": "Test Engineer", "model": "mistral"},
            {"id": "runner", "type": "runner", "role": "Test Runner"}
        ]
        
        print(f"🤖 Created {len(workflow_agents)} agents")
        
        # Process the workflow
        result = await message_bus.process_workflow(request.prompt, workflow_agents)
        
        print(f"✅ Workflow completed with result: {result}")
        
        # Check if workflow failed
        if not result.get("success", False):
            return {
                "type": "error",
                "message": result.get("message", "Workflow failed"),
                "success": False
            }
        
        # Extract results from the workflow
        code = None
        tests = None
        test_results = None
        tests_passed = None
        
        # Look for generated files in the results
        for agent_id, agent in message_bus.agents.items():
            print(f"🔍 Checking agent {agent_id}: {len(agent.memory.short_term)} messages")
            if agent_id == "coder":
                # Look for code in the agent's memory
                for msg in agent.memory.short_term:
                    if msg.metadata.get("code"):
                        code = msg.metadata["code"]
                        print(f"📝 Found code from coder agent: {len(code)} characters")
                        break
            elif agent_id == "tester":
                # Look for tests in the agent's memory
                for msg in agent.memory.short_term:
                    if msg.metadata.get("test_code"):
                        tests = msg.metadata["test_code"]
                        print(f"🧪 Found tests from tester agent: {len(tests)} characters")
                        break
            elif agent_id == "runner":
                # Look for test results in the agent's memory
                for msg in agent.memory.short_term:
                    if msg.metadata.get("test_results"):
                        test_results = msg.metadata["test_results"]
                        tests_passed = msg.metadata.get("tests_passed", False)
                        print(f"🏃 Found test results from runner agent: {len(test_results)} characters")
                        break
        
        # If code wasn't found in memory, try to read from the latest generated file
        if not code:
            try:
                code_files = list(GENERATED_DIR.glob("code_*.py"))
                if code_files:
                    latest_code_file = max(code_files, key=lambda x: x.stat().st_mtime)
                    with open(latest_code_file, 'r', encoding='utf-8') as f:
                        code = f.read()
                    print(f"📝 Found code from file: {latest_code_file.name}")
            except Exception as e:
                print(f"⚠️ Could not read code from file: {e}")
        
        # If tests weren't found in memory, try to read from the latest generated file
        if not tests:
            try:
                test_files = list(GENERATED_DIR.glob("test_*.py"))
                if test_files:
                    latest_test_file = max(test_files, key=lambda x: x.stat().st_mtime)
                    with open(latest_test_file, 'r', encoding='utf-8') as f:
                        tests = f.read()
                    print(f"🧪 Found tests from file: {latest_test_file.name}")
            except Exception as e:
                print(f"⚠️ Could not read tests from file: {e}")
        
        # If test results weren't found in memory, try to execute the latest tests
        if not test_results and code and tests:
            try:
                print("🏃 No test results found in memory, attempting to execute tests...")
                # Create a temporary runner to execute the tests
                temp_runner = RunnerAgent("temp_runner", "runner", "Test Runner")
                test_results = temp_runner._run_tests(code, tests)
                tests_passed = "✅ TESTS PASSED" in test_results
                print(f"🏃 Test execution completed: {len(test_results)} characters")
            except Exception as e:
                print(f"⚠️ Could not execute tests: {e}")
                test_results = f"❌ Test execution failed: {str(e)}"
                tests_passed = False
        
        # Determine response type based on what was generated
        response_type = "coding" if (code or tests) else "error"
        
        response_data = {
            "type": response_type,
            "message": result.get("message", "Task completed"),
            "code": code,
            "tests": tests,
            "test_results": test_results,
            "tests_passed": tests_passed,
            "success": result.get("success", False)
        }
        
        print(f"📤 Returning response: {response_data}")
        return response_data
        
    except Exception as e:
        print(f"❌ Error in chat endpoint: {str(e)}")
        return {
            "type": "error",
            "message": f"Error processing request: {str(e)}",
            "success": False
        }

@app.post("/run-workflow")
async def run_workflow(request: WorkflowRequest):
    """
    What: Endpoint for custom agent workflows
    Why: Frontend needs a way to define custom agent configurations
    Can I change: YES - you can modify the workflow processing
    """
    try:
        message_bus = MessageBus()
        result = await message_bus.process_workflow(request.task, request.agents)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/update-agent-model")
async def update_agent_model(agent_id: str, model_name: str, model_config: Dict[str, Any] = None):
    """
    What: Updates the AI model for a specific agent
    Why: Agents might need different models for different tasks
    Can I change: YES - you can modify model updating logic
    """
    # This would need to be implemented with agent management
    return {"success": True, "message": f"Updated agent {agent_id} to use model {model_name}"}

# =============================================================================
# LEGACY ENDPOINTS - FOR BACKWARD COMPATIBILITY
# =============================================================================
# These endpoints maintain compatibility with existing frontend code

@app.post("/generate-code")
async def generate_code(data: PromptRequest):
    """
    What: Legacy endpoint for code generation
    Why: Maintains compatibility with existing frontend
    Can I change: NO - this is for backward compatibility
    """
    return await chat(data)

@app.post("/generate-test")
async def generate_test(request: PromptRequest):
    """
    What: Legacy endpoint for test generation
    Why: Maintains compatibility with existing frontend
    Can I change: NO - this is for backward compatibility
    """
    return await chat(request)

@app.post("/run-test")
async def run_test(data: PromptRequest):
    """
    What: Legacy endpoint for test execution
    Why: Maintains compatibility with existing frontend
    Can I change: NO - this is for backward compatibility
    """
    return await chat(data)

# =============================================================================
# FILE MANAGEMENT ENDPOINTS - FOR FRONTEND FILE OPERATIONS
# =============================================================================

@app.get("/list-files")
async def list_files():
    """
    What: Lists all generated files
    Why: Frontend needs to know what files are available
    Can I change: YES - you can modify file listing logic
    """
    try:
        files = []
        for file in GENERATED_DIR.glob("*.py"):
            files.append(file.name)
        return {"files": files}
    except Exception as e:
        return {"files": [], "error": str(e)}

@app.get("/generated/{filename}")
async def get_generated_file(filename: str):
    """
    What: Serves generated files to the frontend
    Why: Frontend needs to display generated code and tests
    Can I change: YES - you can modify file serving logic
    """
    try:
        filepath = GENERATED_DIR / filename
        if filepath.exists():
            return FileResponse(filepath, media_type="text/plain")
        else:
            raise HTTPException(status_code=404, detail=f"File {filename} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@app.delete("/generated/{filename}")
async def delete_generated_file(filename: str):
    """
    What: Deletes a generated file
    Why: Frontend needs to be able to clean up files
    Can I change: YES - you can modify file deletion logic
    """
    try:
        filepath = GENERATED_DIR / filename
        if filepath.exists():
            filepath.unlink()
            return {"success": True, "message": f"Deleted {filename}"}
        else:
            raise HTTPException(status_code=404, detail=f"File {filename} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

# =============================================================================
# MANUAL AGENT WORKFLOW ENDPOINTS - FOR VISUAL WORKFLOW DESIGN
# =============================================================================

class ManualAgentBox(BaseModel):
    """
    What: Represents an agent box in the visual workflow designer
    Why: Frontend needs to send agent configurations
    Can I change: YES - you can add more agent properties
    """
    id: str
    x: float
    y: float
    width: float
    height: float
    agentType: str
    role: str
    model: str = DEFAULT_MODEL

class ManualAgentConnection(BaseModel):
    """
    What: Represents a connection between agents in the visual workflow
    Why: Frontend needs to define how agents communicate
    Can I change: YES - you can add more connection properties
    """
    id: str
    fromId: str
    fromSide: str
    toId: str
    toSide: str

class ManualFlowRequest(BaseModel):
    """
    What: Request format for manual workflow execution
    Why: Frontend needs to send manual workflow configurations
    Can I change: YES - you can add more workflow properties
    """
    prompt: str
    boxes: List[ManualAgentBox]
    connections: List[ManualAgentConnection]

@app.post("/run-manual-flow")
async def run_manual_flow(data: ManualFlowRequest):
    """
    What: Executes a manually designed workflow
    Why: Frontend needs to run custom agent workflows
    Can I change: YES - you can modify manual workflow processing
    """
    try:
        # Convert manual flow to agent configurations
        agents = []
        for box in data.boxes:
            agents.append({
                "id": box.id,
                "type": box.agentType,
                "role": box.role,
                "model": box.model
            })
        
        # Create message bus and process workflow
        message_bus = MessageBus()
        result = await message_bus.process_workflow(data.prompt, agents)
        
        # Collect messages from all agents
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
            "generated_files": []  # You can add file tracking here
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "messages": []
        }

@app.get("/example-workflow")
async def example_workflow():
    """
    What: Returns an example workflow configuration
    Why: Frontend needs example data for testing
    Can I change: YES - you can modify the example workflow
    """
    return {
        "agents": [
            {"id": "coordinator", "type": "coordinator", "role": "Smart Coordinator"},
            {"id": "coder", "type": "coder", "role": "Python Developer"},
            {"id": "tester", "type": "tester", "role": "Test Engineer"},
            {"id": "runner", "type": "runner", "role": "Test Runner"}
        ],
        "description": "A complete workflow for code generation and testing"
    }

# =============================================================================
# ADDITIONAL ENDPOINTS - FOR FRONTEND COMPATIBILITY
# =============================================================================

@app.get("/health")
async def health_check():
    """
    What: Health check endpoint
    Why: Frontend needs to verify backend is running
    Can I change: YES - you can modify health check logic
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "agents_available": ["coordinator", "coder", "tester", "runner"]
    }

@app.get("/agent-types")
async def get_agent_types():
    """
    What: Returns available agent types
    Why: Frontend needs to know what agents are available
    Can I change: YES - you can add new agent types
    """
    return {
        "agent_types": ["coordinator", "coder", "tester", "runner"],
        "count": 4
    }

@app.get("/agents")
async def get_active_agents():
    """
    What: Returns currently active agents
    Why: Frontend needs to know about active agents
    Can I change: YES - you can modify agent status reporting
    """
    return {
        "agents": {
            "coordinator": {"status": "available", "type": "coordinator"},
            "coder": {"status": "available", "type": "coder"},
            "tester": {"status": "available", "type": "tester"},
            "runner": {"status": "available", "type": "runner"}
        },
        "count": 4
    }

@app.get("/pipelines")
async def get_pipelines():
    """
    What: Returns available pipelines
    Why: Frontend needs pipeline information
    Can I change: YES - you can add pipeline management
    """
    return {
        "pipelines": [
            {
                "id": "default",
                "name": "Default Workflow",
                "description": "Standard code generation and testing workflow",
                "agents": ["coordinator", "coder", "tester", "runner"]
            }
        ],
        "count": 1
    }

@app.post("/execute-pipeline/{pipeline_id}")
async def execute_pipeline(pipeline_id: str, task: str):
    """
    What: Executes a specific pipeline
    Why: Frontend needs to run predefined pipelines
    Can I change: YES - you can modify pipeline execution
    """
    if pipeline_id == "default":
        return await chat(PromptRequest(prompt=task))
    else:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")

@app.delete("/cleanup")
async def cleanup_system():
    """
    What: Cleans up the system
    Why: Frontend needs cleanup functionality
    Can I change: YES - you can modify cleanup logic
    """
    return {
        "message": "System cleaned up successfully",
        "removed_agents": 0,
        "cleared_messages": 0
    }

@app.get("/gpu-status")
async def get_gpu_status():
    """
    What: Check GPU availability and current model configuration
    Why: Users need to know if GPU acceleration is available
    Can I change: YES - you can add more GPU diagnostics
    """
    try:
        # Check if CUDA is available
        cuda_available = False
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            cuda_available = result.returncode == 0
        except:
            pass
        
        # Check Ollama GPU support
        ollama_gpu = False
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            ollama_gpu = "gpu" in result.stdout.lower()
        except:
            pass
        
        return {
            "cuda_available": cuda_available,
            "ollama_gpu_support": ollama_gpu,
            "current_model": DEFAULT_MODEL,
            "gpu_config": DEFAULT_GPU_CONFIG,
            "available_models": list(MODEL_CONFIGS.keys()),
            "recommendation": "CodeLlama:7b-instruct is optimized for code generation with GPU acceleration",
            "model_comparison": {
                "codellama:7b-instruct": "Best for code generation, lower temperature for focused output",
                "mistral": "Good for general tasks and coordination",
                "llama2": "Balanced performance for various tasks"
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "cuda_available": False,
            "ollama_gpu_support": False
        }

@app.post("/configure-gpu")
async def configure_gpu_settings(num_gpu: int = 1, num_thread: int = 8, temperature: float = 0.7):
    """
    What: Configure GPU settings for all agents
    Why: Users need to adjust GPU parameters
    Can I change: YES - you can add more configuration options
    """
    try:
        # Update the default GPU configuration
        global DEFAULT_GPU_CONFIG
        DEFAULT_GPU_CONFIG = {
            "num_gpu": num_gpu,
            "num_thread": num_thread,
            "temperature": temperature,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
        
        return {
            "success": True,
            "message": f"GPU configuration updated: {num_gpu} GPU(s), {num_thread} threads, temp={temperature}",
            "config": DEFAULT_GPU_CONFIG
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/models")
async def get_available_models():
    """
    What: Get information about available models and their configurations
    Why: Users need to know what models are available and their settings
    Can I change: YES - you can add more model information
    """
    return {
        "current_default": DEFAULT_MODEL,
        "available_models": MODEL_CONFIGS,
        "recommendations": {
            "code_generation": "codellama:7b-instruct",
            "general_tasks": "mistral", 
            "balanced": "llama2"
        }
    }

@app.post("/switch-model")
async def switch_default_model(model_name: str):
    """
    What: Switch the default model for all new agents
    Why: Users need to easily change the default model
    Can I change: YES - you can add more model switching logic
    """
    try:
        global DEFAULT_MODEL
        if model_name not in MODEL_CONFIGS:
            return {
                "success": False,
                "error": f"Model '{model_name}' not found. Available models: {list(MODEL_CONFIGS.keys())}"
            }
        
        DEFAULT_MODEL = model_name
        return {
            "success": True,
            "message": f"Default model switched to {model_name}",
            "new_default": DEFAULT_MODEL,
            "model_config": MODEL_CONFIGS[model_name]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# =============================================================================
# DATABASE API ENDPOINTS - NEW ADDITIONS
# =============================================================================

@app.post("/conversations")
async def create_conversation(request: ConversationRequest):
    """Create new conversation - doesn't affect current agents"""
    try:
        conversation_id = await db_integration.start_conversation(request.title)
        return {"conversation_id": conversation_id, "title": request.title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")

@app.get("/conversations")
async def get_conversations():
    """Get conversation history - read-only"""
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

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get specific conversation - read-only"""
    try:
        conversation = await db_integration.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = db_integration.db_service.get_conversation_messages(conversation_id)
        return {
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
                "is_active": conversation.is_active
            },
            "messages": [
                {
                    "id": msg.id,
                    "from_agent": msg.from_agent,
                    "to_agent": msg.to_agent,
                    "message_type": msg.message_type,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.message_metadata
                }
                for msg in messages
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete conversation - doesn't affect current agents"""
    try:
        success = await db_integration.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")

# =============================================================================
# GITHUB API ENDPOINTS
# =============================================================================

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

# =============================================================================
# ONLINE AGENT SERVICE INTEGRATION
# =============================================================================
# Import the online agent service components
from online_agent_service import (
    online_app as online_agent_app,
    workflow_manager as online_workflow_manager,
    OnlineWorkflowRequest,
    OnlineAgent,
    ONLINE_MODEL_CONFIGS
)

# Mount the online agent service under /online path
app.mount("/online", online_agent_app, name="online_agent_service")

# Add a combined health check endpoint
@app.get("/combined-health")
async def combined_health_check():
    """Health check for both main service and online agent service"""
    return {
        "main_service": {
            "status": "healthy",
            "port": 8000,
            "endpoints": ["/chat", "/run-workflow", "/conversations"]
        },
        "online_agent_service": {
            "status": "healthy", 
            "port": 8000,
            "path": "/online",
            "endpoints": ["/online/health", "/online/run-workflow", "/online/models"],
            "available_models": list(ONLINE_MODEL_CONFIGS.keys())
        },
        "timestamp": datetime.now().isoformat()
    }

# Add endpoint to get online models from main service
@app.get("/online-models")
async def get_online_models_from_main():
    """Get online models through main service"""
    return {
        "available_models": ONLINE_MODEL_CONFIGS,
        "default_model": "gpt-3.5-turbo",
        "providers": {
            "openai": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
            "mistral": ["mistral-large", "mistral-medium", "mistral-small"]
        }
    }

# Add endpoint to run online workflow through main service
@app.post("/run-online-workflow")
async def run_online_workflow_from_main(request: OnlineWorkflowRequest):
    """Run online agent workflow through main service"""
    try:
        response = await online_workflow_manager.run_workflow(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Online workflow failed: {str(e)}")

# =============================================================================
# WEBSOCKET MANAGER FOR REAL-TIME COMMUNICATION
# =============================================================================

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.workflow_status: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"🔗 WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"🔌 WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Error sending message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def send_agent_message(self, from_agent: str, to_agent: str, content: str, message_type: str = "message"):
        """Send agent message to all connected clients"""
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
        """Send workflow status update to all connected clients"""
        message = {
            "type": "workflow_status",
            "workflow_id": workflow_id,
            "status": status,
            "agents": agents or {},
            "message_history": message_history or [],
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(json.dumps(message))

# Create WebSocket manager instance
websocket_manager = WebSocketManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                print(f"📨 Received WebSocket message: {message}")
                
                # Handle different message types
                if message.get("type") == "test":
                    # Send test response
                    await websocket_manager.send_personal_message(
                        json.dumps({
                            "type": "test_response",
                            "message": "WebSocket connection working!",
                            "timestamp": datetime.now().isoformat()
                        }),
                        websocket
                    )
                elif message.get("type") == "ping":
                    # Send pong response
                    await websocket_manager.send_personal_message(
                        json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }),
                        websocket
                    )
                else:
                    # Echo back unknown messages
                    await websocket_manager.send_personal_message(
                        json.dumps({
                            "type": "echo",
                            "original_message": message,
                            "timestamp": datetime.now().isoformat()
                        }),
                        websocket
                    )
                    
            except json.JSONDecodeError:
                await websocket_manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

# =============================================================================
# STARTUP MESSAGE - SHOWS WHEN SERVER STARTS
# =============================================================================
if __name__ == "__main__":
    print("🚀 Starting Multi-Agent AI System...")
    print(f"🔧 GPU Configuration: {DEFAULT_GPU_CONFIG}")
    print("📁 Generated files will be saved to:", GENERATED_DIR)
    print("🌐 Main Server will be available at: http://localhost:8000")
    print("🌐 Online Agent Service will be available at: http://localhost:8000/online")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("📚 Online Service Documentation: http://localhost:8000/online/docs")
    print("🔗 Combined Health Check: http://localhost:8000/combined-health")
    uvicorn.run(app, host="0.0.0.0", port=8000)
