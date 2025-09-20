# Backend Setup Instructions

## Overview

This backend server creates Coral sessions, spawns agents, and facilitates communication between the webapp and the agent system.

## How It Works

1. **Session Creation**: When a user sends a prompt, the backend automatically creates a Coral session with all 4 agents (orchestrator, summarizer, risk, voice)
2. **Agent Communication**: The orchestrator agent uses the backend tools to send progress updates and final results
3. **Real-time Updates**: The webapp receives live updates via Server-Sent Events (SSE)

## Setup & Running

### 1. Install Dependencies
```bash
pip install -r requirements_backend.txt
```

### 2. Set Environment Variables

**Option A: Create a `.env` file** (Recommended)
Create a `.env` file in the project root with:
```bash
# API Keys for LLM Models
ORCHESTRATOR_API_KEY=your_nebius_api_key
SUMMARIZER_API_KEY=your_aiml_api_key
RISK_API_KEY=your_aiml_api_key
VOICE_API_KEY=your_aiml_api_key

# GitHub API Access
GITHUB_TOKEN=your_github_personal_access_token

# ElevenLabs Voice Synthesis
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_preferred_voice_id

# Optional ElevenLabs Settings
ELEVENLABS_BASE_URL=https://api.elevenlabs.io/v1
ELEVENLABS_MODEL_ID=eleven_turbo_v2_5
VOICE_OVER_DIR=voice_over_outputs
```

**Option B: Export Environment Variables**
```bash
export ORCHESTRATOR_API_KEY="your_nebius_api_key"
export SUMMARIZER_API_KEY="your_aiml_api_key"
export RISK_API_KEY="your_aiml_api_key"
export VOICE_API_KEY="your_aiml_api_key"
export GITHUB_TOKEN="your_github_token"
export ELEVENLABS_API_KEY="your_elevenlabs_key"
export ELEVENLABS_VOICE_ID="your_voice_id"
```

**Required API Keys:**
- **NEBIUS API Key**: For orchestrator agent (GPT-OSS-120B model)
- **AIML API Keys**: For summarizer, risk, and voice agents (GPT-5 model)
- **GitHub Token**: For accessing GitHub PR data
- **ElevenLabs Keys**: For voice synthesis (optional for voice features)

### 3. Start Coral Server
```bash
# In the coral-server directory
./gradlew run
```
*Coral server should be running on http://localhost:5555*

### 4. Start Backend Server
```bash
python backend_server.py
```
*Backend will run on http://localhost:8000*

### 5. Test the System

#### Direct API Test:
```bash
curl "http://localhost:8000/prompt?message=Analyze%20https://github.com/microsoft/vscode/pull/123"
```

#### Webapp Integration:
Update your webapp's `useSSEConnection.ts` to use:
```typescript
const apiUrl = 'http://localhost:8000';
const url = `${apiUrl}/prompt?message=${encodeURIComponent(prompt)}`;
```

## Architecture Flow

```
User Request → Backend Server → Creates Coral Session → Spawns 4 Agents
                     ↓
Agent Tools → Backend Server → SSE Stream → Webapp Updates
```

## API Endpoints

- `GET /prompt?message=<text>` - Main SSE endpoint for webapp
- `POST /agent/message` - Agents send progress updates here
- `POST /callback` - Orchestrator sends final results here
- `GET /health` - Health check

## Agent Tools

The agents now have these tools available:

- `send_action_update()` - Send progress updates
- `webhook_callback()` - Send final results (existing pattern)
- `send_error()` - Send error messages
- `send_completion()` - Alternative completion method

## Troubleshooting

1. **Coral Server Connection**: Ensure Coral server is running on port 5555
2. **Environment Variables**: Check all API keys are properly set
3. **Agent Registration**: Check coral-server logs for agent registration status
4. **Backend Logs**: Check backend console for session creation and message flow

## Example Flow

1. User enters: "Analyze https://github.com/microsoft/vscode/pull/123"
2. Backend creates Coral session with 4 agents
3. Orchestrator receives the request and calls:
   - `send_action_update("orchestrator", "Starting Analysis", "Processing PR", "running")`
   - Mentions summarizer-agent for PR analysis
   - `send_action_update("orchestrator", "Getting Summary", "Waiting for analysis", "running")`
   - `webhook_callback("request_id", "PR summary here", "Risk report", "voice_url")`
4. Webapp receives real-time updates via SSE events

The system is now complete with automatic session creation and agent spawning! 🎉