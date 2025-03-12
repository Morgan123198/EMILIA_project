"""
State Utilities

This module provides utility functions for managing CBT bot state.
"""

from typing import Dict, List, Any
from src.schema.cbt_state import CBTBotState


def get_default_state() -> CBTBotState:
    """
    Create a default initial state for the CBT bot.

    Returns:
        CBTBotState: A default state with empty collections and initialized values.
    """
    return {
        "messages": [],
        "phase": "listening",
        "cognitive_analysis": {},
        "identified_distortions": [],
        "recommended_techniques": [],
        "session_summary": {
            "main_issues": [],
            "insights": [],
            "techniques_practiced": [],
            "homework": None,
            "progress_notes": "",
        },
        "last_user_input": True,
    }


def merge_states(base_state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge state updates into a base state, handling special cases like message lists.

    Args:
        base_state: The existing state to update
        updates: New state values to merge in

    Returns:
        Dict[str, Any]: The merged state
    """
    # Create a copy of the base state to avoid modifying the original
    result = dict(base_state)

    # Handle each update field appropriately
    for key, value in updates.items():
        # Skip None values
        if value is None:
            continue

        # Special handling for lists - append instead of replace
        if key in result and isinstance(result[key], list) and isinstance(value, list):
            # For messages, this will use the add_messages function due to Annotated type
            result[key] = result[key] + value
        # Special handling for dicts - deep merge
        elif (
            key in result and isinstance(result[key], dict) and isinstance(value, dict)
        ):
            result[key] = {**result[key], **value}
        # Default case - replace the value
        else:
            result[key] = value

    return result


def extract_conversation_history(state: Dict[str, Any]) -> List[str]:
    """
    Extract plain text conversation history from a state object.

    Args:
        state: The current state with messages

    Returns:
        List[str]: List of message contents as strings
    """
    if "messages" not in state:
        return []

    return [
        m.content
        for m in state["messages"]
        if hasattr(m, "content") and isinstance(m.content, str)
    ]
