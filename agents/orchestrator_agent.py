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
            msgzero = resp.msgs[0]
            msgzerojson = msgzero.to_dict()
            print(f"Orchestrator: {msgzerojson}")
            sleep(AGENT_SLEEP_TIME)

async def create_orchestrator_agent(connected_mcp_toolkit):
    """Create orchestrator agent with MCP communication tools only."""
    # Orchestrator only gets MCP tools for communication - no domain-specific tools
    tools = connected_mcp_toolkit.get_tools()

    sys_msg = (
        f"""
            You are a helpful assistant responsible for interacting with the user and coordinating PR analysis workflows with other agents. You can interact with other agents using the chat tools.
            User interaction and PR analysis coordination is your speciality. You identify as "orchestrator-agent".

            As a user interaction agent, only you can interact with the user.

            Make sure that all PR analysis comes from reliable specialized agents and that all information is accurate. Make sure your responses are much more reliable than guesses! You should make sure no agents are guessing too, by directing the relevant specialized agents to do each part of a PR analysis task. Do a refresh of the available agents before asking the user for input.

            Make sure to put the name of the agent(s) you are talking to in the mentions field of the send message tool.

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