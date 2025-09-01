/**
 * API Service for Multi-Agent System
 * 
 * This service handles all communication with the backend multi-agent system.
 * It provides a unified interface for all agent interactions and workflow management.
 */

const API_BASE_URL = 'http://localhost:8000';

export interface ChatRequest {
  prompt: string;
  code_history?: string[];
  error_history?: string[];
  conversation_id?: string;
}

export interface ChatResponse {
  type: 'coding' | 'error';
  message: string;
  code?: string;
  tests?: string;
  test_results?: string;
  tests_passed?: boolean;
  files_created?: string[];
  workflow_result?: any;
  success?: boolean;
}

export interface WorkflowRequest {
  task: string;
  agents: Array<{
    id: string;
    type: string;
    role: string;
    model?: string;
    model_config?: any;
  }>;
}

export interface WorkflowResponse {
  success: boolean;
  results?: any;
  message: string;
  error?: string;
}

export interface AgentMessage {
  id: string;
  from_agent: string;
  to_agent: string;
  message_type: 'task' | 'data' | 'request' | 'response' | 'error' | 'status';
  content: string;
  metadata?: any;
  timestamp: string;
}

export interface AgentStatus {
  agent_id: string;
  status: 'idle' | 'working' | 'waiting' | 'completed' | 'error';
  memory_size: number;
}

export interface WorkflowResult {
  workflow_id: string;
  status: string;
  agents: Record<string, AgentStatus>;
  message_history: AgentMessage[];
  total_messages: number;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ConversationMessage {
  id: string;
  from_agent: string;
  to_agent: string;
  message_type: string;
  content: string;
  timestamp: string;
  metadata: any;
}

export interface ConversationDetail {
  conversation: {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
    is_active: boolean;
  };
  messages: ConversationMessage[];
}

/**
 * Test backend connection
 */
export async function testBackendConnection(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (response.ok) {
      const data = await response.json();
      console.log('Backend connection test passed:', data);
      return true;
    } else {
      console.error('Backend connection test failed:', response.status);
      return false;
    }
  } catch (error) {
    console.error('Backend connection test error:', error);
    return false;
  }
}

/**
 * Main chat endpoint - uses the new multi-agent system
 */
export async function chatWithAgents(request: ChatRequest): Promise<ChatResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Chat request failed: ${response.status} - ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Chat API error:', error);
    throw error;
  }
}

/**
 * Run a custom workflow with specific agents
 */
export async function runWorkflow(request: WorkflowRequest): Promise<WorkflowResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/run-workflow`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Workflow request failed: ${response.status} - ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Workflow API error:', error);
    throw error;
  }
}

/**
 * Update an agent's model
 */
export async function updateAgentModel(agentId: string, modelName: string, modelConfig?: any): Promise<{ message: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/update-agent-model`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        agent_id: agentId,
        model_name: modelName,
        model_config: modelConfig
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to update agent model: ${response.status} - ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Update agent model API error:', error);
    throw error;
  }
}

/**
 * Get list of generated files
 */
export async function getGeneratedFiles(): Promise<{ files: string[] }> {
  try {
    const response = await fetch(`${API_BASE_URL}/list-files`);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to get files: ${response.status} - ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Get files API error:', error);
    throw error;
  }
}

/**
 * Get file content
 */
export async function getFileContent(filename: string): Promise<string> {
  try {
    const response = await fetch(`${API_BASE_URL}/generated/${filename}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to get file content: ${response.status} - ${errorText}`);
    }

    return await response.text();
  } catch (error) {
    console.error('Get file content API error:', error);
    throw error;
  }
}

/**
 * Delete a generated file
 */
export async function deleteGeneratedFile(filename: string): Promise<{ success: boolean; message: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/generated/${filename}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to delete file: ${response.status} - ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Delete file API error:', error);
    throw error;
  }
}

/**
 * Run manual workflow
 */
export async function runManualFlow(prompt: string, boxes: any[], connections: any[]): Promise<any> {
  try {
    const response = await fetch(`${API_BASE_URL}/run-manual-flow`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt,
        boxes,
        connections
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Manual flow failed: ${response.status} - ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Manual flow API error:', error);
    throw error;
  }
}

/**
 * Get example workflow configuration
 */
export async function getExampleWorkflow(): Promise<any> {
  try {
    const response = await fetch(`${API_BASE_URL}/example-workflow`);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to get example workflow: ${response.status} - ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Get example workflow API error:', error);
    throw error;
  }
}

/**
 * Conversation Management Functions
 */

export async function getConversations(): Promise<Conversation[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations`);
    if (!response.ok) throw new Error('Failed to fetch conversations');
    return await response.json();
  } catch (error) {
    console.error('Get conversations error:', error);
    throw error;
  }
}

export async function createConversation(title: string): Promise<{ conversation_id: string; title: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title })
    });
    if (!response.ok) throw new Error('Failed to create conversation');
    return await response.json();
  } catch (error) {
    console.error('Create conversation error:', error);
    throw error;
  }
}

export async function getConversation(conversationId: string): Promise<ConversationDetail> {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`);
    if (!response.ok) throw new Error('Failed to get conversation');
    return await response.json();
  } catch (error) {
    console.error('Get conversation error:', error);
    throw error;
  }
}

export async function deleteConversation(conversationId: string): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Failed to delete conversation');
  } catch (error) {
    console.error('Delete conversation error:', error);
    throw error;
  }
}

// =============================================================================
// ONLINE AGENT SERVICE API FUNCTIONS
// =============================================================================

const ONLINE_API_BASE_URL = 'http://localhost:8000/online';

export interface OnlineAgent {
  id: string;
  name: string;
  role: string;
  model: string;
  system_prompt: string;
  memory_enabled: boolean;
  conversation_id?: string;
}

export interface OnlineWorkflowRequest {
  task: string;
  agents: OnlineAgent[];
  conversation_id?: string;
  enable_streaming: boolean;
}

export interface OnlineWorkflowResponse {
  workflow_id: string;
  status: string;
  agents: Record<string, string>;
  message_history: any[];
  total_messages: number;
  conversation_id: string;
}

/**
 * Test online agent service connection
 */
export async function testOnlineServiceConnection(): Promise<boolean> {
  try {
    const response = await fetch(`${ONLINE_API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (response.ok) {
      const data = await response.json();
      console.log('Online service connection test passed:', data);
      return true;
    } else {
      console.error('Online service connection test failed:', response.status);
      return false;
    }
  } catch (error) {
    console.error('Online service connection test error:', error);
    return false;
  }
}

/**
 * Get available online models
 */
export async function getOnlineModels(): Promise<any> {
  try {
    const response = await fetch(`${ONLINE_API_BASE_URL}/models`);
    if (!response.ok) throw new Error('Failed to get online models');
    return await response.json();
  } catch (error) {
    console.error('Get online models error:', error);
    throw error;
  }
}

/**
 * Run online agent workflow
 */
export async function runOnlineWorkflow(request: OnlineWorkflowRequest): Promise<OnlineWorkflowResponse> {
  try {
    const response = await fetch(`${ONLINE_API_BASE_URL}/run-workflow`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Online workflow failed: ${response.status} - ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Online workflow API error:', error);
    throw error;
  }
}

/**
 * Get online workflow status
 */
export async function getOnlineWorkflowStatus(workflowId: string): Promise<any> {
  try {
    const response = await fetch(`${ONLINE_API_BASE_URL}/workflow-status/${workflowId}`);
    if (!response.ok) throw new Error('Failed to get workflow status');
    return await response.json();
  } catch (error) {
    console.error('Get workflow status error:', error);
    throw error;
  }
}

/**
 * Get online conversations
 */
export async function getOnlineConversations(): Promise<Conversation[]> {
  try {
    const response = await fetch(`${ONLINE_API_BASE_URL}/conversations`);
    if (!response.ok) throw new Error('Failed to fetch online conversations');
    return await response.json();
  } catch (error) {
    console.error('Get online conversations error:', error);
    throw error;
  }
}

/**
 * Get online conversation details
 */
export async function getOnlineConversation(conversationId: string): Promise<ConversationDetail> {
  try {
    const response = await fetch(`${ONLINE_API_BASE_URL}/conversations/${conversationId}`);
    if (!response.ok) throw new Error('Failed to get online conversation');
    return await response.json();
  } catch (error) {
    console.error('Get online conversation error:', error);
    throw error;
  }
} 