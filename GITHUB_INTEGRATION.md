# GitHub Integration Feature

## Overview

The GitHub Integration feature allows you to extract AI-generated code from the Cube AI System and push it directly to GitHub repositories. This feature provides seamless integration between your AI-generated projects and GitHub's version control system.

## Features

### 🔧 Configuration
- **GitHub Authentication**: Configure your GitHub account using Personal Access Tokens
- **Token Validation**: Automatic validation of GitHub tokens
- **User Verification**: Verify GitHub username and permissions

### 📁 Repository Management
- **Create Repositories**: Create new GitHub repositories with custom settings
- **List Repositories**: View all your GitHub repositories
- **Delete Repositories**: Remove repositories (with confirmation)
- **Repository Info**: Get detailed information about specific repositories

### 🚀 Code Extraction & Push
- **Directory Extraction**: Extract code from specified directories
- **File Filtering**: Include/exclude specific file patterns
- **Batch Operations**: Push multiple files in a single operation
- **Quick Extract**: One-click extraction with default settings

### 🎯 Smart Features
- **Pattern Matching**: Intelligent file inclusion/exclusion patterns
- **Error Handling**: Comprehensive error reporting and recovery
- **Progress Tracking**: Real-time operation status updates
- **Security**: Secure token handling and validation

## Backend Components

### GitHub Agent (`github_agent.py`)

The core GitHub integration module that handles all GitHub operations:

```python
# Key Classes
- GitHubConfig: Configuration management
- GitHubRepository: Repository representation
- GitHubFile: File representation for commits
- GitHubAgent: Main agent for GitHub operations
- GitHubWorkflow: High-level workflow operations
```

### API Endpoints

The backend provides RESTful API endpoints for GitHub operations:

```
POST /github/configure          # Configure GitHub integration
GET  /github/status            # Get integration status
POST /github/repositories      # Create new repository
GET  /github/repositories      # List user repositories
GET  /github/repositories/{name} # Get repository info
POST /github/extract-and-push  # Extract and push code
POST /github/update-repository # Update existing repository
DELETE /github/repositories/{name} # Delete repository
```

### Agent Integration

The GitHub agent is integrated into the main agent system:

```python
# Agent Factory Registration
_agent_types = {
    "coordinator": CoordinatorAgent,
    "coder": CoderAgent,
    "tester": TesterAgent,
    "runner": RunnerAgent,
    "github": GitHubAgent  # New GitHub agent
}
```

## Frontend Components

### GitHub Service (`services/github.ts`)

TypeScript service for frontend-backend communication:

```typescript
// Key Interfaces
- GitHubConfig: Configuration interface
- GitHubRepository: Repository interface
- GitHubExtractRequest: Extraction request interface
- GitHubStatus: Status interface
- GitHubResult: Result interface
```

### UI Components

1. **GitHubConfig**: Configuration component for setting up GitHub
2. **GitHubOperations**: Operations component for repository management
3. **GitHubPage**: Main page component with tabbed interface

## Setup Instructions

### 1. Backend Setup

1. **Install Dependencies**:
   ```bash
   cd backend-ai
   pip install -r requirements.txt
   ```

2. **Environment Variables** (Optional):
   ```bash
   export GITHUB_TOKEN="your_github_token"
   export GITHUB_USERNAME="your_github_username"
   ```

3. **Start Backend**:
   ```bash
   python main.py
   ```

### 2. Frontend Setup

1. **Install Dependencies**:
   ```bash
   cd offline-ai-frontend
   npm install
   ```

2. **Start Frontend**:
   ```bash
   npm run dev
   ```

### 3. GitHub Token Setup

1. **Create Personal Access Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `workflow`
   - Copy the generated token

2. **Configure in UI**:
   - Navigate to GitHub Integration page
   - Enter your GitHub username and token
   - Click "Configure GitHub"

## Usage Guide

### Basic Workflow

1. **Configure GitHub**:
   - Open the GitHub Integration page
   - Enter your GitHub token and username
   - Verify the connection

2. **Generate Code**:
   - Use the AI agents to generate code
   - Code will be saved to the generated directory

3. **Extract and Push**:
   - Go to the Operations tab
   - Choose source directory (default: `./generated`)
   - Enter repository name and description
   - Click "Extract & Push"

### Advanced Usage

#### Custom File Patterns

You can specify custom include/exclude patterns:

```json
{
  "include_patterns": ["*.py", "*.js", "*.md"],
  "exclude_patterns": ["__pycache__", "*.log", "node_modules"]
}
```

#### Repository Management

- **Create Repository**: Create empty repositories for future use
- **List Repositories**: View all your repositories with details
- **Delete Repository**: Remove repositories (use with caution)

#### Quick Extract

Use the "Quick Extract" button for automatic naming:
- Generates timestamp-based repository names
- Uses default description
- Automatically configures common file patterns

## API Reference

### Configuration Endpoints

#### POST /github/configure
Configure GitHub integration with token and username.

**Request**:
```json
{
  "token": "ghp_xxxxxxxxxxxxxxxxxxxx",
  "username": "your-username"
}
```

**Response**:
```json
{
  "success": true,
  "message": "GitHub configured successfully",
  "user": "your-username",
  "username": "your-username"
}
```

#### GET /github/status
Get current GitHub integration status.

**Response**:
```json
{
  "configured": true,
  "username": "your-username",
  "user": "your-username",
  "message": "GitHub integration is active"
}
```

### Repository Endpoints

#### POST /github/repositories
Create a new GitHub repository.

**Request**:
```json
{
  "name": "my-project",
  "description": "My awesome project",
  "private": false,
  "auto_init": true,
  "gitignore_template": "Python"
}
```

#### GET /github/repositories
List all user repositories.

#### DELETE /github/repositories/{repo_name}
Delete a repository.

### Extraction Endpoints

#### POST /github/extract-and-push
Extract code and push to new repository.

**Request**:
```json
{
  "source_dir": "./generated",
  "repo_name": "ai-generated-project",
  "description": "AI-generated code from Cube AI System",
  "private": false,
  "include_patterns": ["*.py", "*.js", "*.md"],
  "exclude_patterns": ["__pycache__", "*.log"]
}
```

## Error Handling

### Common Errors

1. **Invalid Token**:
   ```
   Error: Invalid GitHub token
   Solution: Generate a new token with correct permissions
   ```

2. **Repository Already Exists**:
   ```
   Error: Repository already exists
   Solution: Use a different repository name
   ```

3. **Permission Denied**:
   ```
   Error: Insufficient permissions
   Solution: Ensure token has 'repo' scope
   ```

4. **Directory Not Found**:
   ```
   Error: Source directory does not exist
   Solution: Check the source directory path
   ```

### Error Recovery

- **Token Issues**: Reconfigure GitHub with a new token
- **Repository Conflicts**: Use different repository names
- **Network Issues**: Check internet connection and retry
- **Permission Issues**: Verify token permissions

## Security Considerations

### Token Security
- **Never commit tokens**: Tokens are stored in memory only
- **Use minimal permissions**: Only grant necessary scopes
- **Regular rotation**: Rotate tokens periodically
- **Secure storage**: Use environment variables in production

### Data Protection
- **File filtering**: Only extract intended file types
- **Validation**: Validate all inputs before processing
- **Error handling**: Don't expose sensitive information in errors

## Troubleshooting

### Backend Issues

1. **Import Errors**:
   ```bash
   pip install requests
   ```

2. **Module Not Found**:
   ```bash
   # Ensure you're in the backend-ai directory
   cd backend-ai
   python main.py
   ```

3. **Port Conflicts**:
   ```bash
   # Check if port 8000 is in use
   lsof -i :8000
   ```

### Frontend Issues

1. **Connection Errors**:
   - Ensure backend is running on port 8000
   - Check CORS configuration
   - Verify API endpoints

2. **Build Errors**:
   ```bash
   npm install
   npm run build
   ```

3. **TypeScript Errors**:
   ```bash
   npm run type-check
   ```

## Development

### Adding New Features

1. **Backend Extensions**:
   - Add new methods to `GitHubAgent` class
   - Create corresponding API endpoints
   - Update agent factory if needed

2. **Frontend Extensions**:
   - Add new methods to `GitHubService`
   - Create new UI components
   - Update TypeScript interfaces

### Testing

1. **Backend Testing**:
   ```bash
   python -m pytest test_github_agent.py
   ```

2. **Frontend Testing**:
   ```bash
   npm test
   ```

3. **Integration Testing**:
   - Test complete workflow from configuration to push
   - Verify error handling
   - Test with different file types

## Contributing

### Code Style
- Follow existing code patterns
- Add comprehensive documentation
- Include error handling
- Write tests for new features

### Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review error messages carefully
3. Verify GitHub token permissions
4. Open an issue with detailed information

## License

This feature is part of the Cube AI System and follows the same license terms.

