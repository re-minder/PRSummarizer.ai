"""ElevenLabs voice-over integration."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv()


action_tracker: list[Dict[str, Any]] = []


def track_action(action: str, detail: str, status: str) -> None:
    action_tracker.append(
        {
            "timestamp": time.time(),
            "action": action,
            "detail": detail,
            "status": status,
        }
    )


def generate_voice_over(text: str, voice_id: Optional[str] = None) -> Dict[str, str]:
    """Generate voice-over audio through the ElevenLabs Text-to-Speech API."""

    track_action("voice_generate", "Preparing voice-over synthesis", "running")

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        track_action("voice_generate", "Missing ELEVENLABS_API_KEY", "failed")
        raise RuntimeError("ELEVENLABS_API_KEY not configured.")

    voice = voice_id or os.getenv("ELEVENLABS_VOICE_ID")
    if not voice:
        track_action("voice_generate", "Missing voice_id", "failed")
        raise RuntimeError(
            "Voice ID not provided. Set ELEVENLABS_VOICE_ID or pass voice_id explicitly."
        )

    # Import configuration constants
    try:
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))
        from agent_models import DEFAULT_ELEVENLABS_BASE_URL, DEFAULT_ELEVENLABS_MODEL, DEFAULT_VOICE_STABILITY, DEFAULT_VOICE_SIMILARITY, DEFAULT_VOICE_OUTPUT_DIR
        base_url = os.getenv("ELEVENLABS_BASE_URL", DEFAULT_ELEVENLABS_BASE_URL)
    except ImportError:
        base_url = os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io/v1")
    endpoint = f"{base_url}/text-to-speech/{voice}"

    payload: Dict[str, Any] = {
        "text": text,
        "model_id": os.getenv("ELEVENLABS_MODEL_ID", globals().get('DEFAULT_ELEVENLABS_MODEL', 'eleven_turbo_v2_5')),
    }

    stability = os.getenv("ELEVENLABS_STABILITY")
    similarity = os.getenv("ELEVENLABS_SIMILARITY")
    if stability or similarity:
        payload["voice_settings"] = {
            "stability": float(stability) if stability else globals().get('DEFAULT_VOICE_STABILITY', 0.5),
            "similarity_boost": float(similarity) if similarity else globals().get('DEFAULT_VOICE_SIMILARITY', 0.5),
        }

    try:
        response = requests.post(
            endpoint,
            headers={
                "xi-api-key": api_key,
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        track_action("voice_generate", f"HTTP error: {exc}", "failed")
        raise RuntimeError(f"Voice-over request failed: {exc}")

    if response.status_code >= 400:
        track_action(
            "voice_generate",
            f"API error {response.status_code}: {response.text[:200]}",
            "failed",
        )
        raise RuntimeError(
            f"ElevenLabs API error {response.status_code}: {response.text[:200]}"
        )

    output_dir = Path(os.getenv("VOICE_OVER_DIR", globals().get('DEFAULT_VOICE_OUTPUT_DIR', 'voice_over_outputs')))
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time())
    output_path = output_dir / f"voice_{voice}_{timestamp}.mp3"
    output_path.write_bytes(response.content)

    track_action(
        "voice_generate",
        f"Voice-over stored at {output_path}",
        "completed",
    )

    return {"voice_path": str(output_path)}


def reset_actions() -> None:
    action_tracker.clear()


__all__ = ["generate_voice_over", "reset_actions", "action_tracker", "track_action"]