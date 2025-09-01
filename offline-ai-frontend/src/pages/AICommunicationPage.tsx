import React, { useState, useEffect, useRef } from 'react';
import AgentVisualization from '../components/AgentVisualization';
import ConversationHistory, { ConversationHistoryRef } from '../components/ConversationHistory';
import { testBackendConnection, createConversation, getConversation, chatWithAgents } from '../services/api';
import { useTheme } from '../hooks/useTheme';
import websocketService from '../services/websocket';

interface AIBlock {
  id: string;
  name: string;
  type: 'coordinator' | 'coder' | 'tester' | 'runner';
  content: string;
  timestamp: string;
  iteration: number;
}

export default function AICommunicationPage() {
  const { isDark } = useTheme();
  const [interactions, setInteractions] = useState<AIBlock[]>([]);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>(undefined);
  const [selectedConversation, setSelectedConversation] = useState<any>(null);
  const [isHistoryCollapsed, setIsHistoryCollapsed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // WebSocket state
  const [wsConnected, setWsConnected] = useState(false);
  const [wsStatus, setWsStatus] = useState('CLOSED');
  const [realTimeMessages, setRealTimeMessages] = useState<AIBlock[]>([]);
  
  // Ref to ConversationHistory component for refreshing
  const conversationHistoryRef = useRef<ConversationHistoryRef>(null);

  // Test backend connection on component mount
  useEffect(() => {
    const testConnection = async () => {
      try {
        setError(null);
        const connected = await testBackendConnection();
        setBackendConnected(connected);
      } catch (error) {
        console.error('Backend connection test failed:', error);
        setBackendConnected(false);
        setError('Backend connection failed');
      }
    };

    testConnection();
    
    // Test connection every 30 seconds
    const interval = setInterval(testConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket event handlers
  useEffect(() => {
    const handleConnected = () => {
      setWsConnected(true);
      setWsStatus('OPEN');
      console.log('🔗 WebSocket connected to AICommunicationPage');
    };

    const handleDisconnected = () => {
      setWsConnected(false);
      setWsStatus('CLOSED');
      console.log('🔌 WebSocket disconnected from AICommunicationPage');
    };

    const handleAgentMessage = (data: any) => {
      console.log('📨 Received agent message via WebSocket:', data);
      if (data.content && data.from_agent && data.to_agent) {
        // Determine agent type based on name
        let agentType: 'coordinator' | 'coder' | 'tester' | 'runner' = 'coordinator';
        let agentName = data.from_agent;
        
        if (agentName.toLowerCase().includes('coder') || agentName.toLowerCase().includes('mistral')) {
          agentType = 'coder';
        } else if (agentName.toLowerCase().includes('tester') || agentName.toLowerCase().includes('phi')) {
          agentType = 'tester';
        } else if (agentName.toLowerCase().includes('runner') || agentName.toLowerCase().includes('llama')) {
          agentType = 'runner';
        } else if (agentName.toLowerCase().includes('coordinator')) {
          agentType = 'coordinator';
        }

        const newMessage: AIBlock = {
          id: `ws-${Date.now()}-${Math.random()}`,
          name: agentName,
          type: agentType,
          content: data.content,
          timestamp: data.timestamp || new Date().toISOString(),
          iteration: realTimeMessages.length + 1
        };

        setRealTimeMessages(prev => [...prev, newMessage]);
        setInteractions(prev => [...prev, newMessage]);
        console.log('🔄 Added real-time message:', newMessage);
      }
    };

    const handleWorkflowStatus = (data: any) => {
      console.log('📊 Received workflow status via WebSocket:', data);
      if (data.status === 'completed' || data.status === 'error') {
        setIsLoading(false);
        const statusMessage: AIBlock = {
          id: `status-${Date.now()}`,
          name: 'System',
          type: 'coordinator',
          content: data.status === 'completed' ? '✅ Workflow completed successfully!' : '❌ Workflow failed',
          timestamp: new Date().toISOString(),
          iteration: realTimeMessages.length + 1
        };
        setRealTimeMessages(prev => [...prev, statusMessage]);
      }
    };

    const handleTestMessage = (data: any) => {
      console.log('🧪 Received test message via WebSocket:', data);
      const testMessage: AIBlock = {
        id: `test-${Date.now()}`,
        name: 'System',
        type: 'coordinator',
        content: `🧪 WebSocket Test: ${data.message || 'Connection working!'}`,
        timestamp: new Date().toISOString(),
        iteration: realTimeMessages.length + 1
      };
      setRealTimeMessages(prev => [...prev, testMessage]);
    };

    // Subscribe to WebSocket events
    websocketService.on('connected', handleConnected);
    websocketService.on('disconnected', handleDisconnected);
    websocketService.on('agent_message', handleAgentMessage);
    websocketService.on('workflow_status', handleWorkflowStatus);
    websocketService.on('test_response', handleTestMessage);

    // Connect to WebSocket
    websocketService.connect();

    // Cleanup
    return () => {
      websocketService.off('connected', handleConnected);
      websocketService.off('disconnected', handleDisconnected);
      websocketService.off('agent_message', handleAgentMessage);
      websocketService.off('workflow_status', handleWorkflowStatus);
      websocketService.off('test_response', handleTestMessage);
    };
  }, [realTimeMessages.length]);

  // Conversation handlers
  const handleNewConversation = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const title = prompt('Enter conversation title:') || 'New Conversation';
      const result = await createConversation(title);
      setCurrentConversationId(result.conversation_id);
      setSelectedConversation(null);
      
      // Refresh the conversation list to show the new conversation
      if (conversationHistoryRef.current) {
        conversationHistoryRef.current.refresh();
      }
    } catch (error) {
      console.error('Failed to create conversation:', error);
      setError('Failed to create conversation');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectConversation = async (conversationId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      setCurrentConversationId(conversationId);
      const conversation = await getConversation(conversationId);
      setSelectedConversation(conversation);
      
      if (conversation.messages && conversation.messages.length > 0) {
        const conversationInteractions: AIBlock[] = conversation.messages.map((msg: any, index: number) => {
          let agentType: 'coordinator' | 'coder' | 'tester' | 'runner' = 'coordinator';
          let agentName = msg.from_agent || 'User';
          
          if (agentName.toLowerCase().includes('coder') || agentName.toLowerCase().includes('mistral')) {
            agentType = 'coder';
          } else if (agentName.toLowerCase().includes('tester') || agentName.toLowerCase().includes('phi')) {
            agentType = 'tester';
          } else if (agentName.toLowerCase().includes('runner') || agentName.toLowerCase().includes('llama')) {
            agentType = 'runner';
          } else if (agentName.toLowerCase().includes('coordinator') || agentName.toLowerCase().includes('coordinator')) {
            agentType = 'coordinator';
          }
          
          return {
            id: `conv-${conversationId}-${index}`,
            name: agentName,
            type: agentType,
            content: msg.content,
            timestamp: msg.timestamp || new Date().toISOString(),
            iteration: index + 1
          };
        });
        
        setInteractions(conversationInteractions);
      } else {
        setInteractions([]);
      }
    } catch (error) {
      console.error('Failed to select conversation:', error);
      setError('Failed to load conversation');
    } finally {
      setIsLoading(false);
    }
  };

  // Example interaction data
  useEffect(() => {
    const exampleInteractions: AIBlock[] = [
      {
        id: '1',
        name: 'Coordinator Agent',
        type: 'coordinator',
        content: 'Ready to coordinate AI tasks...',
        timestamp: new Date(Date.now() - 5000).toISOString(),
        iteration: 1
      },
      {
        id: '2',
        name: 'Coder Agent (Mistral)',
        type: 'coder',
        content: 'Ready to generate and refine code...',
        timestamp: new Date(Date.now() - 4000).toISOString(),
        iteration: 1
      },
      {
        id: '3',
        name: 'Tester Agent (Phi)',
        type: 'tester',
        content: 'Ready to generate unit tests...',
        timestamp: new Date(Date.now() - 3000).toISOString(),
        iteration: 1
      },
      {
        id: '4',
        name: 'Runner Agent (Llama3.2)',
        type: 'runner',
        content: 'Ready to run tests and report outcomes...',
        timestamp: new Date(Date.now() - 2000).toISOString(),
        iteration: 1
      }
    ];
    setInteractions(exampleInteractions);
  }, []);

  const handlePromptSubmit = async (prompt: string) => {
    try {
      // Only show loading if WebSocket is not connected
      if (!wsConnected) {
        setIsLoading(true);
      }
      setError(null);
      
      // Clear real-time messages for new conversation
      setRealTimeMessages([]);
      
      // Create user interaction block
      const userInteraction: AIBlock = {
        id: `user-${Date.now()}`,
        name: 'User',
        type: 'coordinator',
        content: prompt,
        timestamp: new Date().toISOString(),
        iteration: 1
      };

      // Add user message to real-time messages and interactions
      setRealTimeMessages([userInteraction]);
      setInteractions(prev => [...prev, userInteraction]);

      // Send test message via WebSocket to verify connection
      if (wsConnected) {
        websocketService.send({
          type: 'test',
          message: 'Starting AI workflow - testing real-time communication',
          timestamp: new Date().toISOString()
        });
        
        // Don't wait for API response if WebSocket is connected
        // The WebSocket messages will update the UI in real-time
        console.log('🔗 WebSocket connected - using real-time communication');
        return;
      }

      // Only call API if WebSocket is not connected
      console.log('⚠️ WebSocket not connected - using API fallback');
      const response = await chatWithAgents({
        prompt,
        conversation_id: currentConversationId
      });

      // Create AI interaction blocks based on response
      const aiInteractions: AIBlock[] = [];

      if (response.code) {
        aiInteractions.push({
          id: `coder-${Date.now()}`,
          name: 'Coder Agent (Mistral)',
          type: 'coder',
          content: response.code,
          timestamp: new Date().toISOString(),
          iteration: 2
        });
      }

      if (response.tests) {
        aiInteractions.push({
          id: `tester-${Date.now()}`,
          name: 'Tester Agent (Phi-3)',
          type: 'tester',
          content: response.tests,
          timestamp: new Date().toISOString(),
          iteration: 3
        });
      }

      if (response.test_results) {
        aiInteractions.push({
          id: `runner-${Date.now()}`,
          name: 'Runner Agent (Llama3.2)',
          type: 'runner',
          content: response.test_results,
          timestamp: new Date().toISOString(),
          iteration: 4
        });
      }
      
      // Update interactions with new blocks
      setInteractions(prev => [...prev, ...aiInteractions]);
      
      // Refresh conversation list to show updated conversation
      if (conversationHistoryRef.current) {
        conversationHistoryRef.current.refresh();
      }
      
    } catch (error) {
      console.error('Failed to submit prompt:', error);
      setError('Failed to submit prompt');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSidebarToggle = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsHistoryCollapsed(!isHistoryCollapsed);
  };

  return (
    <div className="h-full relative flex overflow-hidden">
      {/* Error Display */}
      {error && (
        <div className={`absolute top-16 left-4 right-4 z-50 p-3 rounded text-sm ${
          isDark ? 'bg-red-900/90 text-red-200' : 'bg-red-100 text-red-800'
        }`}>
          {error}
        </div>
      )}

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-black/20 z-40 flex items-center justify-center">
          <div className={`p-4 rounded ${
            isDark ? 'bg-gray-800 text-white' : 'bg-white text-gray-900'
          }`}>
            Loading...
          </div>
        </div>
      )}

      {/* Main AI Visualization Area */}
      <div className={`flex-1 min-w-0 ${isHistoryCollapsed ? '' : 'mr-80'}`}>
        <AgentVisualization 
          isDark={isDark}
          interactions={interactions}
          onPromptSubmit={handlePromptSubmit}
        />
      </div>

      {/* Collapsible Conversation History Sidebar */}
      <div className={`absolute right-0 top-0 h-full border-l shadow-lg transition-all duration-300 ${
        isDark ? 'bg-gray-900 border-gray-700' : 'bg-white border-gray-200'
      } ${isHistoryCollapsed ? 'w-12' : 'w-80'}`}>
        {/* Collapse Toggle Button */}
        <button
          type="button"
          onClick={handleSidebarToggle}
          className="absolute -left-3 top-4 bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-blue-700 transition-colors"
        >
          {isHistoryCollapsed ? '›' : '‹'}
        </button>

        {/* Conversation History Content */}
        {!isHistoryCollapsed && (
          <div className="h-full p-4 overflow-hidden">
            <ConversationHistory
              ref={conversationHistoryRef}
              onSelectConversation={handleSelectConversation}
              onNewConversation={handleNewConversation}
              currentConversationId={currentConversationId}
            />
          </div>
        )}
      </div>

      {/* Backend Connection Status */}
      {backendConnected !== null && (
        <div className={`absolute top-4 left-4 flex items-center space-x-2 px-3 py-1 rounded text-sm ${
          backendConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          <div className={`w-2 h-2 rounded-full ${
            backendConnected ? 'bg-green-500' : 'bg-red-500'
          }`}></div>
          <span>
            {backendConnected ? 'Backend Connected' : 'Backend Disconnected'}
          </span>
        </div>
      )}

      {/* WebSocket Status */}
      <div className={`absolute top-4 left-64 flex items-center space-x-2 px-3 py-1 rounded text-sm ${
        wsConnected ? 'bg-blue-100 text-blue-800' : 'bg-yellow-100 text-yellow-800'
      }`}>
        <div className={`w-2 h-2 rounded-full ${
          wsConnected ? 'bg-blue-500' : 'bg-yellow-500'
        }`}></div>
        <span>
          {wsConnected ? 'WebSocket Live' : 'WebSocket Connecting...'}
        </span>
      </div>

      {/* WebSocket Test Button */}
      <button
        onClick={() => {
          websocketService.testConnection();
          const testMessage: AIBlock = {
            id: `test-${Date.now()}`,
            name: 'System',
            type: 'coordinator',
            content: `🧪 Testing WebSocket connection... Status: ${wsStatus}`,
            timestamp: new Date().toISOString(),
            iteration: realTimeMessages.length + 1
          };
          setRealTimeMessages(prev => [...prev, testMessage]);
        }}
        className="absolute top-4 left-96 px-3 py-1 bg-purple-600 text-white rounded text-sm hover:bg-purple-700 transition-colors"
        title={`WebSocket Status: ${wsStatus}`}
      >
        Test WS
      </button>
    </div>
  );
} 