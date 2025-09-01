# Online Agent Service Setup Guide

This guide explains how to set up and use the online agent service with LangChain integration for manual agent workflows.

## Overview

The online agent service provides integration with cloud-based AI models (OpenAI, Anthropic) for the manual agent workflow. It uses LangChain for conversation tracking and memory management.

## Features

- **Online Model Integration**: Support for GPT-4, GPT-3.5 Turbo, Claude 3 Opus, Sonnet, and Haiku
- **LangChain Integration**: Advanced conversation tracking and memory management
- **Real-time Communication**: See conversations between agents in real-time
- **Database Integration**: Persistent conversation history
- **Streaming Support**: Real-time response streaming

## Prerequisites

1. **Python 3.8+** installed
2. **API Keys** for online models:
   - OpenAI API key (for GPT models)
   - Anthropic API key (for Claude models)

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend-ai
pip install -r requirements.txt
```

### 2. Set Environment Variables

Set your API keys as environment variables:

**Windows:**
```cmd
set OPENAI_API_KEY=your_openai_api_key_here
set ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY=your_openai_api_key_here
export ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 3. Start the Online Agent Service

```bash
cd backend-ai
python online_agent_service.py
```

The service will start on `http://localhost:8001`

### 4. Start the Frontend

In a new terminal:
```bash
cd offline-ai-frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

### 1. Access Manual Agents Page

Navigate to the "Manual Agents" tab in the frontend.

### 2. Switch to Online Mode

Click the "Online" button in the mode toggle to enable online models.

### 3. Create Agent Boxes

- Click "+ Create an empty box" to add agents
- Configure each agent with:
  - **Role**: Coordinator, Coder, Tester, Runner, or Custom
  - **Model**: Choose from available online models
  - **System Prompt**: Custom instructions for the agent

### 4. Connect Agents

- Drag from connection handles to create agent connections
- Agents will communicate based on these connections

### 5. Run Workflow

- Enter a task prompt
- Click "Run Flow" to execute the workflow
- Watch real-time conversation between agents

## Available Models

### OpenAI Models
- **GPT-4**: Most capable model, best for complex tasks
- **GPT-3.5 Turbo**: Fast and cost-effective, good for most tasks

### Anthropic Models
- **Claude 3 Opus**: Most capable Claude model
- **Claude 3 Sonnet**: Balanced performance and cost
- **Claude 3 Haiku**: Fastest and most cost-effective

## API Endpoints

The online agent service provides the following endpoints:

- `GET /` - Service information
- `GET /health` - Health check
- `GET /models` - Available models
- `POST /run-workflow` - Execute agent workflow
- `GET /workflow-status/{id}` - Get workflow status
- `GET /conversations` - Get conversation history
- `GET /conversations/{id}` - Get specific conversation

## Conversation Tracking

The service uses LangChain's conversation memory to:
- Track all agent interactions
- Maintain context across messages
- Store conversation history in database
- Enable real-time conversation viewing

## Troubleshooting

### Service Won't Start
- Check that all dependencies are installed
- Verify API keys are set correctly
- Ensure port 8001 is available

### API Key Errors
- Verify your API keys are valid
- Check that you have sufficient credits
- Ensure the keys are set as environment variables

### Connection Issues
- Check that both services are running
- Verify frontend is connecting to correct ports
- Check browser console for errors

## Architecture

```
Frontend (Port 5173)
    ↓
Online Agent Service (Port 8001)
    ↓
LangChain + Online Models
    ↓
Database (Conversation History)
```

## Development

### Adding New Models

To add new online models:

1. Update `ONLINE_MODEL_CONFIGS` in `online_agent_service.py`
2. Add corresponding LangChain integration
3. Update frontend model options

### Customizing Agent Behavior

Modify the `system_prompt` field in agent configuration to customize behavior.

## Security Notes

- Never commit API keys to version control
- Use environment variables for sensitive data
- Consider rate limiting for production use
- Monitor API usage and costs

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the API documentation at `http://localhost:8001/docs`
3. Check the console logs for error messages

