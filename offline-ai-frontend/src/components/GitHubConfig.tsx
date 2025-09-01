// =============================================================================
// GITHUB CONFIGURATION COMPONENT
// =============================================================================
/**
 * Component for configuring GitHub integration
 * Allows users to set up GitHub token and username
 */

import React, { useState, useEffect } from 'react';
import { githubService, GitHubStatus } from '../services/github';

interface GitHubConfigProps {
  onConfigChange?: (status: GitHubStatus) => void;
}

const GitHubConfig: React.FC<GitHubConfigProps> = ({ onConfigChange }) => {
  const [token, setToken] = useState('');
  const [username, setUsername] = useState('');
  const [status, setStatus] = useState<GitHubStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      setLoading(true);
      const currentStatus = await githubService.getStatus();
      setStatus(currentStatus);
      onConfigChange?.(currentStatus);
    } catch (error) {
      console.error('Failed to check GitHub status:', error);
      setError('Failed to check GitHub status');
    } finally {
      setLoading(false);
    }
  };

  const handleConfigure = async () => {
    if (!token.trim() || !username.trim()) {
      setError('Please provide both token and username');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const result = await githubService.configure({ token, username });
      
      if (result.success) {
        setSuccess('GitHub configured successfully!');
        setToken('');
        setUsername('');
        await checkStatus();
      } else {
        setError(result.error || 'Configuration failed');
      }
    } catch (error) {
      console.error('GitHub configuration error:', error);
      setError(error instanceof Error ? error.message : 'Configuration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setLoading(true);
      // Clear configuration by setting empty values
      await githubService.configure({ token: '', username: '' });
      setStatus({ configured: false, message: 'GitHub disconnected' });
      onConfigChange?.({ configured: false, message: 'GitHub disconnected' });
      setSuccess('GitHub disconnected successfully');
    } catch (error) {
      console.error('Failed to disconnect GitHub:', error);
      setError('Failed to disconnect GitHub');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600 dark:text-gray-300">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center mb-4">
        <svg className="w-6 h-6 text-gray-700 dark:text-gray-300 mr-2" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
        </svg>
        <h2 className="text-xl font-semibold text-gray-800 dark:text-white">GitHub Configuration</h2>
      </div>

      {status?.configured ? (
        <div className="space-y-4">
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-green-600 dark:text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="text-green-800 dark:text-green-200 font-medium">GitHub Connected</span>
            </div>
            <p className="text-green-700 dark:text-green-300 mt-1">
              Username: {status.username} | User: {status.user}
            </p>
            {status.message && (
              <p className="text-green-600 dark:text-green-400 text-sm mt-1">{status.message}</p>
            )}
          </div>

          <div className="flex space-x-3">
            <button
              onClick={checkStatus}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Refresh Status
            </button>
            <button
              onClick={handleDisconnect}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Disconnect
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span className="text-yellow-800 dark:text-yellow-200 font-medium">GitHub Not Configured</span>
            </div>
            <p className="text-yellow-700 dark:text-yellow-300 mt-1">
              Configure GitHub to extract and push your generated code to repositories.
            </p>
          </div>

          <div className="space-y-3">
            <div>
              <label htmlFor="github-token" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                GitHub Personal Access Token
              </label>
              <input
                id="github-token"
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Create a token at <a href="https://github.com/settings/tokens" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">GitHub Settings</a>
              </p>
            </div>

            <div>
              <label htmlFor="github-username" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                GitHub Username
              </label>
              <input
                id="github-username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="your-username"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
            </div>

            <button
              onClick={handleConfigure}
              disabled={!token.trim() || !username.trim()}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              Configure GitHub
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-600 dark:text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span className="text-red-800 dark:text-red-200 font-medium">Error</span>
          </div>
          <p className="text-red-700 dark:text-red-300 mt-1">{error}</p>
        </div>
      )}

      {success && (
        <div className="mt-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-green-600 dark:text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span className="text-green-800 dark:text-green-200 font-medium">Success</span>
          </div>
          <p className="text-green-700 dark:text-green-300 mt-1">{success}</p>
        </div>
      )}
    </div>
  );
};

export default GitHubConfig;

