"""
CBT Schema Definitions

This module contains the schema definitions for the CBT bot state and related types.
"""

from typing import Dict, List, Literal, TypedDict, Any, Optional
from langchain_core.messages import BaseMessage
from typing_extensions import Annotated, Protocol


# Helper function for message history handling
def add_messages(
    messages_old: List[BaseMessage], messages_new: List[BaseMessage]
) -> List[BaseMessage]:
    """Handle merging of message lists for the state."""
    return messages_old + messages_new


class CognitiveDistortion(TypedDict):
    """Represents an identified cognitive distortion."""

    type: str  # The type of cognitive distortion
    examples: List[str]  # Quotes from the conversation demonstrating this distortion
    explanation: str  # Explanation of why this qualifies as this distortion
    severity: int  # 1-5 rating of severity


class CBTTechnique(TypedDict):
    """Represents a CBT technique to address cognitive distortions."""

    name: str  # Name of the technique
    description: str  # Description of the technique
    steps: List[str]  # Steps to implement the technique
    target_distortions: List[str]  # Distortions this technique addresses


class SessionSummary(TypedDict):
    """Summary of a therapy session."""

    main_issues: List[str]  # Main issues discussed
    insights: List[str]  # Insights gained
    techniques_practiced: List[str]  # Techniques practiced
    homework: Optional[str]  # Homework assigned, if any
    progress_notes: str  # Notes on progress


class CBTBotState(TypedDict):
    """State for the CBT bot."""

    messages: Annotated[List[BaseMessage], add_messages]  # Conversation history
    phase: Literal["listening", "cbt_intervention"]  # Current phase of the conversation
    cognitive_analysis: Dict[str, Any]  # Analysis of cognitive patterns
    identified_distortions: List[
        CognitiveDistortion
    ]  # Identified cognitive distortions
    recommended_techniques: List[CBTTechnique]  # Recommended CBT techniques
    session_summary: SessionSummary  # Summary of the current session
    last_user_input: bool  # Flag to track if the last message was from the user
