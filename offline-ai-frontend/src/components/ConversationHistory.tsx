import React, { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import { useTheme } from '../hooks/useTheme';
import { getConversations, deleteConversation, Conversation } from '../services/api';

interface ConversationHistoryProps {
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void;
  currentConversationId?: string;
}

export interface ConversationHistoryRef {
  refresh: () => void;
}

const ConversationHistory = forwardRef<ConversationHistoryRef, ConversationHistoryProps>(({
  onSelectConversation,
  onNewConversation,
  currentConversationId
}, ref) => {
  const { isDark } = useTheme();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  const loadConversations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getConversations();
      setConversations(data);
    } catch (error) {
      console.error('Error loading conversations:', error);
      setError('Failed to load conversations');
    } finally {
      setLoading(false);
    }
  };

  // Expose refresh function to parent component
  useImperativeHandle(ref, () => ({
    refresh: loadConversations
  }));

  useEffect(() => {
    loadConversations();
  }, []);

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    
    // First confirmation - show delete button
    if (!showDeleteConfirm) {
      setShowDeleteConfirm(id);
      return;
    }
    
    // Second confirmation - actually delete
    if (showDeleteConfirm === id) {
      try {
        setDeletingId(id);
        setShowDeleteConfirm(null);
        await deleteConversation(id);
        setConversations(conversations.filter(c => c.id !== id));
        setError(null);
      } catch (error) {
        console.error('Error deleting conversation:', error);
        setError('Failed to delete conversation');
      } finally {
        setDeletingId(null);
      }
    }
  };

  const handleCancelDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    setShowDeleteConfirm(null);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleConversationClick = (conversationId: string) => {
    console.log('Conversation clicked:', conversationId);
    onSelectConversation(conversationId);
  };

  const handleNewConversationClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onNewConversation();
  };

  const handleConversationItemClick = (conversationId: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    handleConversationClick(conversationId);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className={`p-4 border-b ${
        isDark ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-gray-50'
      }`}>
        <div className="flex items-center justify-between">
          <h2 className={`text-lg font-semibold ${
            isDark ? 'text-gray-100' : 'text-gray-900'
          }`}>
            Conversations
          </h2>
          <button
            type="button"
            onClick={handleNewConversationClick}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              isDark 
                ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            New
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className={`p-3 mx-4 mt-2 text-sm rounded ${
          isDark ? 'bg-red-900/20 text-red-400' : 'bg-red-100 text-red-700'
        }`}>
          {error}
        </div>
      )}

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 space-y-2">
            {Array(3).fill(0).map((_, i) => (
              <div key={i} className={`h-12 rounded animate-pulse ${
                isDark ? 'bg-gray-700' : 'bg-gray-200'
              }`}></div>
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <div className={`p-4 text-center ${
            isDark ? 'text-gray-400' : 'text-gray-600'
          }`}>
            No conversations yet
          </div>
        ) : (
          <div className="space-y-1">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                onClick={handleConversationItemClick(conversation.id)}
                className={`p-3 cursor-pointer transition-colors group ${
                  conversation.id === currentConversationId
                    ? (isDark ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-900')
                    : (isDark 
                        ? 'hover:bg-gray-800 text-gray-300' 
                        : 'hover:bg-gray-100 text-gray-700')
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className={`font-medium truncate ${
                      conversation.id === currentConversationId
                        ? (isDark ? 'text-white' : 'text-blue-900')
                        : (isDark ? 'text-gray-200' : 'text-gray-900')
                    }`}>
                      {conversation.title}
                    </div>
                    <div className={`text-xs ${
                      conversation.id === currentConversationId
                        ? (isDark ? 'text-blue-200' : 'text-blue-700')
                        : (isDark ? 'text-gray-400' : 'text-gray-500')
                    }`}>
                      {formatDate(conversation.created_at)}
                    </div>
                  </div>
                  
                  {/* Delete Button - Always Visible */}
                  <div className="flex items-center space-x-1 ml-2">
                    {showDeleteConfirm === conversation.id ? (
                      // Confirmation buttons
                      <>
                        <button
                          type="button"
                          onClick={(e) => handleDeleteConversation(conversation.id, e)}
                          disabled={deletingId === conversation.id}
                          className={`px-2 py-1 text-xs rounded transition-colors ${
                            isDark 
                              ? 'bg-red-600 hover:bg-red-700 text-white' 
                              : 'bg-red-600 hover:bg-red-700 text-white'
                          } ${deletingId === conversation.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                          title="Confirm delete"
                        >
                          {deletingId === conversation.id ? (
                            <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></div>
                          ) : (
                            '✓'
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={handleCancelDelete}
                          className={`px-2 py-1 text-xs rounded transition-colors ${
                            isDark 
                              ? 'bg-gray-600 hover:bg-gray-700 text-white' 
                              : 'bg-gray-600 hover:bg-gray-700 text-white'
                          }`}
                          title="Cancel delete"
                        >
                          ✕
                        </button>
                      </>
                    ) : (
                      // Regular delete button
                      <button
                        type="button"
                        onClick={(e) => handleDeleteConversation(conversation.id, e)}
                        disabled={deletingId === conversation.id}
                        className={`p-1 rounded transition-colors ${
                          isDark 
                            ? 'text-gray-400 hover:text-red-400 hover:bg-gray-700' 
                            : 'text-gray-500 hover:text-red-600 hover:bg-gray-200'
                        } ${deletingId === conversation.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                        title="Delete conversation"
                      >
                        {deletingId === conversation.id ? (
                          <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                        ) : (
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
});

ConversationHistory.displayName = 'ConversationHistory';

export default ConversationHistory; 