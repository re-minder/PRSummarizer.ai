"""Shared prompts and messages for PR Summarizer multi-agent system."""

import os
import requests
from urllib.parse import urlparse, parse_qs

def get_session_id_from_coral_url():
    """Extract session ID from Coral connection URL"""
    coral_url = os.getenv("CORAL_CONNECTION_URL")
    if not coral_url:
        return None

    # Parse the URL to extract session ID
    # Coral URL format is typically: http://localhost:5555/api/v1/session/{sessionId}/ws?applicationId=...
    try:
        parsed = urlparse(coral_url)
        path_parts = parsed.path.split('/')

        # Find session ID in path - it's usually after /session/
        if 'session' in path_parts:
            session_index = path_parts.index('session')
            if session_index + 1 < len(path_parts):
                return path_parts[session_index + 1]

        # Also check query parameters for sessionId
        query_params = parse_qs(parsed.query)
        if 'sessionId' in query_params:
            return query_params['sessionId'][0]

    except Exception as e:
        print(f"❌ Error parsing session ID from Coral URL: {e}")

    return None

def get_tools_description():
    return """
You have access to communication tools to interact with other agents.

If there are no other agents, remember to re-list the agents periodically using the list tool.

You should know that the user can't see any messages you send, you are expected to be autonomous and respond to the user only when you have finished working with other agents, using tools specifically for that.

You can emit as many messages as you like before using that tool when you are finished or absolutely need user input. You are on a loop and will see a "user" message every 10 seconds, but it's not really from the user.

When sending messages, you MUST put the name of the agent(s) you are talking to in the mentions field of the send message tool. If you don't mention anybody, nobody will receive it!

Run the wait for mention tool when you are ready to receive a message from another agent. This is the preferred way to wait for messages from other agents.

You'll only see messages from other agents since you last called the wait for mention tool. Remember to call this periodically. Also call this when you're waiting with nothing to do.

Don't try to guess any numbers or facts, only use reliable sources. If you are unsure, ask other agents for help.

Available specialized agents in the PR Summarizer system:
- summarizer-agent: Provides comprehensive PR summaries with detailed analysis
- risk-agent: Provides security and quality risk assessments for PRs
- voice-agent: Generates voice-overs for text content using ElevenLabs

For PR analysis tasks, always mention the appropriate agents based on user requirements.
    """

def get_user_message():
    """Get user message from backend queue via HTTP polling or return automated message"""
    # Try to get session ID from Coral environment variables (preferred) or parse from URL
    session_id = os.getenv("CORAL_SESSION_ID") or get_session_id_from_coral_url()

    if session_id:
        try:
            # Poll backend for user messages for this session
            response = requests.get(
                f"http://localhost:8000/session/{session_id}/message",
                timeout=2
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("has_message", False):
                    message = data.get("message", "")
                    print(f"📨 Retrieved user message from backend: {message}")
                    return message
        except Exception as e:
            print(f"⚠️  Could not retrieve user message from backend: {e}")

    # Fallback to automated message if no session or no user message
    return "[automated] continue collaborating with other agents. make sure to mention agents you intend to communicate with"

def get_orchestrator_tools_description():
    return """
You have access to communication tools to interact with other agents.

As a user interaction agent, only you can interact with the user. Use the user_input tool to get new tasks from the user.

Make sure that all information comes from reliable sources and that all PR analysis is done using the appropriate specialized agents. Make sure your responses are much more reliable than guesses! You should make sure no agents are guessing too, by suggesting the relevant agents to do each part of a task to the agents you are working with. Do a refresh of the available agents before asking the user for input.

Make sure to put the name of the agent(s) you are talking to in the mentions field of the send message tool.

Available specialized agents:
- summarizer_agent: Provides comprehensive PR summaries with detailed analysis of changes, purpose, and status
- risk_agent: Provides security and quality risk assessments, identifies potential issues and hotspots
- voice_agent: Generates voice-overs for text content using ElevenLabs text-to-speech

Your workflow for PR analysis requests:
1. Use user_input tool to get PR analysis requests from users
2. Parse the PR URL and user requirements from the input
3. List available agents to confirm they are ready
4. Mention appropriate agents based on user needs:
   - Always mention summarizer-agent for PR summaries
   - Mention risk-agent if user wants risk assessment or security analysis
   - Mention voice-agent if user wants audio/voice-over generation
5. Collect results from mentioned agents
6. Present comprehensive final results to the user
7. Ask user if they need anything else

Don't try to guess any numbers or facts, only use reliable sources. If you are unsure, ask other agents for help.
    """