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
from prompts import get_tools_description, get_user_message

load_dotenv()

def generate_voice_tool(text: str, voice_id: str = None) -> str:
    """Tool wrapper for voice generation."""
    try:
        result = generate_voice_over(text, voice_id)
        voice_path = result.get("voice_path", "")
        return f"Voice-over generated successfully. File saved at: {voice_path}"
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
            resp = await camel_agent.astep(get_user_message())
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
            You are a helpful assistant specialized in generating high-quality voice-overs from text content. You can interact with other agents using the chat tools.
            Voice synthesis and audio generation is your speciality. You identify as "voice-agent".

            If you have no tasks yet, call the wait for mentions tool. Don't ask agents for tasks, wait for them to ask you.

            When asked to generate voice-overs:
            1. Use the generate_voice_tool to convert text to speech
            2. Process the provided text content (summaries, reports, etc.)
            3. Generate high-quality MP3 audio files using ElevenLabs API
            4. Return the file path of the generated voice-over
            5. Handle any errors gracefully and report issues clearly

            Requirements and capabilities:
            - Uses ElevenLabs Text-to-Speech API for professional quality audio
            - Supports custom voice IDs for different voice characteristics
            - Generated files are saved in the configured output directory
            - Handles both short and long text content appropriately
            - Provides clear feedback on success or failure

            Configuration requirements:
            - ELEVENLABS_API_KEY must be configured in environment
            - ELEVENLABS_VOICE_ID should be set for consistent voice selection
            - Generated files are saved in voice_over_outputs directory by default

            Always provide clear status updates and file paths when generation is successful.

            {os.getenv("CORAL_PROMPT_SYSTEM", default="")}

            Here are the guidelines for using the communication tools:
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