@echo off
echo ========================================
echo Multi-Agent AI System Setup
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)
echo ✅ Python is installed

echo.
echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    echo Please install Node.js 16+ from https://nodejs.org
    pause
    exit /b 1
)
echo ✅ Node.js is installed

echo.
echo Installing Python dependencies...
cd backend-ai
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)
echo ✅ Python dependencies installed

echo.
echo Checking Ollama installation...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Ollama is not installed
    echo.
    echo Please install Ollama:
    echo 1. Download from https://ollama.ai
    echo 2. Or run: winget install Ollama.Ollama
    echo.
    echo After installing Ollama, run this script again.
    pause
    exit /b 1
)
echo ✅ Ollama is installed

echo.
echo Starting Ollama service...
start /B ollama serve
timeout /t 3 /nobreak >nul

echo.
echo Downloading AI models...
echo This may take several minutes...
ollama pull codellama:7b-instruct
ollama pull mistral
ollama pull llama2

echo.
echo Installing frontend dependencies...
cd ..\offline-ai-frontend
npm install
if errorlevel 1 (
    echo ❌ Failed to install frontend dependencies
    pause
    exit /b 1
)
echo ✅ Frontend dependencies installed

echo.
echo ========================================
echo ✅ Setup completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Start the backend: cd backend-ai ^&^& python main.py
echo 2. Start the frontend: cd offline-ai-frontend ^&^& npm run dev
echo.
echo Backend will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:5173
echo.
pause 