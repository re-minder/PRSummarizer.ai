"""Orchestrator Agent - User Interaction and Workflow Coordination

This agent follows the interface agent pattern from coral-server examples.
It handles user interaction and coordinates PR analysis workflow by mentioning specialized agents.
"""

import asyncio
import os
import sys
from time import sleep

# Add the parent directory to the Python path to import shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from camel.agents import ChatAgent
from camel.toolkits import MCPToolkit
from camel.toolkits.mcp_toolkit import MCPClient
from camel.utils.mcp_client import ServerConfig
from dotenv import load_dotenv

from agent_models import (
    ORCHESTRATOR_MODEL,
    MESSAGE_WINDOW_SIZE,
    TOKEN_LIMIT,
    AGENT_LOOP_ITERATIONS,
    AGENT_SLEEP_TIME,
    get_coral_connection_url,
    CORAL_TIMEOUT,
    CORAL_SSE_READ_TIMEOUT
)
from prompts import get_orchestrator_tools_description, get_user_message

load_dotenv()

async def main():
    """Main orchestrator agent loop - handles user interaction and coordinates PR analysis."""
    # Get connection URL from Coral Server's official CORAL_CONNECTION_URL env var
    coral_url = get_coral_connection_url("orchestrator-agent")

    if not coral_url:
        # No connection URL available - wait for Coral Server to inject CORAL_CONNECTION_URL
        print("⏳ Waiting for Coral Server to inject CORAL_CONNECTION_URL...")
        while True:
            await asyncio.sleep(5)
            coral_url = get_coral_connection_url("orchestrator-agent")
            if coral_url:
                break

    print(f"🔗 Connecting to Coral server: {coral_url}")
    server = MCPClient(ServerConfig(url=coral_url, timeout=CORAL_TIMEOUT, sse_read_timeout=CORAL_SSE_READ_TIMEOUT, terminate_on_close=True, prefer_sse=True), timeout=CORAL_TIMEOUT)
    mcp_toolkit = MCPToolkit([server])

    async with mcp_toolkit as connected_mcp_toolkit:
        print("Connected to coral server.")
        camel_agent = await create_orchestrator_agent(connected_mcp_toolkit)

        # Step the agent continuously
        for _ in range(AGENT_LOOP_ITERATIONS):  # Limit for testing, should be infinite in production
            resp = await camel_agent.astep(get_user_message())
            if (not resp.msgs):
                continue
            msgzero = resp.msgs[0]
            msgzerojson = msgzero.to_dict()
            print(f"Orchestrator: {msgzerojson}")
            sleep(AGENT_SLEEP_TIME)

async def create_orchestrator_agent(connected_mcp_toolkit):
    """Create orchestrator agent with MCP tools from Coral Server."""

    # Get all tools from Coral Server (includes both MCP tools and custom tools)
    tools = connected_mcp_toolkit.get_tools()

    sys_msg = (
        f"""
            You are the orchestrator agent - coordinate user requests and manage PR analysis workflow.

            WORKFLOW:
            1. Extract request_id from "User Request (ID: ...)" format
            2. Send progress updates via send_action_update (agent_id="orchestrator-agent")
            3. Always call summarizer-agent first for PR analysis
            4. Call voice-agent ONLY if user mentions "voice"/"audio"/"sound" - pass summary text
            5. Call risk-agent ONLY if user mentions "risk"/"security"/"vulnerability"
            6. Send final results via webhook_callback with exact agent content (not summaries)

            TOOLS:
            - send_action_update: Progress updates to frontend
            - webhook_callback: Final results (request_id, summary, risk_report, voice_url)
            - coral_create_thread: Start agent communication
            - coral_send_message: Send to specific agents
            - coral_wait_for_mentions: Receive agent responses

            CRITICAL RULES:
            - Forward exact agent responses, not acknowledgments
            - Extract voice URLs from "File saved at: /audio/..." responses
            - Never call agents unless user explicitly requests their functionality

            {os.getenv("CORAL_PROMPT_SYSTEM", default="")}
            {get_orchestrator_tools_description()}
            """
    )

    camel_agent = ChatAgent(
        system_message=sys_msg,
        model=ORCHESTRATOR_MODEL,
        tools=tools,
        message_window_size=MESSAGE_WINDOW_SIZE,
        token_limit=TOKEN_LIMIT
    )
    return camel_agent

if __name__ == "__main__":
    asyncio.run(main())