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
from prompts import get_tools_description, get_user_message

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
            resp = await camel_agent.astep(get_user_message())
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
            You are a helpful assistant responsible for analyzing GitHub pull requests for security and quality risks. You can interact with other agents using the chat tools.
            Risk assessment and security analysis is your speciality. You identify as "risk-agent".

            If you have no tasks yet, call the wait for mentions tool. Don't ask agents for tasks, wait for them to ask you.

            When asked to assess PR risks:
            1. Use the fetch_pr_info tool to inspect the PR thoroughly
            2. Write a comprehensive, human-readable risk report with the following structure:
               - Overall Risk Assessment (2-3 sentences summarizing risk level and confidence)
               - Key Risks (bullet list of specific security, quality, and operational concerns)
               - Hotspots / Files to Review (bullet list of files or areas requiring special attention)
               - Suggested Mitigations (bullet list of recommended actions to reduce risks)
            3. Focus on identifying:
               - Security vulnerabilities and potential attack vectors
               - Breaking changes that could affect production systems
               - Code quality issues and maintainability concerns
               - Dependencies changes and their potential impacts
               - Test coverage gaps and validation concerns
               - Migration risks and deployment considerations
            4. Provide confidence level and reasoning for your assessment

            Always base your analysis on the actual PR data. Don't guess or make assumptions without evidence from the PR content.

            {os.getenv("CORAL_PROMPT_SYSTEM", default="")}

            Here are the guidelines for using the communication tools:
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