@echo off
echo Starting Online Agent Service...
echo.
echo Make sure you have set the following environment variables:
echo - OPENAI_API_KEY (for OpenAI models)
echo - ANTHROPIC_API_KEY (for Anthropic models)
echo.
echo Installing dependencies...
cd backend-ai
pip install -r requirements.txt
echo.
echo Starting Online Agent Service on port 8001...
python online_agent_service.py
pause

