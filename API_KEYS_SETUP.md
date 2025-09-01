# API Keys Setup Guide

## Overview
This project uses multiple AI services that require API keys. Follow this guide to set up your API keys securely.

## Step 1: Get Your API Keys

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the generated key (starts with `sk-`)

### Mistral API Key
1. Go to [Mistral Console](https://console.mistral.ai/api-keys/)
2. Sign in or create an account
3. Click "Create new key"
4. Copy the generated key

### Google Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key

## Step 2: Configure Your Environment

### Option A: Using .env file (Recommended)
1. Navigate to the `backend-ai` folder
2. Copy `env_example.txt` to `.env`:
   ```bash
   cp env_example.txt .env
   ```
3. Edit the `.env` file and replace the placeholder values:
   ```
   OPENAI_API_KEY=sk-your-actual-openai-key-here
   MISTRAL_API_KEY=your-actual-mistral-key-here
   GEMINI_API_KEY=your-actual-gemini-key-here
   ```

### Option B: Environment Variables
Set these environment variables in your system:
```bash
export OPENAI_API_KEY="sk-your-actual-openai-key-here"
export MISTRAL_API_KEY="your-actual-mistral-key-here"
export GEMINI_API_KEY="your-actual-gemini-key-here"
```

## Step 3: Verify Setup

1. Run the backend service:
   ```bash
   cd backend-ai
   python main.py
   ```

2. Check the console output - it should show which models are available

## Security Notes

⚠️ **IMPORTANT SECURITY WARNINGS:**
- Never commit your `.env` file to version control
- Never share your API keys publicly
- The `.env` file is already in `.gitignore` to prevent accidental commits
- API keys have usage limits and costs - monitor your usage

## Troubleshooting

### "API key not found" error
- Make sure your `.env` file exists in the `backend-ai` folder
- Check that the API key format is correct (no extra spaces)
- Verify the API key is valid by testing it on the provider's website

### "Module not found" error
- Install dependencies: `pip install -r requirements.txt`
- Make sure you're in the virtual environment

### Service not starting
- Check that at least one API key is configured
- Verify your internet connection
- Check the console for specific error messages

## Support

If you encounter issues:
1. Check the console output for error messages
2. Verify your API keys are correct
3. Ensure all dependencies are installed
4. Check the provider's status page for service issues

