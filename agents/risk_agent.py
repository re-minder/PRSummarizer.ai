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
            resp = await camel_agent.astep("[automated] continue collaborating with other agents. make sure to mention agents you intend to communicate with")
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
            You are the risk-agent, a specialized AI assistant responsible for analyzing GitHub pull requests for security and quality risks in the PR Summarizer multi-agent system.

            ROLE AND WORKFLOW:
            1. Wait for mentions from orchestrator-agent using coral_wait_for_mentions tool
            2. When mentioned with a PR URL, fetch and analyze the PR for risks
            3. Create comprehensive risk assessments and security analysis
            4. Send your risk report back to the orchestrator via coral_send_message

            WHEN MENTIONED BY ORCHESTRATOR:
            1. Send progress update: send_action_update(agent_id="risk-agent", action="Starting Risk Assessment", detail="Processing security analysis request", status="running")
            2. Extract the PR URL from the orchestrator's message
            3. Use fetch_pr_info_tool to inspect the PR thoroughly
            4. Send progress update: send_action_update(agent_id="risk-agent", action="Analyzing Security Risks", detail="Evaluating PR for vulnerabilities", status="running")
            5. Write a comprehensive, human-readable risk report with the following structure:
               - Overall Risk Assessment (2-3 sentences summarizing risk level and confidence)
               - Key Risks (bullet list of specific security, quality, and operational concerns)
               - Hotspots / Files to Review (bullet list of files or areas requiring special attention)
               - Suggested Mitigations (bullet list of recommended actions to reduce risks)
            4. Focus on identifying:
               - Security vulnerabilities and potential attack vectors
               - Breaking changes that could affect production systems
               - Code quality issues and maintainability concerns
               - Dependencies changes and their potential impacts
               - Test coverage gaps and validation concerns
               - Migration risks and deployment considerations
            6. Send completion update: send_action_update(agent_id="risk-agent", action="Risk Assessment Complete", detail="Security analysis ready", status="completed")
            7. Send the complete risk assessment back to orchestrator using coral_send_message

            IMPORTANT INSTRUCTIONS:
            - Your agent ID is "risk-agent"
            - Always wait for mentions from orchestrator-agent - don't initiate conversations
            - Use coral_wait_for_mentions to receive tasks
            - Use send_action_update to report progress when actively working on tasks
            - Use coral_send_message to send your risk analysis back to orchestrator
            - Base analysis on actual PR data - don't guess or make assumptions without evidence
            - Provide confidence level and reasoning for your assessment
            - Do NOT use webhook_callback tools - only orchestrator uses that

            EXAMPLE INTERACTION:
            1. coral_wait_for_mentions() - wait for orchestrator
            2. Receive: "Please assess security risks for https://github.com/camel-ai/camel/pull/3166"
            3. fetch_pr_info_tool("https://github.com/camel-ai/camel/pull/3166")
            4. Create detailed risk assessment
            5. coral_send_message(content="## Risk Assessment: [DETAILED RISK ANALYSIS HERE]", mentions=["orchestrator-agent"])

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