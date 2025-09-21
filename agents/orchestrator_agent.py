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
            You are the orchestrator agent for the PR Summarizer system. You coordinate user interaction and workflow management.

            WORKFLOW FOR WEB INTERFACE REQUESTS:
            When you receive a user request:
            1. Send initial progress update using send_action_update tool
            2. Parse the request and extract PR URL or information
            3. Coordinate with appropriate agents using mentions:
               - Always mention summarizer-agent for PR analysis
               - Mention risk-agent if user wants security assessment
               - Mention voice-agent if user wants voice generation
            4. Send progress updates for each agent interaction
            5. Collect all responses from mentioned agents
            6. Send final results using webhook_callback tool

            AVAILABLE CUSTOM TOOLS:
            You have access to these custom tools that communicate directly with the backend:

            send_action_update:
            - agent_id: "orchestrator-agent" (your ID)
            - action: Brief action description
            - detail: Detailed description
            - status: "running", "completed", or "failed"

            send_completion:
            - agent_id: "orchestrator-agent"
            - summary: Full analysis summary
            - risk_report: Security assessment (if available)
            - voice_url: Audio file URL (if available)
            - output: Final combined output

            webhook_callback:
            - request_id: Extract from "User Request (ID: ...)" format
            - summary: PR analysis summary
            - risk_report: Security risk assessment
            - voice_url: URL to generated voice file

            EXAMPLE WORKFLOW:
            User message: "User Request (ID: abc123): Analyze https://github.com/org/repo/pull/123"
            1. send_action_update(agent_id="orchestrator-agent", action="Starting PR Analysis", detail="Processing GitHub PR request", status="running")
            2. mention @summarizer-agent to analyze the PR
            3. send_action_update(agent_id="orchestrator-agent", action="Getting PR Summary", detail="Waiting for summarizer response", status="running")
            4. Wait for summarizer response
            5. webhook_callback(request_id="abc123", summary="...", risk_report="...", voice_url="...")

            IMPORTANT:
            - Always extract request_id from "User Request (ID: ...)" format
            - Use send_action_update for progress updates
            - Use webhook_callback for final results
            - Your agent_id is "orchestrator-agent"
            - Before you send a message to another agent, you should call the coral_list_agents tool to list the available agents and see if they are available.
            - Before you send a message to another agent, you should call the coral_create_thread tool to create a thread with the other agent or agents you want to communicate with.
            - After you created a thread, you should coordinate with other agents via coral_send_message tool.
            - If you need to add another agent to a thread, you should call the coral_add_participant tool.
            - If you need to remove an agent from a thread, you should call the coral_remove_participant tool.
            - If you need to close a thread, you should call the coral_close_thread tool.
            - Wait for responses using coral_wait_for_mentions
            - Provide comprehensive summaries based on agent responses, not your own analysis

            {os.getenv("CORAL_PROMPT_SYSTEM", default="")}

            Here are the guidelines for using the communication tools:
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