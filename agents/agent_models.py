"""Model configurations for each agent in the PR Summarizer multi-agent system.

This file contains non-sensitive configuration settings for all agents.
Sensitive information like API keys should be stored in .env file.
"""

import os
from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

load_dotenv()

# =================================================================
# ORCHESTRATOR AGENT MODEL (User Interaction)
# =================================================================

# ORCHESTRATOR_MODEL = ModelFactory.create(
#     model_platform=ModelPlatformType.NEBIUS,
#     model_type="Qwen/Qwen3-30B-A3B-Instruct-2507",
#     api_key=os.getenv("ORCHESTRATOR_API_KEY"),
#     model_config_dict={
#         "temperature": 0.1,
#         "max_tokens": 2000,
#     },
# )

# ORCHESTRATOR_MODEL = ModelFactory.create(
#     model_platform=ModelPlatformType.AIML,
#     model_type="openai/gpt-5-2025-08-07",
#     api_key=os.getenv("ORCHESTRATOR_API_KEY"),
#     model_config_dict={
#         "temperature": 0.1,
#         "max_tokens": 2000,
#     },
# )

ORCHESTRATOR_MODEL = ModelFactory.create(
    model_platform=ModelPlatformType.AIML,
    model_type="gpt-4o",
    api_key=os.getenv("ORCHESTRATOR_API_KEY"),
    model_config_dict={
        "temperature": 0.1,
        "max_tokens": 2000,
    },
)

# =================================================================
# SPECIALIZED AGENT MODELS (Domain-specific tasks)
# =================================================================

# SUMMARIZER_MODEL = ModelFactory.create(
#     model_platform=ModelPlatformType.AIML,
#     model_type="openai/gpt-5-2025-08-07",
#     api_key=os.getenv("SUMMARIZER_API_KEY"),
#     model_config_dict={
#         "temperature": 0.1,
#         "max_tokens": 3000,
#     },
# )

SUMMARIZER_MODEL = ModelFactory.create(
    model_platform=ModelPlatformType.AIML,
    model_type="gpt-4o",
    api_key=os.getenv("SUMMARIZER_API_KEY"),
    model_config_dict={
        "temperature": 0.1,
        "max_tokens": 3000,
    },
)

# SUMMARIZER_MODEL = ModelFactory.create(
#     model_platform=ModelPlatformType.NEBIUS,
#     model_type="Qwen/Qwen3-30B-A3B-Instruct-2507",
#     api_key=os.getenv("SUMMARIZER_API_KEY"),
#     model_config_dict={
#         "temperature": 0.1,
#         "max_tokens": 3000,
#     },
# )

# RISK_MODEL = ModelFactory.create(
#     model_platform=ModelPlatformType.AIML,
#     model_type="openai/gpt-5-2025-08-07",
#     api_key=os.getenv("RISK_API_KEY"),
#     model_config_dict={
#         "temperature": 0.1,
#         "max_tokens": 3000,
#     },
# )

RISK_MODEL = ModelFactory.create(
    model_platform=ModelPlatformType.AIML,
    model_type="gpt-4o",
    api_key=os.getenv("RISK_API_KEY"),
    model_config_dict={
        "temperature": 0.1,
        "max_tokens": 3000,
    },
)

# RISK_MODEL = ModelFactory.create(
#     model_platform=ModelPlatformType.NEBIUS,
#     model_type="Qwen/Qwen3-30B-A3B-Instruct-2507",
#     api_key=os.getenv("RISK_API_KEY"),
#     model_config_dict={
#         "temperature": 0.1,
#         "max_tokens": 3000,
#     },
# )

# VOICE_MODEL = ModelFactory.create(
#     model_platform=ModelPlatformType.AIML,
#     model_type="openai/gpt-5-2025-08-07",
#     api_key=os.getenv("VOICE_API_KEY", os.getenv("SUMMARIZER_API_KEY")),  # Fallback to summarizer key
#     model_config_dict={
#         "temperature": 0.1,
#         "max_tokens": 2000,
#     },
# )

VOICE_MODEL = ModelFactory.create(
    model_platform=ModelPlatformType.AIML,
    model_type="gpt-4o",
    api_key=os.getenv("VOICE_API_KEY", os.getenv("SUMMARIZER_API_KEY")),  # Fallback to summarizer key
    model_config_dict={
        "temperature": 0.1,
        "max_tokens": 2000,
    },
)

# VOICE_MODEL = ModelFactory.create(
#     model_platform=ModelPlatformType.NEBIUS,
#     model_type="Qwen/Qwen3-30B-A3B-Instruct-2507",
#     api_key=os.getenv("VOICE_API_KEY", os.getenv("SUMMARIZER_API_KEY")),  # Fallback to summarizer key
#     model_config_dict={
#         "temperature": 0.1,
#         "max_tokens": 2000,
#     },
# )

# =================================================================
# AGENT COMMUNICATION SETTINGS
# =================================================================

# Message window size for all agents
MESSAGE_WINDOW_SIZE = 204800

# Token limit for all agents
TOKEN_LIMIT = 20000

# Number of iterations for agent loops (change to while True for production)
AGENT_LOOP_ITERATIONS = 200

# Sleep time between agent iterations (seconds)
AGENT_SLEEP_TIME = 10

# =================================================================
# CORAL SERVER SETTINGS
# =================================================================

# Coral Server connection settings
CORAL_BASE_URL = "http://localhost:5555"
CORAL_APP_ID = "pr-summarizer-app"
CORAL_PRIVACY_KEY = "pr-analysis-key"
CORAL_TIMEOUT = 3000000.0
CORAL_SSE_READ_TIMEOUT = 3000000.0

# Function to get Coral connection URL (Coral Server's official approach)
def get_coral_connection_url(agent_id: str) -> str:
    """
    Get Coral connection URL from Coral Server's official CORAL_CONNECTION_URL environment variable.
    Coral Server automatically injects this when a session is created.
    """
    connection_url = os.getenv("CORAL_CONNECTION_URL")
    if connection_url:
        # Append agent ID to the Coral-provided URL
        separator = "&" if "?" in connection_url else "?"
        return f"{connection_url}{separator}agentId={agent_id}"
    else:
        # Return None to indicate no session available yet
        return None

# =================================================================
# SHARED CONFIGURATION FOR COMPATIBILITY
# =================================================================

# For compatibility with coral-server examples config pattern
PLATFORM_TYPE = "NEBIUS"  # For orchestrator
MODEL_TYPE = "NEBIUS_GPT_OSS_120B"  # For orchestrator
MODEL_CONFIG = {
    "temperature": 0.1,
    "max_tokens": 2000,
}

__all__ = [
    "ORCHESTRATOR_MODEL",
    "SUMMARIZER_MODEL",
    "RISK_MODEL",
    "VOICE_MODEL",
    "MESSAGE_WINDOW_SIZE",
    "TOKEN_LIMIT",
    "AGENT_LOOP_ITERATIONS",
    "AGENT_SLEEP_TIME",
    "CORAL_BASE_URL",
    "CORAL_APP_ID",
    "CORAL_PRIVACY_KEY",
    "get_coral_connection_url",
    "CORAL_TIMEOUT",
    "CORAL_SSE_READ_TIMEOUT",
    "PLATFORM_TYPE",
    "MODEL_TYPE",
    "MODEL_CONFIG"
]