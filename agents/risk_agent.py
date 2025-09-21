"""Risk Agent - PR Security and Quality Risk Assessment

This agent follows the specialized agent pattern from coral-server examples.
It waits for mentions from orchestrator and provides comprehensive risk assessments.
"""

import asyncio
import os
import sys
from time import sleep

# Add the parent directory to the Python path to import shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from camel.agents import ChatAgent
from camel.toolkits import MCPToolkit, FunctionTool
from camel.toolkits.mcp_toolkit import MCPClient
from camel.utils.mcp_client import ServerConfig
from dotenv import load_dotenv

from shared.github_fetcher import fetch_pr_info
from agent_models import (
    RISK_MODEL,
    MESSAGE_WINDOW_SIZE,
    TOKEN_LIMIT,
    AGENT_LOOP_ITERATIONS,
    AGENT_SLEEP_TIME,
    get_coral_connection_url,
    CORAL_TIMEOUT,
    CORAL_SSE_READ_TIMEOUT
)
from prompts import get_tools_description

load_dotenv()

def fetch_pr_info_tool(pr_url: str) -> str:
    """Tool wrapper for GitHub PR fetching."""
    return fetch_pr_info(pr_url, track_action=None)

async def main():
    """Main risk agent loop - waits for mentions and provides risk assessments."""
    # Get connection URL from Coral Server's official CORAL_CONNECTION_URL env var
    coral_url = get_coral_connection_url("risk-agent")

    if not coral_url:
        # No connection URL available - wait for Coral Server to inject CORAL_CONNECTION_URL
        print("⏳ Waiting for Coral Server to inject CORAL_CONNECTION_URL...")
        while True:
            await asyncio.sleep(5)
            coral_url = get_coral_connection_url("risk-agent")
            if coral_url:
                break

    print(f"🔗 Connecting to Coral server: {coral_url}")
    server = MCPClient(ServerConfig(url=coral_url, timeout=CORAL_TIMEOUT, sse_read_timeout=CORAL_SSE_READ_TIMEOUT, terminate_on_close=True, prefer_sse=True), timeout=CORAL_TIMEOUT)
    mcp_toolkit = MCPToolkit([server])

    async with mcp_toolkit as connected_mcp_toolkit:
        camel_agent = await create_risk_agent(connected_mcp_toolkit)

        # Step the agent continuously
        for _ in range(AGENT_LOOP_ITERATIONS):  # Limit for testing, should be infinite in production
            resp = await camel_agent.astep("[automated] continue collaborating with the orchestrator-agent")
            if (not resp.msgs):
                continue
            msgzero = resp.msgs[0]
            msgzerojson = msgzero.to_dict()
            print(f"Risk Agent: {msgzerojson}")
            sleep(AGENT_SLEEP_TIME)

def remove_strict_from_tools(tools_list):
    """Remove 'strict' parameter from all tools - AIML API doesn't support it."""
    for tool in tools_list:
        if hasattr(tool, 'get_openai_tool_schema'):
            tool_schema = tool.get_openai_tool_schema()
            if 'strict' in tool_schema:
                del tool_schema['strict']
            if 'function' in tool_schema and 'strict' in tool_schema['function']:
                del tool_schema['function']['strict']
            tool.openai_tool_schema = tool_schema
    return tools_list

async def create_risk_agent(connected_mcp_toolkit):
    """Create risk agent with MCP tools + GitHub fetching capability."""
    # Create GitHub fetching tool
    fetch_tool = FunctionTool(fetch_pr_info_tool)

    # Get all tools and remove 'strict' parameter from ALL of them
    mcp_tools = connected_mcp_toolkit.get_tools()
    risk_assessment_tools = [fetch_tool]
    all_tools = mcp_tools + risk_assessment_tools

    # WORKAROUND: Remove 'strict' parameter that AIML doesn't support from ALL tools
    tools = remove_strict_from_tools(all_tools)

    sys_msg = (
        f"""
            You are the risk-agent - analyze GitHub PRs for security and quality risks.

            WORKFLOW:
            1. Use coral_wait_for_mentions to wait for orchestrator requests
            2. Extract PR URL from orchestrator message
            3. Use send_action_update to update your progress (agent_id="risk-agent")
            4. Use fetch_pr_info_tool to get PR data
            5. Create comprehensive risk assessment following the structure below
            6. Use coral_send_message to send results back to orchestrator

            RISK ASSESSMENT STRUCTURE:
            - Overall Risk Assessment: Risk level summary with confidence
            - Key Risks: Security vulnerabilities, breaking changes, quality issues
            - Hotspots: Files/areas requiring special attention
            - Suggested Mitigations: Recommended actions to reduce risks

            FOCUS AREAS:
            Security vulnerabilities, breaking changes, dependencies, test coverage, deployment risks

            PROGRESS UPDATES:
            - "Starting Risk Assessment" → "Analyzing Security Risks" → "Risk Assessment Complete"

            CRITICAL RULES:
            - Do not contact anyone other than the orchestrator-agent
            - Provide progress updates only if you are busy with a task, not waiting for mentions

            {os.getenv("CORAL_PROMPT_SYSTEM", default="")}
            {get_tools_description()}
            """
    )

    camel_agent = ChatAgent(
        system_message=sys_msg,
        model=RISK_MODEL,
        tools=tools,
        message_window_size=MESSAGE_WINDOW_SIZE,
        token_limit=TOKEN_LIMIT
    )
    return camel_agent

if __name__ == "__main__":
    asyncio.run(main())