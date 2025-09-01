# =============================================================================
# ONLINE AGENT SERVICE WITH LANGCHAIN INTEGRATION
# =============================================================================
# This service provides online model integration for manual agent workflows
# It uses LangChain for conversation tracking and online models (OpenAI, Anthropic, etc.)

import os
import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# LangChain imports for online models and conversation tracking
from langchain_openai import ChatOpenAI
from langchain_mistralai import ChatMistralAI
# Try to import Gemini, fallback gracefully if not available
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: Gemini integration not available. Install with: pip install langchain-google-genai google-generativeai")
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.callbacks.manager import CallbackManager

# Database integration (reusing existing structure)
from database import SafeDatabaseIntegration, ConversationRequest, ConversationResponse

# =============================================================================
# CONFIGURATION
# =============================================================================

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# API Keys - Set these in environment variables or .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model configurations
ONLINE_MODEL_CONFIGS = {
    "gpt-4": {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.3,
        "max_tokens": 4000,
        "streaming": True
    },
    "gpt-3.5-turbo": {
        "provider": "openai", 
        "model": "gpt-3.5-turbo",
        "temperature": 0.3,
        "max_tokens": 4000,
        "streaming": True
    },
    "gpt-4-turbo": {
        "provider": "openai",
        "model": "gpt-4-turbo-preview",
        "temperature": 0.3,
        "max_tokens": 4000,
        "streaming": True
    },
    "mistral-large": {
        "provider": "mistral",
        "model": "mistral-large-latest",
        "temperature": 0.3,
        "max_tokens": 4000,
        "streaming": True
    },
    "mistral-medium": {
        "provider": "mistral",
        "model": "mistral-medium-latest",
        "temperature": 0.3,
        "max_tokens": 4000,
        "streaming": True
    },
    "mistral-small": {
        "provider": "mistral",
        "model": "mistral-small-latest",
        "temperature": 0.3,
        "max_tokens": 4000,
        "streaming": True
    },
    "gemini-pro": {
        "provider": "gemini",
        "model": "gemini-pro",
        "temperature": 0.3,
        "max_tokens": 4000,
        "streaming": True
    },
    "gemini-pro-vision": {
        "provider": "gemini",
        "model": "gemini-pro-vision",
        "temperature": 0.3,
        "max_tokens": 4000,
        "streaming": True
    }
}

# Default model
DEFAULT_ONLINE_MODEL = "gemini-pro" if GEMINI_AVAILABLE else "mistral-small"

# =============================================================================
# DATA MODELS
# =============================================================================

class MessageType(Enum):
    """Message types for agent communication"""
    TASK = "task"
    DATA = "data" 
    REQUEST = "request"
    RESPONSE = "response"
    COORDINATION = "coordination"
    ERROR = "error"
    STATUS = "status"
    REVIEW = "review"

class OnlineAgentMessage(BaseModel):
    """Message structure for online agent communication"""
    id: str = Field(default_factory=lambda: f"msg_{datetime.now().timestamp()}")
    from_agent: str
    to_agent: str
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)
    conversation_id: Optional[str] = None

class OnlineAgent(BaseModel):
    """Online agent configuration"""
    id: str
    name: str
    role: str
    model: str = DEFAULT_ONLINE_MODEL
    system_prompt: str = ""
    memory_enabled: bool = True
    conversation_id: Optional[str] = None

class OnlineAgentStatus(Enum):
    """Agent status tracking"""
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"

class OnlineWorkflowRequest(BaseModel):
    """Request for running online agent workflow"""
    task: str
    agents: List[OnlineAgent]
    conversation_id: Optional[str] = None
    enable_streaming: bool = True

class OnlineWorkflowResponse(BaseModel):
    """Response from online agent workflow"""
    workflow_id: str
    status: str
    agents: Dict[str, OnlineAgentStatus]
    message_history: List[OnlineAgentMessage]
    total_messages: int
    conversation_id: str

# =============================================================================
# LANGCHAIN AGENT MANAGER
# =============================================================================

class LangChainAgentManager:
    """Manages LangChain agents with conversation tracking"""
    
    def __init__(self):
        self.agents: Dict[str, 'OnlineAgentInstance'] = {}
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.workflow_history: Dict[str, List[OnlineAgentMessage]] = {}
        
    def create_agent(self, agent_config: OnlineAgent) -> 'OnlineAgentInstance':
        """Create a new LangChain agent instance"""
        agent = OnlineAgentInstance(agent_config)
        self.agents[agent_config.id] = agent
        return agent
    
    def get_agent(self, agent_id: str) -> Optional['OnlineAgentInstance']:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def create_conversation_memory(self, conversation_id: str) -> Dict[str, Any]:
        """Create conversation memory for tracking"""
        memory = {
            "messages": [],
            "conversation_id": conversation_id
        }
        self.conversations[conversation_id] = memory
        return memory
    
    def add_message_to_history(self, workflow_id: str, message: OnlineAgentMessage):
        """Add message to workflow history"""
        if workflow_id not in self.workflow_history:
            self.workflow_history[workflow_id] = []
        self.workflow_history[workflow_id].append(message)

# =============================================================================
# ONLINE AGENT INSTANCE
# =============================================================================

class OnlineAgentInstance:
    """Individual online agent with LangChain integration"""
    
    def __init__(self, config: OnlineAgent):
        self.config = config
        self.status = OnlineAgentStatus.IDLE
        self.llm = self._create_llm()
        self.memory = []
        
        if config.memory_enabled:
            self.memory = []
    
    def _create_llm(self):
        """Create LangChain LLM based on configuration"""
        model_config = ONLINE_MODEL_CONFIGS.get(self.config.model, ONLINE_MODEL_CONFIGS[DEFAULT_ONLINE_MODEL])
        
        if model_config["provider"] == "openai":
            if not OPENAI_API_KEY:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
            
            return ChatOpenAI(
                model=model_config["model"],
                temperature=model_config["temperature"],
                max_tokens=model_config["max_tokens"],
                streaming=model_config["streaming"],
                openai_api_key=OPENAI_API_KEY
            )
        
        elif model_config["provider"] == "mistral":
            if not MISTRAL_API_KEY:
                raise ValueError("Mistral API key not found. Set MISTRAL_API_KEY environment variable.")
            
            return ChatMistralAI(
                model=model_config["model"],
                temperature=model_config["temperature"],
                max_tokens=model_config["max_tokens"],
                streaming=model_config["streaming"],
                mistral_api_key=MISTRAL_API_KEY
            )
        
        elif model_config["provider"] == "gemini":
            if not GEMINI_AVAILABLE:
                raise ImportError("Gemini integration not available. Install with: pip install langchain-google-genai google-generativeai")
            if not GEMINI_API_KEY:
                raise ValueError("Gemini API key not found. Set GEMINI_API_KEY environment variable.")
            
            return ChatGoogleGenerativeAI(
                model=model_config["model"],
                temperature=model_config["temperature"],
                max_tokens=model_config["max_tokens"],
                streaming=model_config["streaming"],
                google_api_key=GEMINI_API_KEY
            )
        
        else:
            raise ValueError(f"Unsupported provider: {model_config['provider']}")
    
    async def process_message(self, message: OnlineAgentMessage, conversation_memory: Optional[Dict[str, Any]] = None) -> str:
        """Process incoming message and return response"""
        try:
            self.status = OnlineAgentStatus.WORKING
            
            # Prepare enhanced system prompt for coordination
            coordination_instructions = """
            IMPORTANT: You are part of a multi-agent workflow. When responding:
            1. Be specific about your role and what you can contribute
            2. If you're a coordinator, explain the plan and delegate tasks
            3. If you're a coder, write code and explain what you've implemented
            4. If you're a tester, validate code and provide feedback
            5. If you're a runner, execute the code and report results
            6. Use clear, actionable language
            7. Don't just say "hi" - provide value based on your role
            8. If you're done with your part, mention what should happen next
            """
            
            system_content = f"You are {self.config.name}, a {self.config.role}. {self.config.system_prompt}\n\n{coordination_instructions}"
            
            # Create messages for LangChain
            messages = [SystemMessage(content=system_content)]
            
            # Add conversation history if available
            if conversation_memory and "messages" in conversation_memory:
                messages.extend(conversation_memory["messages"])
            
            # Add current message with context
            message_context = f"Message from {message.from_agent}: {message.content}"
            messages.append(HumanMessage(content=message_context))
            
            # Get response from LLM
            response = await self.llm.agenerate([messages])
            response_content = response.generations[0][0].text
            
            # Add to memory
            if conversation_memory and "messages" in conversation_memory:
                conversation_memory["messages"].extend([
                    HumanMessage(content=message_context),
                    AIMessage(content=response_content)
                ])
            
            self.status = OnlineAgentStatus.COMPLETED
            return response_content
            
        except Exception as e:
            self.status = OnlineAgentStatus.ERROR
            logging.error(f"Error processing message in agent {self.config.id}: {str(e)}")
            return f"Error: {str(e)}"
    
    def get_status(self) -> OnlineAgentStatus:
        """Get current agent status"""
        return self.status

# =============================================================================
# ONLINE WORKFLOW MANAGER
# =============================================================================

class OnlineWorkflowManager:
    """Manages online agent workflows with LangChain integration"""
    
    def __init__(self):
        self.agent_manager = LangChainAgentManager()
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.db_integration = SafeDatabaseIntegration()
    
    async def run_workflow(self, request: OnlineWorkflowRequest) -> OnlineWorkflowResponse:
        """Run a complete workflow with online agents"""
        workflow_id = f"workflow_{datetime.now().timestamp()}"
        
        # Create conversation if needed (only for non-manual flows)
        conversation_id = request.conversation_id
        if conversation_id is None:  # Explicitly None/undefined - don't create DB conversation
            conversation_id = f"manual_workflow_{workflow_id}"  # Use internal ID only
        elif not conversation_id:  # Empty string - create DB conversation
            conversation_id = await self.db_integration.start_conversation(f"Online Workflow: {request.task}")
        
        # Initialize workflow
        self.active_workflows[workflow_id] = {
            "status": "running",
            "agents": {},
            "message_history": [],
            "conversation_id": conversation_id
        }
        
        # Create agents
        agents = {}
        for agent_config in request.agents:
            agent = self.agent_manager.create_agent(agent_config)
            agents[agent_config.id] = agent
            self.active_workflows[workflow_id]["agents"][agent_config.id] = OnlineAgentStatus.IDLE
        
        # Create conversation memory
        conversation_memory = self.agent_manager.create_conversation_memory(conversation_id)
        
        # Start workflow execution
        try:
            # Find coordinator agent or use first agent
            coordinator = next((agent for agent in agents.values() if "coordinator" in agent.config.role.lower()), 
                             list(agents.values())[0])
            
            # Send initial task to coordinator
            initial_message = OnlineAgentMessage(
                from_agent="system",
                to_agent=coordinator.config.id,
                message_type=MessageType.TASK,
                content=request.task,
                conversation_id=conversation_id
            )
            
            # Process workflow
            await self._execute_workflow(workflow_id, agents, initial_message, conversation_memory)
            
            # Update final status
            self.active_workflows[workflow_id]["status"] = "completed"
            
        except Exception as e:
            self.active_workflows[workflow_id]["status"] = "error"
            logging.error(f"Workflow error: {str(e)}")
        
        # Return response
        return OnlineWorkflowResponse(
            workflow_id=workflow_id,
            status=self.active_workflows[workflow_id]["status"],
            agents={agent_id: agent.get_status() for agent_id, agent in agents.items()},
            message_history=self.active_workflows[workflow_id]["message_history"],
            total_messages=len(self.active_workflows[workflow_id]["message_history"]),
            conversation_id=conversation_id
        )
    
    async def _execute_workflow(self, workflow_id: str, agents: Dict[str, OnlineAgentInstance], 
                              initial_message: OnlineAgentMessage, conversation_memory: Dict[str, Any]):
        """Execute the workflow step by step with multi-agent coordination"""
        current_message = initial_message
        max_iterations = 20
        iteration = 0
        agent_roles = {agent_id: agent.config.role.lower() for agent_id, agent in agents.items()}
        
        while iteration < max_iterations:
            # Add message to history
            self.active_workflows[workflow_id]["message_history"].append(current_message)
            self.agent_manager.add_message_to_history(workflow_id, current_message)
            
            # Save to database (only for non-manual workflows)
            if not current_message.conversation_id.startswith("manual_workflow_"):
                await self.db_integration.add_message_to_conversation(
                    current_message.conversation_id,
                    current_message.from_agent,
                    current_message.to_agent,
                    current_message.message_type.value,
                    current_message.content,
                    current_message.metadata
                )
            
            # Get target agent
            target_agent = agents.get(current_message.to_agent)
            if not target_agent:
                break
            
            # Update agent status
            self.active_workflows[workflow_id]["agents"][current_message.to_agent] = OnlineAgentStatus.WORKING
            
            # Process message
            response_content = await target_agent.process_message(current_message, conversation_memory)
            
            # Check if workflow is complete
            if "workflow complete" in response_content.lower() or "task completed" in response_content.lower():
                break
            
            # Simple routing logic - always route to next agent in sequence
            agent_ids = list(agent_roles.keys())
            try:
                current_index = agent_ids.index(current_message.to_agent)
                next_index = (current_index + 1) % len(agent_ids)
                next_agent = agent_ids[next_index]
                
                # Create message to next agent
                next_message = OnlineAgentMessage(
                    from_agent=current_message.to_agent,
                    to_agent=next_agent,
                    message_type=MessageType.COORDINATION,
                    content=f"Message from {current_message.to_agent}: {response_content}",
                    conversation_id=current_message.conversation_id
                )
                current_message = next_message
                
            except ValueError:
                break
            
            iteration += 1

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

# Create FastAPI app for online agent service
online_app = FastAPI(
    title="Online Agent Service",
    description="Online model integration for manual agent workflows with LangChain",
    version="1.0.0"
)

# Add CORS middleware
online_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize workflow manager
workflow_manager = OnlineWorkflowManager()

# =============================================================================
# API ENDPOINTS
# =============================================================================

@online_app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Online Agent Service",
        "version": "1.0.0",
        "description": "Online model integration with LangChain for manual agent workflows",
        "endpoints": {
            "health": "/health",
            "models": "/models",
            "workflow": "/run-workflow",
            "conversations": "/conversations",
            "workflow-status": "/workflow-status/{workflow_id}"
        }
    }

@online_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "online_agent_service",
        "timestamp": datetime.now().isoformat(),
        "available_models": list(ONLINE_MODEL_CONFIGS.keys())
    }

@online_app.get("/models")
async def get_online_models():
    """Get available online models"""
    return {
        "available_models": ONLINE_MODEL_CONFIGS,
        "default_model": DEFAULT_ONLINE_MODEL,
        "providers": {
            "openai": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
            "mistral": ["mistral-large", "mistral-medium", "mistral-small"],
            "gemini": ["gemini-pro", "gemini-pro-vision"]
        }
    }

@online_app.post("/run-workflow")
async def run_online_workflow(request: OnlineWorkflowRequest):
    """Run online agent workflow"""
    # Validate request
    if not request.task or not request.task.strip():
        raise HTTPException(status_code=422, detail="Task cannot be empty")
    
    if not request.agents or len(request.agents) == 0:
        raise HTTPException(status_code=422, detail="At least one agent must be specified")
    
    # Check if required API keys are available
    required_providers = set()
    for agent in request.agents:
        model_config = ONLINE_MODEL_CONFIGS.get(agent.model, ONLINE_MODEL_CONFIGS[DEFAULT_ONLINE_MODEL])
        required_providers.add(model_config["provider"])
    
    missing_keys = []
    if "openai" in required_providers and not OPENAI_API_KEY:
        missing_keys.append("OPENAI_API_KEY")
    if "mistral" in required_providers and not MISTRAL_API_KEY:
        missing_keys.append("MISTRAL_API_KEY")
    if "gemini" in required_providers and not GEMINI_API_KEY:
        missing_keys.append("GEMINI_API_KEY")
    
    if missing_keys:
        raise HTTPException(
            status_code=400, 
            detail=f"Missing required API keys: {', '.join(missing_keys)}. Please set the environment variables."
        )
    
    try:
        response = await workflow_manager.run_workflow(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@online_app.get("/workflow-status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get workflow status"""
    workflow = workflow_manager.active_workflows.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {
        "workflow_id": workflow_id,
        "status": workflow["status"],
        "agents": workflow["agents"],
        "message_count": len(workflow["message_history"]),
        "conversation_id": workflow["conversation_id"]
    }

@online_app.get("/conversations")
async def get_online_conversations():
    """Get conversation history"""
    try:
        conversations = await workflow_manager.db_integration.get_conversations()
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

@online_app.get("/conversations/{conversation_id}")
async def get_online_conversation(conversation_id: str):
    """Get specific conversation"""
    try:
        conversation = await workflow_manager.db_integration.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = workflow_manager.db_integration.db_service.get_conversation_messages(conversation_id)
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

# =============================================================================
# STARTUP
# =============================================================================

if __name__ == "__main__":
    print("🚀 Starting Online Agent Service...")
    print("🔗 LangChain integration enabled")
    print("🌐 Online models available:", list(ONLINE_MODEL_CONFIGS.keys()))
    print("📚 API Documentation: http://localhost:8001/docs")
    print("⚠️  Make sure to set OPENAI_API_KEY, MISTRAL_API_KEY, and GEMINI_API_KEY environment variables")
    
    uvicorn.run(online_app, host="0.0.0.0", port=8001)

