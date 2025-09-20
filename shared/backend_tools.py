"""
Backend Communication Tools for Agents
Provides tools for agents to send messages to the backend server
"""

import time
import requests
from camel.toolkits import FunctionTool

# Backend server configuration
BACKEND_URL = "http://localhost:8000"

def send_action_update(
    agent_id: str,
    action: str,
    detail: str,
    status: str = "running"
) -> str:
    """
    Send an action update to the backend server.

    Args:
        agent_id: ID of the agent sending the update
        action: Brief description of the action
        detail: Detailed description
        status: Status of the action ("running", "completed", "failed")

    Returns:
        Status message
    """
    try:
        payload = {
            "agent_id": agent_id,
            "event_type": "action",
            "data": {
                "timestamp": int(time.time() * 1000),
                "action": action,
                "detail": detail,
                "status": status,
                "source": agent_id
            }
        }

        response = requests.post(
            f"{BACKEND_URL}/agent/message",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            return f"Action update sent successfully: {action}"
        else:
            return f"Failed to send action update: {response.status_code}"

    except Exception as e:
        return f"Error sending action update: {str(e)}"

def send_completion(
    agent_id: str,
    summary: str,
    risk_report: str = "",
    voice_url: str = "",
    output: str = ""
) -> str:
    """
    Send completion results to the backend server.

    Args:
        agent_id: ID of the agent sending the completion
        summary: Analysis summary
        risk_report: Risk assessment report
        voice_url: URL to generated voice file
        output: Final combined output

    Returns:
        Status message
    """
    try:
        payload = {
            "agent_id": agent_id,
            "event_type": "complete",
            "data": {
                "summary": summary,
                "risk_report": risk_report,
                "output": output or summary,
                "voice_url": voice_url
            }
        }

        response = requests.post(
            f"{BACKEND_URL}/agent/message",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            return "Completion results sent successfully"
        else:
            return f"Failed to send completion: {response.status_code}"

    except Exception as e:
        return f"Error sending completion: {str(e)}"

def send_error(
    agent_id: str,
    error_message: str
) -> str:
    """
    Send an error message to the backend server.

    Args:
        agent_id: ID of the agent sending the error
        error_message: Error description

    Returns:
        Status message
    """
    try:
        payload = {
            "agent_id": agent_id,
            "event_type": "error",
            "data": {
                "error": error_message
            }
        }

        response = requests.post(
            f"{BACKEND_URL}/agent/message",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            return "Error message sent successfully"
        else:
            return f"Failed to send error: {response.status_code}"

    except Exception as e:
        return f"Error sending error message: {str(e)}"

def webhook_callback(
    request_id: str,
    summary: str,
    risk_report: str = "",
    voice_url: str = ""
) -> str:
    """
    Send final results via webhook callback (compatible with existing orchestrator).

    Args:
        request_id: Request ID to respond to
        summary: PR analysis summary
        risk_report: Security risk assessment
        voice_url: URL to generated voice file

    Returns:
        Status message
    """
    try:
        payload = {
            "request_id": request_id,
            "summary": summary,
            "risk_report": risk_report,
            "voice_url": voice_url,
            "output": summary
        }

        response = requests.post(
            f"{BACKEND_URL}/callback",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            return "Webhook callback sent successfully"
        else:
            return f"Failed to send webhook callback: {response.status_code}"

    except Exception as e:
        return f"Error sending webhook callback: {str(e)}"

# CAMEL Function Tools
def get_backend_tools():
    """Get all backend communication tools as CAMEL FunctionTool objects"""

    send_action_tool = FunctionTool(
        send_action_update,
        "Send action update to webapp via backend server"
    )

    send_completion_tool = FunctionTool(
        send_completion,
        "Send completion results to webapp via backend server"
    )

    send_error_tool = FunctionTool(
        send_error,
        "Send error message to webapp via backend server"
    )

    webhook_callback_tool = FunctionTool(
        webhook_callback,
        "Send final results via webhook callback to webapp"
    )

    return [
        send_action_tool,
        send_completion_tool,
        send_error_tool,
        webhook_callback_tool
    ]

# Action tracking utility (compatible with existing shared modules)
def track_action(action: str, detail: str, status: str, agent_id: str = "unknown"):
    """Track action progress and send to backend (drop-in replacement for existing track_action)"""
    send_action_update(agent_id, action, detail, status)