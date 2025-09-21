"""Voice Agent - Text-to-Speech Generation

This agent follows the specialized agent pattern from coral-server examples.
It waits for mentions from orchestrator and generates voice-overs for text content.
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

from shared.voice_over import generate_voice_over
from agent_models import (
    VOICE_MODEL,
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

def generate_voice_tool(text: str, voice_id: str = None) -> str:
    """Tool wrapper for voice generation."""
    try:
        result = generate_voice_over(text, voice_id)
        voice_path = result.get("voice_path", "")

        # Convert full file path to relative URL for web access
        # voice_path is like "/path/to/voice_over_outputs/voice_123_456.mp3"
        # We need to return "/audio/voice_123_456.mp3"
        import os
        filename = os.path.basename(voice_path)
        voice_url = f"/audio/{filename}"

        return f"Voice-over generated successfully. File saved at: {voice_url}"
    except Exception as e:
        return f"Voice generation failed: {str(e)}"

async def main():
    """Main voice agent loop - waits for mentions and generates voice-overs."""
    # Get connection URL from Coral Server's official CORAL_CONNECTION_URL env var
    coral_url = get_coral_connection_url("voice-agent")

    if not coral_url:
        # No connection URL available - wait for Coral Server to inject CORAL_CONNECTION_URL
        print("⏳ Waiting for Coral Server to inject CORAL_CONNECTION_URL...")
        while True:
            await asyncio.sleep(5)
            coral_url = get_coral_connection_url("voice-agent")
            if coral_url:
                break

    print(f"🔗 Connecting to Coral server: {coral_url}")
    server = MCPClient(ServerConfig(url=coral_url, timeout=CORAL_TIMEOUT, sse_read_timeout=CORAL_SSE_READ_TIMEOUT, terminate_on_close=True, prefer_sse=True), timeout=CORAL_TIMEOUT)
    mcp_toolkit = MCPToolkit([server])

    async with mcp_toolkit as connected_mcp_toolkit:
        camel_agent = await create_voice_agent(connected_mcp_toolkit)

        # Step the agent continuously
        for _ in range(AGENT_LOOP_ITERATIONS):  # Limit for testing, should be infinite in production
            resp = await camel_agent.astep("[automated] continue collaborating with other agents. make sure to mention agents you intend to communicate with")
            if (not resp.msgs):
                continue
            msgzero = resp.msgs[0]
            msgzerojson = msgzero.to_dict()
            print(f"Voice Agent: {msgzerojson}")
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

async def create_voice_agent(connected_mcp_toolkit):
    """Create voice agent with MCP tools + voice generation capability."""
    # Create voice generation tool
    voice_tool = FunctionTool(generate_voice_tool)

    # Get all tools and remove 'strict' parameter from ALL of them
    mcp_tools = connected_mcp_toolkit.get_tools()
    voice_generation_tools = [voice_tool]
    all_tools = mcp_tools + voice_generation_tools

    # WORKAROUND: Remove 'strict' parameter that AIML doesn't support from ALL tools
    tools = remove_strict_from_tools(all_tools)

    sys_msg = (
        f"""
            You are the voice-agent - generate high-quality voice-overs from text using ElevenLabs API.

            WORKFLOW:
            1. coral_wait_for_mentions - wait for orchestrator requests
            2. Extract text content from orchestrator message
            3. send_action_update progress reports (agent_id="voice-agent")
            4. generate_voice_tool to create MP3 audio files
            5. coral_send_message audio URL back to orchestrator

            PROGRESS UPDATES:
            - "Starting Voice Generation" → "Generating Audio" → "Voice Generation Complete"

            {os.getenv("CORAL_PROMPT_SYSTEM", default="")}
            {get_tools_description()}
            """
    )

    camel_agent = ChatAgent(
        system_message=sys_msg,
        model=VOICE_MODEL,
        tools=tools,
        message_window_size=MESSAGE_WINDOW_SIZE,
        token_limit=TOKEN_LIMIT
    )
    return camel_agent

if __name__ == "__main__":
    asyncio.run(main())