# Multi-Agent AI System

A sophisticated multi-agent AI system with a modern React frontend and FastAPI backend, featuring code generation, testing, and execution capabilities.

## 🚀 Features

- **Multi-Agent Architecture**: Coordinator, Coder, Tester, and Runner agents
- **Modern Frontend**: React + TypeScript with beautiful UI
- **FastAPI Backend**: Robust API with comprehensive endpoints
- **Code Generation**: AI-powered Python code generation
- **Automated Testing**: Test case generation and execution
- **Visual Workflow Designer**: Drag-and-drop agent workflow creation
- **GPU Acceleration**: Optimized for CodeLlama and other models
- **GitHub Integration**: Extract and push code to GitHub repositories

## 📁 Project Structure

```
├── backend-ai/           # FastAPI backend
│   ├── main.py          # Main backend application
│   ├── services/        # Backend services
│   └── generated/       # Generated code and tests
├── offline-ai-frontend/ # React frontend
│   ├── src/            # Source code
│   ├── components/     # React components
│   └── services/       # Frontend services
├── setup.py            # Automated setup script
├── INSTALLATION.md     # Detailed installation guide
└── README.md           # This file
```

## ⚡ Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Run the setup script - it handles everything!
python setup.py
```

### Option 2: Manual Installation

#### What Gets Installed Automatically
When you run `pip install -r requirements.txt`, these are installed:
- ✅ **FastAPI** - Web framework
- ✅ **Uvicorn** - ASGI server  
- ✅ **Pydantic** - Data validation
- ✅ **LangChain-Ollama** - Ollama integration
- ✅ **Python-Multipart** - File uploads
- ✅ **Requests** - HTTP library

#### What You Need to Install Manually
❌ **Ollama** (AI model server) - Not a Python package
❌ **LLM Models** (CodeLlama, Mistral, etc.) - Downloaded separately

```bash
# 1. Install Python dependencies
cd backend-ai
pip install -r requirements.txt

# 2. Install Ollama (system-level application)
# Windows: winget install Ollama.Ollama
# macOS: brew install ollama  
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# 3. Download AI models
ollama pull codellama:7b-instruct
ollama pull mistral
ollama pull llama2

# 4. Install frontend dependencies
cd offline-ai-frontend
npm install
```

## 🎯 Usage

1. **Start the Backend:**
   ```bash
   cd backend-ai
   python main.py
   ```

2. **Start the Frontend:**
   ```bash
   cd offline-ai-frontend
   npm run dev
   ```

3. **Access the Application:**
   - Backend API: http://localhost:8000
   - Frontend UI: http://localhost:5173
   - API Documentation: http://localhost:8000/docs

## 🤖 Available Agents

- **Coordinator**: Manages workflow and task distribution
- **Coder**: Generates Python code based on requirements
- **Tester**: Creates comprehensive test cases
- **Runner**: Executes tests and reports results
- **GitHub**: Extracts and pushes code to GitHub repositories

## ⚙️ Configuration

### GPU Settings

The system supports GPU acceleration. Configure in `main.py`:

```python
DEFAULT_GPU_CONFIG = {
    "num_gpu": 1,
    "num_thread": 8,
    "temperature": 0.3,
    "top_p": 0.9,
    "repeat_penalty": 1.1,
    "top_k": 40,
    "num_ctx": 4096,
}
```

### AI Models

Supported models:
- `codellama:7b-instruct` (recommended for code generation)
- `mistral` (good for general tasks)
- `llama2` (balanced performance)

## 📋 System Requirements

### Minimum
- **Python:** 3.8+
- **Node.js:** 16+
- **RAM:** 8GB (16GB recommended)
- **Storage:** 10GB free space
- **GPU:** Optional but recommended

### Recommended
- **Python:** 3.9+
- **Node.js:** 18+
- **RAM:** 16GB+
- **Storage:** 20GB free space
- **GPU:** NVIDIA GPU with 8GB+ VRAM

## 🔧 API Endpoints

- `POST /chat` - Main chat interface
- `POST /run-workflow` - Custom agent workflows
- `POST /run-manual-flow` - Visual workflow execution
- `GET /health` - Health check
- `GET /list-files` - List generated files
- `GET /gpu-status` - GPU configuration status

### GitHub Integration Endpoints
- `POST /github/configure` - Configure GitHub integration
- `GET /github/status` - Get GitHub integration status
- `POST /github/repositories` - Create new repository
- `GET /github/repositories` - List user repositories
- `POST /github/extract-and-push` - Extract and push code to GitHub
- `DELETE /github/repositories/{name}` - Delete repository

## 🎨 Frontend Features

- **Chat Interface**: Direct interaction with AI agents
- **Code Editor**: Syntax-highlighted code editing
- **File Tree**: Browse generated files
- **Visual Workflow Designer**: Drag-and-drop agent connections
- **Test Results**: View test execution results
- **Dark/Light Theme**: Toggle between themes
- **GitHub Integration**: Configure GitHub and manage repositories

## 🔍 Development

### Adding New Agents

1. Create a new agent class inheriting from `BaseAgent`
2. Implement the required abstract methods
3. Register the agent type in `AgentFactory`
4. Update the frontend to support the new agent

### Customizing Models

Modify `MODEL_CONFIGS` in `main.py` to add new model configurations.

## 📝 Troubleshooting

### Common Issues

1. **"ollama command not found"**
   - Install Ollama: https://ollama.ai

2. **"Model not found" errors**
   - Download models: `ollama pull codellama:7b-instruct`

3. **Out of memory errors**
   - Use smaller models or increase RAM

4. **GPU not detected**
   - Check GPU drivers and Ollama GPU support

### Verification Commands

```bash
# Check Python dependencies
pip list | grep -E "(fastapi|uvicorn|langchain)"

# Check Ollama installation
ollama --version

# Check available models
ollama list

# Test model loading
ollama run codellama:7b-instruct "print('Hello, World!')"
```

## 📚 Documentation

- [Detailed Installation Guide](INSTALLATION.md)
- [GitHub Integration Guide](GITHUB_INTEGRATION.md)
- [API Documentation](http://localhost:8000/docs) (when server is running)
- [Model Configuration](backend-ai/main.py#L25-L50)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the [Installation Guide](INSTALLATION.md)
3. Open an issue on GitHub with detailed error information

## 📄 License

This project is open source. Feel free to contribute! # lilysmokes
# lilysmokes
