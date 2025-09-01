// =============================================================================
// GITHUB PAGE COMPONENT
// =============================================================================
/**
 * Main GitHub page component that combines configuration and operations
 * Provides a tabbed interface for managing GitHub integration
 */

import React, { useState, useEffect } from 'react';
import GitHubConfig from './GitHubConfig';
import GitHubOperations from './GitHubOperations';
import { githubService, GitHubStatus } from '../services/github';

const GitHubPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'config' | 'operations'>('config');
  const [githubStatus, setGitHubStatus] = useState<GitHubStatus>({ configured: false });

  useEffect(() => {
    checkGitHubStatus();
  }, []);

  const checkGitHubStatus = async () => {
    try {
      const status = await githubService.getStatus();
      setGitHubStatus(status);
    } catch (error) {
      console.error('Failed to check GitHub status:', error);
      setGitHubStatus({ configured: false, error: 'Failed to check status' });
    }
  };

  const handleConfigChange = (status: GitHubStatus) => {
    setGitHubStatus(status);
    if (status.configured) {
      setActiveTab('operations');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <svg className="w-8 h-8 text-gray-700 dark:text-gray-300 mr-3" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">GitHub Integration</h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            Extract your AI-generated code and push it to GitHub repositories. Configure your GitHub account and manage your repositories.
          </p>
        </div>

        {/* Status Indicator */}
        <div className="mb-6">
          {githubStatus.configured ? (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-green-600 dark:text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-green-800 dark:text-green-200 font-medium">
                  GitHub Connected
                </span>
                {githubStatus.username && (
                  <span className="text-green-700 dark:text-green-300 ml-2">
                    ({githubStatus.username})
                  </span>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <span className="text-yellow-800 dark:text-yellow-200 font-medium">
                  GitHub Not Configured
                </span>
              </div>
              <p className="text-yellow-700 dark:text-yellow-300 mt-1">
                Configure your GitHub account to start extracting and pushing code to repositories.
              </p>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('config')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'config'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                <div className="flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                  </svg>
                  Configuration
                </div>
              </button>
              <button
                onClick={() => setActiveTab('operations')}
                disabled={!githubStatus.configured}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'operations'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : githubStatus.configured
                    ? 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                    : 'border-transparent text-gray-400 cursor-not-allowed'
                }`}
              >
                <div className="flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                  </svg>
                  Operations
                </div>
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'config' && (
            <GitHubConfig onConfigChange={handleConfigChange} />
          )}
          
          {activeTab === 'operations' && (
            <GitHubOperations githubStatus={githubStatus} />
          )}
        </div>

        {/* Help Section */}
        <div className="mt-12 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-200 mb-3">
            How to Use GitHub Integration
          </h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-blue-700 dark:text-blue-300 mb-2">1. Configuration</h4>
              <ul className="text-sm text-blue-600 dark:text-blue-400 space-y-1">
                <li>• Create a GitHub Personal Access Token</li>
                <li>• Go to GitHub Settings → Developer settings → Personal access tokens</li>
                <li>• Generate a new token with 'repo' permissions</li>
                <li>• Enter your token and GitHub username</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-blue-700 dark:text-blue-300 mb-2">2. Operations</h4>
              <ul className="text-sm text-blue-600 dark:text-blue-400 space-y-1">
                <li>• Create new repositories</li>
                <li>• Extract code from generated files</li>
                <li>• Push code to GitHub repositories</li>
                <li>• Manage existing repositories</li>
              </ul>
            </div>
          </div>
          <div className="mt-4 p-3 bg-blue-100 dark:bg-blue-800/30 rounded-lg">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              <strong>Note:</strong> The system will extract code from the specified directory and push it to GitHub. 
              Make sure you have the necessary permissions and that your token is valid.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GitHubPage;

