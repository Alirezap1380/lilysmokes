/**
 * WebSocket Service for Real-time Agent Communication
 * 
 * This service handles real-time communication with the backend to show
 * live agent interactions instead of just "processing buffering".
 */

export interface AgentMessage {
  type: string;
  from_agent: string;
  to_agent: string;
  message_type: string;
  content: string;
  timestamp: string;
}

export interface AgentStatus {
  agent_id: string;
  status: 'idle' | 'working' | 'waiting' | 'completed' | 'error';
  memory_size: number;
}

export interface WorkflowStatus {
  workflow_id: string;
  status: string;
  agents: Record<string, AgentStatus>;
  message_history: AgentMessage[];
  total_messages: number;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, ((data: any) => void)[]> = new Map();
  private isConnecting = false;

  constructor() {
    // Don't auto-connect in constructor, let the component handle it
    console.log('🔧 WebSocket service initialized');
  }

  public connect() {
    if (this.isConnecting || this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.isConnecting = true;
    console.log('🔗 Attempting to connect to WebSocket...');

    try {
      // Try different WebSocket URLs in case of connection issues
      const wsUrl = 'ws://localhost:8000/ws';
      console.log('🔗 Attempting to connect to:', wsUrl);
      this.ws = new WebSocket(wsUrl);
      console.log('🔗 WebSocket instance created');

      this.ws.onopen = () => {
        console.log('🔗 WebSocket connected');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.emit('connected', {});
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        this.isConnecting = false;
        this.emit('disconnected', {});
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        console.error('WebSocket readyState:', this.ws?.readyState);
        this.isConnecting = false;
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.isConnecting = false;
      this.attemptReconnect();
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

    setTimeout(() => {
      this.connect();
    }, this.reconnectDelay * this.reconnectAttempts);
  }

  private handleMessage(data: any) {
    console.log('📨 Received WebSocket message:', data);

    switch (data.type) {
      case 'agent_message':
        this.emit('agent_message', data);
        break;
      case 'agent_status':
        this.emit('agent_status', data);
        break;
      case 'workflow_status':
        this.emit('workflow_status', data);
        break;
      case 'workflow_complete':
        this.emit('workflow_complete', data);
        break;
      case 'test_response':
        this.emit('test_response', data);
        break;
      case 'error':
        this.emit('error', data);
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  }

  public on(event: string, callback: (data: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  public off(event: string, callback: (data: any) => void) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  private emit(event: string, data: any) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in ${event} callback:`, error);
        }
      });
    }
  }

  public send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  public disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  public isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  public getConnectionState(): string {
    if (!this.ws) return 'CLOSED';
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'CONNECTING';
      case WebSocket.OPEN: return 'OPEN';
      case WebSocket.CLOSING: return 'CLOSING';
      case WebSocket.CLOSED: return 'CLOSED';
      default: return 'UNKNOWN';
    }
  }

  public forceReconnect(): void {
    console.log('🔄 Force reconnecting WebSocket...');
    this.disconnect();
    this.reconnectAttempts = 0;
    this.connect();
  }

  public isReady(): boolean {
    return !this.isConnecting && this.ws?.readyState !== WebSocket.OPEN;
  }

  public testConnection(): void {
    console.log('🧪 Testing WebSocket connection...');
    console.log('Current state:', this.getConnectionState());
    console.log('Is connected:', this.isConnected());

    if (this.isConnected()) {
      this.send({
        type: 'test',
        message: 'Connection test from frontend',
        timestamp: new Date().toISOString()
      });
    } else {
      console.log('❌ WebSocket not connected, attempting to connect...');
      this.connect();
    }
  }
}

// Create a singleton instance
const websocketService = new WebSocketService();

export default websocketService;
