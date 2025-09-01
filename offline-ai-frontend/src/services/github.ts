// =============================================================================
// GITHUB SERVICE - FRONTEND INTEGRATION
// =============================================================================
/**
 * GitHub service for managing code extraction and repository operations
 * Provides methods to interact with GitHub API endpoints
 */

export interface GitHubConfig {
  token: string;
  username: string;
}

export interface GitHubRepository {
  name: string;
  description: string;
  private: boolean;
  auto_init?: boolean;
  gitignore_template?: string;
}

export interface GitHubExtractRequest {
  source_dir: string;
  repo_name: string;
  description: string;
  private: boolean;
  include_patterns?: string[];
  exclude_patterns?: string[];
}

export interface GitHubUpdateRequest {
  repo_name: string;
  source_dir: string;
  include_patterns?: string[];
  exclude_patterns?: string[];
}

export interface GitHubStatus {
  configured: boolean;
  username?: string;
  user?: string;
  message?: string;
  error?: string;
}

export interface GitHubResult {
  success: boolean;
  message?: string;
  error?: string;
  repository?: any;
  files_pushed?: any;
  repositories?: any[];
}

class GitHubService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = 'http://localhost:8000/github';
  }

  /**
   * Configure GitHub integration
   */
  async configure(config: GitHubConfig): Promise<GitHubResult> {
    try {
      const response = await fetch(`${this.baseUrl}/configure`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to configure GitHub');
      }

      return data;
    } catch (error) {
      console.error('GitHub configuration error:', error);
      throw error;
    }
  }

  /**
   * Get GitHub integration status
   */
  async getStatus(): Promise<GitHubStatus> {
    try {
      const response = await fetch(`${this.baseUrl}/status`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to get GitHub status');
      }

      return data;
    } catch (error) {
      console.error('GitHub status error:', error);
      return {
        configured: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Create a new GitHub repository
   */
  async createRepository(repo: GitHubRepository): Promise<GitHubResult> {
    try {
      const response = await fetch(`${this.baseUrl}/repositories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(repo),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create repository');
      }

      return data;
    } catch (error) {
      console.error('Create repository error:', error);
      throw error;
    }
  }

  /**
   * List all GitHub repositories
   */
  async listRepositories(): Promise<GitHubResult> {
    try {
      const response = await fetch(`${this.baseUrl}/repositories`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to list repositories');
      }

      return data;
    } catch (error) {
      console.error('List repositories error:', error);
      throw error;
    }
  }

  /**
   * Get information about a specific repository
   */
  async getRepository(repoName: string): Promise<GitHubResult> {
    try {
      const response = await fetch(`${this.baseUrl}/repositories/${repoName}`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to get repository');
      }

      return data;
    } catch (error) {
      console.error('Get repository error:', error);
      throw error;
    }
  }

  /**
   * Extract code and push to a new GitHub repository
   */
  async extractAndPush(request: GitHubExtractRequest): Promise<GitHubResult> {
    try {
      const response = await fetch(`${this.baseUrl}/extract-and-push`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to extract and push');
      }

      return data;
    } catch (error) {
      console.error('Extract and push error:', error);
      throw error;
    }
  }

  /**
   * Update an existing GitHub repository
   */
  async updateRepository(request: GitHubUpdateRequest): Promise<GitHubResult> {
    try {
      const response = await fetch(`${this.baseUrl}/update-repository`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to update repository');
      }

      return data;
    } catch (error) {
      console.error('Update repository error:', error);
      throw error;
    }
  }

  /**
   * Delete a GitHub repository
   */
  async deleteRepository(repoName: string): Promise<GitHubResult> {
    try {
      const response = await fetch(`${this.baseUrl}/repositories/${repoName}`, {
        method: 'DELETE',
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to delete repository');
      }

      return data;
    } catch (error) {
      console.error('Delete repository error:', error);
      throw error;
    }
  }

  /**
   * Quick extract and push with default settings
   */
  async quickExtract(repoName: string, description: string = '', private: boolean = false): Promise<GitHubResult> {
    const request: GitHubExtractRequest = {
      source_dir: './generated', // Default generated directory
      repo_name: repoName,
      description: description || `AI-generated code from Cube AI System - ${new Date().toISOString()}`,
      private: private,
      include_patterns: ['*.py', '*.js', '*.ts', '*.tsx', '*.jsx', '*.html', '*.css', '*.json', '*.md', '*.txt'],
      exclude_patterns: ['__pycache__', '*.log', '*.tmp', '.DS_Store', 'node_modules', '.git']
    };

    return this.extractAndPush(request);
  }

  /**
   * Validate GitHub token
   */
  async validateToken(token: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/configure`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token, username: 'test' }),
      });

      return response.ok;
    } catch (error) {
      return false;
    }
  }
}

// Export singleton instance
export const githubService = new GitHubService();
export default githubService;

