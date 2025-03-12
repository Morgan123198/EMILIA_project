"""
Conversation Parser Utilities

This module contains utilities for parsing and converting conversations
to and from various formats, including JSON.
"""

import json
from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


def parse_json_conversation(json_data: str) -> List[Dict[str, Any]]:
    """
    Parse a JSON string representing a conversation into a list of message dictionaries.

    Expected JSON format:
    [
        {"role": "human", "content": "Hello"},
        {"role": "ai", "content": "Hi there! How can I help you?"},
        ...
    ]

    Args:
        json_data: JSON string representing the conversation

    Returns:
        List[Dict[str, Any]]: List of message dictionaries
    """
    try:
        # Parse the JSON string
        conversation = json.loads(json_data)

        # Validate the structure
        if not isinstance(conversation, list):
            raise ValueError("JSON data must be a list of messages")

        # Validate each message
        for i, message in enumerate(conversation):
            if not isinstance(message, dict):
                raise ValueError(f"Message at index {i} must be a dictionary")
            if "role" not in message:
                raise ValueError(f"Message at index {i} is missing 'role' field")
            if "content" not in message:
                raise ValueError(f"Message at index {i} is missing 'content' field")
            if message["role"] not in ["human", "ai", "system"]:
                raise ValueError(
                    f"Message at index {i} has invalid role: {message['role']}"
                )

        return conversation

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")


def convert_to_langchain_messages(conversation: List[Dict[str, Any]]) -> List[Any]:
    """
    Convert a list of message dictionaries to LangChain message objects.

    Args:
        conversation: List of message dictionaries

    Returns:
        List[Any]: List of LangChain message objects
    """
    messages = []

    for message in conversation:
        role = message["role"]
        content = message["content"]

        if role == "human":
            messages.append(HumanMessage(content=content))
        elif role == "ai":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))

    return messages


def convert_to_dict_conversation(messages: List[Any]) -> List[Dict[str, Any]]:
    """
    Convert a list of LangChain message objects to message dictionaries.

    Args:
        messages: List of LangChain message objects

    Returns:
        List[Dict[str, Any]]: List of message dictionaries
    """
    conversation = []

    for message in messages:
        if isinstance(message, HumanMessage):
            conversation.append({"role": "human", "content": message.content})
        elif isinstance(message, AIMessage):
            conversation.append({"role": "ai", "content": message.content})
        elif isinstance(message, SystemMessage):
            conversation.append({"role": "system", "content": message.content})

    return conversation


def save_conversation_to_json(messages: List[Any], file_path: str) -> None:
    """
    Save a conversation to a JSON file.

    Args:
        messages: List of message objects
        file_path: Path to save the JSON file
    """
    # Convert messages to dictionary format
    conversation = convert_to_dict_conversation(messages)

    # Write to file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(conversation, f, ensure_ascii=False, indent=2)


def load_conversation_from_json(file_path: str) -> List[Any]:
    """
    Load a conversation from a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        List[Any]: List of LangChain message objects
    """
    # Read from file
    with open(file_path, "r", encoding="utf-8") as f:
        json_data = f.read()

    # Parse the JSON data
    conversation = parse_json_conversation(json_data)

    # Convert to LangChain messages
    return convert_to_langchain_messages(conversation)
