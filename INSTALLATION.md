# Installation Guide

## What Gets Installed vs. What You Need to Install Manually

### ✅ Automatically Installed (via `requirements.txt`)

When you run `pip install -r requirements.txt`, these Python packages are installed:

- **FastAPI** - Web framework for the backend API
- **Uvicorn** - ASGI server to run the backend
- **Pydantic** - Data validation and serialization
- **LangChain-Ollama** - Integration library for Ollama
- **Python-Multipart** - File upload handling
- **Requests** - HTTP library for API calls
- **Typing-Extensions** - Type hint support

### ❌ NOT Automatically Installed (Manual Steps Required)

#### 1. Ollama (AI Model Server)
**What it is:** The actual AI model server that runs the LLMs locally
**Why it's not in requirements.txt:** Ollama is a system-level application, not a Python package

**Installation:**
```bash
# Windows
winget install Ollama.Ollama
# Or download from https://ollama.ai

# macOS
brew install ollama
# Or download from https://ollama.ai

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

#### 2. LLM Models (AI Models)
**What they are:** The actual AI models like CodeLlama, Mistral, etc.
**Why they're not in requirements.txt:** Models are downloaded separately via Ollama

**Installation:**
```bash
# After installing Ollama, download the models:
ollama pull codellama:7b-instruct  # Primary model for code generation
ollama pull mistral                 # General purpose model
ollama pull llama2                  # Alternative model
```

## Quick Setup (Recommended)

### Option 1: Use the Setup Script
```bash
# Run the automated setup script
python setup.py
```

This script will:
- ✅ Install Python dependencies
- ✅ Check if Ollama is installed
- ✅ Guide you through Ollama installation if needed
- ✅ Download required LLM models
- ✅ Create startup scripts

### Option 2: Manual Installation

#### Step 1: Install Python Dependencies
```bash
cd backend-ai
pip install -r requirements.txt
```

#### Step 2: Install Ollama
```bash
# Windows
winget install Ollama.Ollama

# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Step 3: Download Models
```bash
# Start Ollama service
ollama serve

# In another terminal, download models
ollama pull codellama:7b-instruct
ollama pull mistral
ollama pull llama2
```

#### Step 4: Install Frontend Dependencies
```bash
cd offline-ai-frontend
npm install
```

## System Requirements

### Minimum Requirements
- **Python:** 3.8 or higher
- **Node.js:** 16 or higher
- **RAM:** 8GB (16GB recommended for larger models)
- **Storage:** 10GB free space for models
- **GPU:** Optional but recommended for better performance

### Recommended Requirements
- **Python:** 3.9 or higher
- **Node.js:** 18 or higher
- **RAM:** 16GB or more
- **Storage:** 20GB free space
- **GPU:** NVIDIA GPU with 8GB+ VRAM

## Model Sizes and Download Times

| Model | Size | Download Time (50 Mbps) | RAM Usage |
|-------|------|-------------------------|-----------|
| codellama:7b-instruct | ~4GB | ~10 minutes | 8GB |
| mistral | ~4GB | ~10 minutes | 8GB |
| llama2 | ~4GB | ~10 minutes | 8GB |

## Troubleshooting

### Common Issues

#### 1. "ollama command not found"
**Solution:** Ollama isn't installed or not in PATH
```bash
# Reinstall Ollama
# Windows: Download from https://ollama.ai
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh
```

#### 2. "Model not found" errors
**Solution:** Models haven't been downloaded
```bash
# Download the required models
ollama pull codellama:7b-instruct
ollama pull mistral
ollama pull llama2
```

#### 3. Out of memory errors
**Solution:** Reduce model size or increase RAM
```bash
# Use smaller models
ollama pull codellama:3b-instruct  # Smaller version
ollama pull mistral:7b             # Smaller version
```

#### 4. GPU not detected
**Solution:** Check GPU drivers and Ollama GPU support
```bash
# Check if GPU is available
nvidia-smi

# Check Ollama GPU support
ollama list
```

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

## Environment Variables (Optional)

You can set these environment variables for customization:

```bash
# Model configuration
export OLLAMA_HOST=127.0.0.1
export OLLAMA_ORIGINS=*

# GPU configuration
export CUDA_VISIBLE_DEVICES=0

# Backend configuration
export BACKEND_PORT=8000
export BACKEND_HOST=0.0.0.0
```

## Next Steps After Installation

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

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all dependencies are installed correctly
3. Check the logs for error messages
4. Open an issue on GitHub with detailed error information 