// =============================================================================
// GITHUB OPERATIONS COMPONENT
// =============================================================================
/**
 * Component for GitHub operations like creating repositories and extracting code
 * Provides interface for managing GitHub repositories and code extraction
 */

import React, { useState, useEffect } from 'react';
import { githubService, GitHubStatus, GitHubResult } from '../services/github';

interface GitHubOperationsProps {
  githubStatus: GitHubStatus;
}

const GitHubOperations: React.FC<GitHubOperationsProps> = ({ githubStatus }) => {
  const [repositories, setRepositories] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Form states
  const [repoName, setRepoName] = useState('');
  const [repoDescription, setRepoDescription] = useState('');
  const [isPrivate, setIsPrivate] = useState(false);
  const [sourceDir, setSourceDir] = useState('./generated');
  const [extractRepoName, setExtractRepoName] = useState('');
  const [extractDescription, setExtractDescription] = useState('');
  const [extractPrivate, setExtractPrivate] = useState(false);

  useEffect(() => {
    if (githubStatus.configured) {
      loadRepositories();
    }
  }, [githubStatus.configured]);

  const loadRepositories = async () => {
    try {
      setLoading(true);
      const result = await githubService.listRepositories();
      if (result.success && result.repositories) {
        setRepositories(result.repositories);
      }
    } catch (error) {
      console.error('Failed to load repositories:', error);
      setError('Failed to load repositories');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRepository = async () => {
    if (!repoName.trim()) {
      setError('Please provide a repository name');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const result = await githubService.createRepository({
        name: repoName,
        description: repoDescription,
        private: isPrivate
      });

      if (result.success) {
        setSuccess(`Repository "${repoName}" created successfully!`);
        setRepoName('');
        setRepoDescription('');
        setIsPrivate(false);
        await loadRepositories();
      } else {
        setError(result.error || 'Failed to create repository');
      }
    } catch (error) {
      console.error('Create repository error:', error);
      setError(error instanceof Error ? error.message : 'Failed to create repository');
    } finally {
      setLoading(false);
    }
  };

  const handleExtractAndPush = async () => {
    if (!extractRepoName.trim()) {
      setError('Please provide a repository name');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const result = await githubService.extractAndPush({
        source_dir: sourceDir,
        repo_name: extractRepoName,
        description: extractDescription || `AI-generated code from Cube AI System - ${new Date().toISOString()}`,
        private: extractPrivate
      });

      if (result.success) {
        setSuccess(`Code extracted and pushed to "${extractRepoName}" successfully!`);
        setExtractRepoName('');
        setExtractDescription('');
        setExtractPrivate(false);
        await loadRepositories();
      } else {
        setError(result.error || 'Failed to extract and push code');
      }
    } catch (error) {
      console.error('Extract and push error:', error);
      setError(error instanceof Error ? error.message : 'Failed to extract and push code');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickExtract = async () => {
    const defaultName = `ai-generated-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}`;
    setExtractRepoName(defaultName);
    setExtractDescription(`AI-generated code from Cube AI System - ${new Date().toISOString()}`);
  };

  const handleDeleteRepository = async (repoName: string) => {
    if (!confirm(`Are you sure you want to delete the repository "${repoName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const result = await githubService.deleteRepository(repoName);
      
      if (result.success) {
        setSuccess(`Repository "${repoName}" deleted successfully!`);
        await loadRepositories();
      } else {
        setError(result.error || 'Failed to delete repository');
      }
    } catch (error) {
      console.error('Delete repository error:', error);
      setError(error instanceof Error ? error.message : 'Failed to delete repository');
    } finally {
      setLoading(false);
    }
  };

  if (!githubStatus.configured) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="text-center text-gray-500 dark:text-gray-400">
          <svg className="w-12 h-12 mx-auto mb-4 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
          </svg>
          <p>Please configure GitHub first to use these operations.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Create Repository Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Create Repository</h3>
        
        <div className="space-y-3">
          <div>
            <label htmlFor="repo-name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Repository Name
            </label>
            <input
              id="repo-name"
              type="text"
              value={repoName}
              onChange={(e) => setRepoName(e.target.value)}
              placeholder="my-awesome-project"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
          </div>

          <div>
            <label htmlFor="repo-description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description (optional)
            </label>
            <input
              id="repo-description"
              type="text"
              value={repoDescription}
              onChange={(e) => setRepoDescription(e.target.value)}
              placeholder="A brief description of your project"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
          </div>

          <div className="flex items-center">
            <input
              id="repo-private"
              type="checkbox"
              checked={isPrivate}
              onChange={(e) => setIsPrivate(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="repo-private" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
              Private repository
            </label>
          </div>

          <button
            onClick={handleCreateRepository}
            disabled={!repoName.trim() || loading}
            className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Creating...' : 'Create Repository'}
          </button>
        </div>
      </div>

      {/* Extract and Push Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Extract & Push Code</h3>
        
        <div className="space-y-3">
          <div>
            <label htmlFor="source-dir" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Source Directory
            </label>
            <input
              id="source-dir"
              type="text"
              value={sourceDir}
              onChange={(e) => setSourceDir(e.target.value)}
              placeholder="./generated"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
          </div>

          <div>
            <label htmlFor="extract-repo-name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Repository Name
            </label>
            <input
              id="extract-repo-name"
              type="text"
              value={extractRepoName}
              onChange={(e) => setExtractRepoName(e.target.value)}
              placeholder="ai-generated-project"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
          </div>

          <div>
            <label htmlFor="extract-description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description (optional)
            </label>
            <input
              id="extract-description"
              type="text"
              value={extractDescription}
              onChange={(e) => setExtractDescription(e.target.value)}
              placeholder="AI-generated code from Cube AI System"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
          </div>

          <div className="flex items-center">
            <input
              id="extract-private"
              type="checkbox"
              checked={extractPrivate}
              onChange={(e) => setExtractPrivate(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="extract-private" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
              Private repository
            </label>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={handleQuickExtract}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Quick Extract
            </button>
            <button
              onClick={handleExtractAndPush}
              disabled={!extractRepoName.trim() || loading}
              className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Extracting...' : 'Extract & Push'}
            </button>
          </div>
        </div>
      </div>

      {/* Repositories List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Your Repositories</h3>
          <button
            onClick={loadRepositories}
            disabled={loading}
            className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 disabled:bg-gray-400 transition-colors"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {repositories.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-center py-4">No repositories found</p>
        ) : (
          <div className="space-y-2">
            {repositories.map((repo) => (
              <div key={repo.id} className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-800 dark:text-white">{repo.name}</span>
                    {repo.private && (
                      <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded">
                        Private
                      </span>
                    )}
                  </div>
                  {repo.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{repo.description}</p>
                  )}
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    Created: {new Date(repo.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex space-x-2">
                  <a
                    href={repo.html_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                  >
                    View
                  </a>
                  <button
                    onClick={() => handleDeleteRepository(repo.name)}
                    className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Error and Success Messages */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
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
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
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

export default GitHubOperations;

