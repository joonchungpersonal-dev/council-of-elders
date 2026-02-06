"""Conversation history management."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from council.config import get_history_dir, get_config_value


def save_session(
    elder_ids: list[str],
    conversation: list[dict],
    topic: str | None = None,
) -> str:
    """
    Save a conversation session.

    Args:
        elder_ids: List of elders involved
        conversation: List of conversation turns
        topic: Optional topic/title for the session

    Returns:
        Session ID
    """
    if not get_config_value("history_enabled", True):
        return ""

    history_dir = get_history_dir()
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    session_data = {
        "id": session_id,
        "timestamp": datetime.now().isoformat(),
        "elders": elder_ids,
        "topic": topic or _extract_topic(conversation),
        "conversation": conversation,
    }

    session_file = history_dir / f"{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)

    # Cleanup old sessions if needed
    _cleanup_old_sessions()

    return session_id


def load_session(session_id: str) -> dict | None:
    """Load a conversation session by ID."""
    history_dir = get_history_dir()
    session_file = history_dir / f"{session_id}.json"

    if not session_file.exists():
        return None

    with open(session_file) as f:
        return json.load(f)


def list_sessions(limit: int = 20) -> list[dict]:
    """
    List recent conversation sessions.

    Args:
        limit: Maximum number of sessions to return

    Returns:
        List of session summaries (id, timestamp, topic, elders)
    """
    history_dir = get_history_dir()
    sessions = []

    for session_file in sorted(history_dir.glob("*.json"), reverse=True)[:limit]:
        try:
            with open(session_file) as f:
                data = json.load(f)
                sessions.append({
                    "id": data.get("id", session_file.stem),
                    "timestamp": data.get("timestamp"),
                    "topic": data.get("topic", "Untitled"),
                    "elders": data.get("elders", []),
                })
        except Exception:
            continue

    return sessions


def delete_session(session_id: str) -> bool:
    """Delete a conversation session."""
    history_dir = get_history_dir()
    session_file = history_dir / f"{session_id}.json"

    if session_file.exists():
        session_file.unlink()
        return True
    return False


def clear_history() -> int:
    """
    Clear all conversation history.

    Returns:
        Number of sessions deleted
    """
    history_dir = get_history_dir()
    count = 0

    for session_file in history_dir.glob("*.json"):
        session_file.unlink()
        count += 1

    return count


def _extract_topic(conversation: list[dict]) -> str:
    """Extract a topic from the first user message."""
    for turn in conversation:
        if turn.get("role") == "user":
            content = turn.get("content", "")
            # Take first 50 chars, ending at word boundary
            if len(content) <= 50:
                return content
            truncated = content[:50]
            last_space = truncated.rfind(" ")
            if last_space > 30:
                truncated = truncated[:last_space]
            return truncated + "..."
    return "Untitled"


def _cleanup_old_sessions() -> None:
    """Remove old sessions beyond the max limit."""
    max_sessions = get_config_value("history_max_sessions", 100)
    history_dir = get_history_dir()

    sessions = sorted(history_dir.glob("*.json"), reverse=True)

    if len(sessions) > max_sessions:
        for old_session in sessions[max_sessions:]:
            old_session.unlink()
