@echo off
echo Starting AI Coding Assistant Servers...

echo.
echo Starting Backend Server...
start "Backend Server" cmd /k "cd backend-ai && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo Waiting 3 seconds for backend to start...
timeout /t 3 /nobreak >nul

echo.
echo Starting Frontend Server...
start "Frontend Server" cmd /k "cd offline-ai-frontend && npm run dev"

echo.
echo Both servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173 (Vite default)
echo.
pause 