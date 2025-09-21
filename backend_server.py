#!/usr/bin/env python3
"""
Simple Backend Server for Agent Communication
Listens for agent messages and provides SSE endpoint for webapp
"""

import asyncio
import json
import os
import re
import sys
import time
import requests
import uuid
from datetime import datetime
from typing import Dict, List, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Agent Communication Backend", version="1.0.0")

# Enable CORS for webapp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CORAL_SERVER_URL = "http://localhost:5555"

# In-memory storage for messages and active connections
class MessageStore:
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.connections: List[asyncio.Queue] = []
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.user_message_queues: Dict[str, List[str]] = {}  # sessionId -> list of user messages

    def add_connection(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.connections.append(queue)
        return queue

    def remove_connection(self, queue: asyncio.Queue):
        if queue in self.connections:
            self.connections.remove(queue)

    async def add_message(self, message: Dict[str, Any]):
        self.messages.append(message)
        # Broadcast to all connected clients
        for queue in self.connections:
            try:
                await queue.put(message)
            except:
                # Remove broken connections
                self.connections = [q for q in self.connections if q != queue]

    def create_session(self, session_id: str, session_data: Dict[str, Any]):
        self.sessions[session_id] = session_data
        self.user_message_queues[session_id] = []  # Initialize message queue for this session

    def add_user_message(self, session_id: str, message: str):
        """Add a user message to the session's queue"""
        if session_id not in self.user_message_queues:
            self.user_message_queues[session_id] = []
        self.user_message_queues[session_id].append(message)
        print(f"📝 Added user message to session {session_id}: {message}")

    def get_user_message(self, session_id: str) -> str:
        """Get the next user message for a session (FIFO)"""
        if session_id in self.user_message_queues and self.user_message_queues[session_id]:
            message = self.user_message_queues[session_id].pop(0)
            print(f"📤 Retrieved user message for session {session_id}: {message}")
            return message
        return None

    def get_session(self, session_id: str) -> Dict[str, Any]:
        return self.sessions.get(session_id, {})

message_store = MessageStore()

def substitute_env_variables(payload):
    """Substitute environment variables in the payload"""
    def replace_env_var(match):
        var_name = match.group(1)
        env_value = os.getenv(var_name)
        if env_value is None:
            print(f"⚠️  Warning: Environment variable {var_name} not found")
            return f"MISSING_{var_name}"
        return env_value

    # Convert payload to JSON string, replace variables, then convert back
    payload_str = json.dumps(payload)
    # Replace {{VARIABLE_NAME}} with actual environment variable values
    payload_str = re.sub(r'\{\{([^}]+)\}\}', replace_env_var, payload_str)
    return json.loads(payload_str)

def create_coral_session():
    """Create a session with the Coral Server"""
    session_payload = {
        "applicationId": "pr-summarizer-app",
        "privacyKey": "pr-analysis-key",
        "agentGraphRequest": {
            "agents": [
                {
                    "id": {"name": "orchestrator-agent", "version": "1.0.0"},
                    "name": "orchestrator-agent",
                    "coralPlugins": [],
                    "provider": {"type": "local", "runtime": "executable"},
                    "blocking": True,
                    "options": {
                        "ORCHESTRATOR_API_KEY": {"type": "string", "value": "{{ORCHESTRATOR_API_KEY}}"},
                        "GITHUB_TOKEN": {"type": "string", "value": "{{GITHUB_TOKEN}}"}
                    },
                    "customToolAccess": ["send_action_update", "send_completion", "webhook_callback"]
                },
                {
                    "id": {"name": "summarizer-agent", "version": "1.0.0"},
                    "name": "summarizer-agent",
                    "coralPlugins": [],
                    "provider": {"type": "local", "runtime": "executable"},
                    "blocking": True,
                    "options": {
                        "SUMMARIZER_API_KEY": {"type": "string", "value": "{{SUMMARIZER_API_KEY}}"},
                        "GITHUB_TOKEN": {"type": "string", "value": "{{GITHUB_TOKEN}}"}
                    },
                    "customToolAccess": ["send_action_update"]
                },
                {
                    "id": {"name": "risk-agent", "version": "1.0.0"},
                    "name": "risk-agent",
                    "coralPlugins": [],
                    "provider": {"type": "local", "runtime": "executable"},
                    "blocking": True,
                    "options": {
                        "RISK_API_KEY": {"type": "string", "value": "{{RISK_API_KEY}}"},
                        "GITHUB_TOKEN": {"type": "string", "value": "{{GITHUB_TOKEN}}"}
                    },
                    "customToolAccess": ["send_action_update"]
                },
                {
                    "id": {"name": "voice-agent", "version": "1.0.0"},
                    "name": "voice-agent",
                    "coralPlugins": [],
                    "provider": {"type": "local", "runtime": "executable"},
                    "blocking": True,
                    "options": {
                        "VOICE_API_KEY": {"type": "string", "value": "{{VOICE_API_KEY}}"},
                        "GITHUB_TOKEN": {"type": "string", "value": "{{GITHUB_TOKEN}}"},
                        "ELEVENLABS_API_KEY": {"type": "string", "value": "{{ELEVENLABS_API_KEY}}"},
                        "ELEVENLABS_VOICE_ID": {"type": "string", "value": "{{ELEVENLABS_VOICE_ID}}"},
                        "ELEVENLABS_BASE_URL": {"type": "string", "value": "https://api.elevenlabs.io/v1"},
                        "ELEVENLABS_MODEL_ID": {"type": "string", "value": "eleven_turbo_v2_5"},
                        "VOICE_OVER_DIR": {"type": "string", "value": "voice_over_outputs"}
                    },
                    "customToolAccess": ["send_action_update"]
                }
            ],
            "customTools": {
                "send_action_update": {
                    "transport": {
                        "type": "http",
                        "url": "http://localhost:8000/agent/message"
                    },
                    "toolSchema": {
                        "name": "send_action_update",
                        "description": "Send progress update to webapp",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "agent_id": {
                                    "type": "string",
                                    "description": "ID of the agent sending the update"
                                },
                                "action": {
                                    "type": "string",
                                    "description": "Brief description of the action"
                                },
                                "detail": {
                                    "type": "string",
                                    "description": "Detailed description"
                                },
                                "status": {
                                    "type": "string",
                                    "description": "Status: running, completed, failed"
                                }
                            },
                            "required": ["agent_id", "action", "detail", "status"]
                        }
                    }
                },
                "send_completion": {
                    "transport": {
                        "type": "http",
                        "url": "http://localhost:8000/agent/message"
                    },
                    "toolSchema": {
                        "name": "send_completion",
                        "description": "Send completion results to webapp",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "agent_id": {
                                    "type": "string",
                                    "description": "ID of the agent sending completion"
                                },
                                "summary": {
                                    "type": "string",
                                    "description": "Analysis summary"
                                },
                                "risk_report": {
                                    "type": "string",
                                    "description": "Risk assessment report"
                                },
                                "voice_url": {
                                    "type": "string",
                                    "description": "URL to generated voice file"
                                },
                                "output": {
                                    "type": "string",
                                    "description": "Final combined output"
                                }
                            },
                            "required": ["agent_id", "summary"]
                        }
                    }
                },
                "webhook_callback": {
                    "transport": {
                        "type": "http",
                        "url": "http://localhost:8000/callback"
                    },
                    "toolSchema": {
                        "name": "webhook_callback",
                        "description": "Send final results to webapp via callback",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "request_id": {
                                    "type": "string",
                                    "description": "Request ID to respond to"
                                },
                                "summary": {
                                    "type": "string",
                                    "description": "PR analysis summary"
                                },
                                "risk_report": {
                                    "type": "string",
                                    "description": "Security risk assessment"
                                },
                                "voice_url": {
                                    "type": "string",
                                    "description": "URL to generated voice file"
                                }
                            },
                            "required": ["request_id", "summary"]
                        }
                    }
                }
            },
            "groups": [["orchestrator-agent", "summarizer-agent", "risk-agent", "voice-agent"]]
        }
    }

    # Substitute environment variables in the payload
    session_payload = substitute_env_variables(session_payload)

    # Log which environment variables we're using
    print("🔑 Loading environment variables:")
    for var_name in ["ORCHESTRATOR_API_KEY", "SUMMARIZER_API_KEY", "RISK_API_KEY", "VOICE_API_KEY", "GITHUB_TOKEN", "ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID"]:
        value = os.getenv(var_name)
        if value:
            print(f"  ✅ {var_name}: {'*' * min(len(value), 8)}...")
        else:
            print(f"  ❌ {var_name}: MISSING")

    try:
        response = requests.post(
            f"{CORAL_SERVER_URL}/api/v1/sessions",
            json=session_payload,
            timeout=30
        )

        if response.status_code == 200:
            session_info = response.json()
            print(f"✅ Created Coral session: {session_info['sessionId']}")
            return session_info
        else:
            print(f"❌ Failed to create Coral session: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error creating Coral session: {str(e)}")
        return None

def send_message_to_orchestrator(session_id: str, application_id: str, privacy_key: str, message: str):
    """Send a message to the orchestrator agent via Coral Server"""
    try:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        formatted_message = f"User Request (ID: {request_id}): {message}"

        # Store the message in the session's queue for the orchestrator to poll
        message_store.add_user_message(session_id, formatted_message)
        print(f"📤 Queued request for orchestrator in session {session_id}: {formatted_message}")

        # Return the request ID so agents can reference it
        return request_id

    except Exception as e:
        print(f"❌ Error preparing message for orchestrator: {str(e)}")
        return None

# Request models
class AgentMessage(BaseModel):
    agent_id: str
    event_type: str  # "action", "complete", "error"
    data: Dict[str, Any]

class CallbackMessage(BaseModel):
    request_id: str
    summary: str = ""
    risk_report: str = ""
    voice_url: str = ""
    output: str = ""

@app.post("/agent/message/{session_id}/{agent_id}")
async def receive_agent_message(session_id: str, agent_id: str, request_data: dict):
    """Receive a message from an agent (custom tool call)"""

    # Handle both custom tool format and our internal format
    if "agent_id" in request_data:
        # Our internal format
        agent_id = request_data["agent_id"]
        action = request_data.get("action", "Unknown Action")
        detail = request_data.get("detail", "")
        status = request_data.get("status", "running")

        # send_action_update calls are ALWAYS action updates, never final completions
        # Final completions only come from webhook_callback endpoint
        if status == "failed":
            event_type = "error"
            sse_message = {"error": f"{action}: {detail}"}
        else:
            event_type = "action"
            sse_message = {
                "timestamp": int(time.time() * 1000),
                "action": action,
                "detail": detail,
                "status": status,
                "source": agent_id
            }
    else:
        # Direct custom tool call format - extract relevant data
        agent_id = request_data.get("name", "unknown")

        if "summary" in request_data:
            # This is a completion message
            event_type = "complete"
            sse_message = {
                "summary": request_data.get("summary", ""),
                "risk_report": request_data.get("risk_report", ""),
                "output": request_data.get("output", request_data.get("summary", "")),
                "voice_url": request_data.get("voice_url", "")
            }
        elif "error" in request_data:
            # This is an error message
            event_type = "error"
            sse_message = {"error": request_data.get("error", "Unknown error")}
        else:
            # This is an action update
            event_type = "action"
            sse_message = {
                "timestamp": int(time.time() * 1000),
                "action": request_data.get("action", "Processing"),
                "detail": request_data.get("detail", "Agent is working..."),
                "status": request_data.get("status", "running"),
                "source": agent_id
            }

    # Store and broadcast the message
    await message_store.add_message({
        "event": event_type,
        "data": json.dumps(sse_message)
    })

    print(f"📨 Received {event_type} from {agent_id}: {json.dumps(sse_message, indent=2)}")
    return {"status": "received"}

@app.post("/callback/{session_id}/{agent_id}")
async def receive_callback(session_id: str, agent_id: str, callback: CallbackMessage):
    """Receive callback from orchestrator (webhook_callback tool)"""

    # Format as completion event
    complete_data = {
        "summary": callback.summary,
        "risk_report": callback.risk_report,
        "output": callback.output or callback.summary,
        "voice_url": callback.voice_url
    }

    await message_store.add_message({
        "event": "complete",
        "data": json.dumps(complete_data)
    })

    return {"status": "received"}

@app.get("/prompt")
async def handle_prompt(message: str):
    """Handle prompt from webapp and return SSE stream"""

    async def event_stream():
        # Create a queue for this connection
        queue = message_store.add_connection()

        try:
            # Send initial message
            initial_action = {
                "timestamp": int(time.time() * 1000),
                "action": "Creating Session",
                "detail": "Setting up agent environment...",
                "status": "running",
                "source": "backend"
            }

            yield f"event: action\ndata: {json.dumps(initial_action)}\n\n"

            # Create Coral session
            session_info = create_coral_session()
            if not session_info:
                error_msg = {"error": "Failed to create agent session"}
                yield f"event: error\ndata: {json.dumps(error_msg)}\n\n"
                return

            # Store session info
            message_store.create_session(session_info['sessionId'], session_info)

            # Send session created message
            session_action = {
                "timestamp": int(time.time() * 1000),
                "action": "Session Created",
                "detail": f"Agent session {session_info['sessionId']} is ready",
                "status": "completed",
                "source": "backend"
            }

            yield f"event: action\ndata: {json.dumps(session_action)}\n\n"

            # Send message to orchestrator
            processing_action = {
                "timestamp": int(time.time() * 1000),
                "action": "Processing Request",
                "detail": f"Sending request to orchestrator agent...",
                "status": "running",
                "source": "backend"
            }

            yield f"event: action\ndata: {json.dumps(processing_action)}\n\n"

            # Send the user message to orchestrator
            request_id = send_message_to_orchestrator(
                session_info['sessionId'],
                session_info['applicationId'],
                session_info['privacyKey'],
                message
            )

            if not request_id:
                error_msg = {"error": "Failed to send message to orchestrator"}
                yield f"event: error\ndata: {json.dumps(error_msg)}\n\n"
                return

            # Now listen for messages from agents
            while True:
                try:
                    # Wait for a message with timeout
                    msg = await asyncio.wait_for(queue.get(), timeout=60.0)
                    yield f"event: {msg['event']}\ndata: {msg['data']}\n\n"

                    # If it's a complete or error event, end the stream
                    if msg['event'] in ['complete', 'error']:
                        break

                except asyncio.TimeoutError:
                    # Send keepalive
                    keepalive = {
                        "timestamp": int(time.time() * 1000),
                        "action": "Waiting for Analysis",
                        "detail": "Agents are processing your request...",
                        "status": "running",
                        "source": "backend"
                    }
                    yield f"event: action\ndata: {json.dumps(keepalive)}\n\n"

        finally:
            message_store.remove_connection(queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_connections": len(message_store.connections),
        "total_messages": len(message_store.messages)
    }

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "Agent Communication Backend",
        "endpoints": {
            "POST /agent/message": "Receive messages from agents",
            "POST /callback": "Receive callback from orchestrator",
            "GET /prompt": "SSE endpoint for webapp",
            "GET /health": "Health check"
        }
    }

@app.get("/session/{session_id}/message")
async def get_user_message_endpoint(session_id: str):
    """Get the next user message for a session (for agents to poll)"""
    message = message_store.get_user_message(session_id)
    if message:
        return {"message": message, "has_message": True}
    else:
        return {"message": None, "has_message": False}

if __name__ == "__main__":
    print("🚀 Starting Agent Communication Backend...")
    print("📡 Backend will listen on http://localhost:8000")
    print("🔗 Webapp should connect to: http://localhost:8000/prompt?message=<your_message>")
    print("🤖 Agents should send messages to: http://localhost:8000/agent/message")

    uvicorn.run(
        "backend_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )