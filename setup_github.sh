#!/bin/bash

# GitHub Integration Setup Script
# This script helps set up the GitHub integration feature

set -e

echo "🚀 Setting up GitHub Integration for Cube AI System"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "backend-ai" ] || [ ! -d "offline-ai-frontend" ]; then
    print_error "Please run this script from the root directory of the Cube AI System"
    exit 1
fi

print_status "Found Cube AI System project structure"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

print_status "Python 3 is installed"

# Check Node.js installation
if ! command -v node &> /dev/null; then
    print_error "Node.js is required but not installed"
    exit 1
fi

print_status "Node.js is installed"

# Install backend dependencies
print_info "Installing backend dependencies..."
cd backend-ai

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found in backend-ai directory"
    exit 1
fi

# Install Python dependencies
pip3 install -r requirements.txt
print_status "Backend dependencies installed"

# Check if github_agent.py exists
if [ ! -f "github_agent.py" ]; then
    print_error "github_agent.py not found. Please ensure the GitHub integration files are present."
    exit 1
fi

print_status "GitHub agent module found"

cd ..

# Install frontend dependencies
print_info "Installing frontend dependencies..."
cd offline-ai-frontend

# Check if package.json exists
if [ ! -f "package.json" ]; then
    print_error "package.json not found in offline-ai-frontend directory"
    exit 1
fi

npm install
print_status "Frontend dependencies installed"

# Check if GitHub components exist
if [ ! -f "src/services/github.ts" ]; then
    print_error "GitHub service not found. Please ensure the GitHub integration files are present."
    exit 1
fi

print_status "GitHub frontend components found"

cd ..

# Create .env file for GitHub configuration (optional)
print_info "Setting up environment variables..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# GitHub Integration Configuration
# Uncomment and set these values to configure GitHub integration
# GITHUB_TOKEN=your_github_token_here
# GITHUB_USERNAME=your_github_username_here

# Backend Configuration
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
EOF
    print_status "Created .env file template"
else
    print_warning ".env file already exists"
fi

# Test the installation
print_info "Testing GitHub integration..."
python3 test_github_integration.py

if [ $? -eq 0 ]; then
    print_status "GitHub integration test passed"
else
    print_warning "GitHub integration test had issues (this is normal if backend is not running)"
fi

# Print setup instructions
echo ""
echo "🎉 GitHub Integration Setup Complete!"
echo "====================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start the backend server:"
echo "   cd backend-ai"
echo "   python3 main.py"
echo ""
echo "2. Start the frontend server:"
echo "   cd offline-ai-frontend"
echo "   npm run dev"
echo ""
echo "3. Configure GitHub integration:"
echo "   - Open http://localhost:5173 in your browser"
echo "   - Navigate to the GitHub Integration page"
echo "   - Enter your GitHub token and username"
echo ""
echo "4. Create a GitHub Personal Access Token:"
echo "   - Go to GitHub Settings → Developer settings → Personal access tokens"
echo "   - Generate a new token with 'repo' permissions"
echo "   - Copy the token and use it in the configuration"
echo ""
echo "5. Test the integration:"
echo "   - Use the AI agents to generate some code"
echo "   - Go to GitHub Operations tab"
echo "   - Extract and push the code to a new repository"
echo ""
echo "For more information, see:"
echo "- GITHUB_INTEGRATION.md - Detailed documentation"
echo "- README.md - General project information"
echo ""
echo "Happy coding! 🚀"

