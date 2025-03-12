#!/usr/bin/env python3
"""
CBT Bot JSON Test Script

This script tests the CBT bot with a conversation loaded from a JSON file.
It includes all previous conversation turns from the JSON as context,
then invokes the bot only once with the final human message.
"""

import os
import argparse
import json
from dotenv import load_dotenv
from langgraph.pregel.remote import RemoteGraph, get_sync_client
from langchain_core.messages import HumanMessage, AIMessage

from src.utils.state_utils import get_default_state
from src.utils.conversation_parser import load_conversation_from_json
from src.core.config import get_settings


def main():
    """Main function to run the CBT bot JSON test with the final message only."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Test the CBT bot with the final message of a JSON conversation."
    )
    parser.add_argument(
        "--conversation",
        type=str,
        required=True,
        help="Path to the JSON file containing the conversation to test",
    )
    parser.add_argument(
        "--server",
        type=str,
        default="http://localhost:2024",
        help="LangGraph server URL",
    )
    parser.add_argument(
        "--graph", type=str, default="cbt_bot", help="Name of the graph on the server"
    )
    parser.add_argument("--debug", action="store_true", help="Show debug information")
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Get settings
    settings = get_settings()

    # Check if OpenRouter API key is set
    if not settings.OPENROUTER_API_KEY:
        print(
            "Warning: OPENROUTER_API_KEY not found. Server may not be able to process requests."
        )

    # Load the conversation
    try:
        all_messages = load_conversation_from_json(args.conversation)
        message_count = len(all_messages)
        print(
            f"Loaded conversation with {message_count} messages from {args.conversation}"
        )

        if message_count == 0:
            print("Error: No messages found in the conversation file")
            return

        # Check if we have at least one human message
        human_messages = [msg for msg in all_messages if isinstance(msg, HumanMessage)]
        if not human_messages:
            print("Error: No human messages found in the conversation")
            return

        # Get the last human message
        last_human_index = -1
        for i in range(len(all_messages) - 1, -1, -1):
            if isinstance(all_messages[i], HumanMessage):
                last_human_index = i
                break

        if last_human_index < 0:
            print("Error: Could not find the last human message")
            return

        # Use all messages up to the last human message as context
        context_messages = all_messages[:last_human_index]
        last_human_message = all_messages[last_human_index]

        print(f"Using {len(context_messages)} messages as context")
        print(
            f"Will invoke the bot with the last human message: \"{last_human_message.content[:100]}{'...' if len(last_human_message.content) > 100 else ''}\""
        )

    except Exception as e:
        print(f"Error loading conversation: {e}")
        return

    # Connect to LangGraph server
    try:
        # Initialize the client
        client = get_sync_client(url=args.server)
        print(f"Connected to LangGraph server at {args.server}")

        # Create a RemoteGraph instance
        remote_graph = RemoteGraph(args.graph, sync_client=client)
        print(f"Successfully initialized RemoteGraph for: {args.graph}\n")

        # Create a conversation thread for persistence
        thread = client.threads.create()
        thread_id = thread["thread_id"]
        print(f"Started new conversation thread: {thread_id}\n")

        # Configure the thread for conversation
        config = {"configurable": {"thread_id": thread_id}}

        # Convert messages to simple dict representation
        simple_context_messages = []
        for msg in context_messages:
            if isinstance(msg, HumanMessage):
                simple_context_messages.append(
                    {"type": "human", "content": msg.content}
                )
            elif isinstance(msg, AIMessage):
                simple_context_messages.append({"type": "ai", "content": msg.content})

        # Convert the last human message
        simple_last_human = {"type": "human", "content": last_human_message.content}

        # Set the phase based on context
        # For simplicity, if we have context messages, we'll check if any AI messages
        # suggest we're in the CBT intervention phase
        cbt_intervention_indicators = [
            "cognitive distortion",
            "negative thought pattern",
            "reframe",
            "distortion",
            "técnica",  # For Spanish: technique
            "técnicas",  # For Spanish: techniques
            "distorsión",  # For Spanish: distortion
            "distorsiones",  # For Spanish: distortions
            "pensamiento negativo",  # For Spanish: negative thought
        ]

        # Analyze AI messages for indicators
        phase = "listening"
        for msg in simple_context_messages:
            if msg["type"] == "ai" and any(
                indicator.lower() in msg["content"].lower()
                for indicator in cbt_intervention_indicators
            ):
                phase = "cbt_intervention"
                print("Based on context, setting initial phase to: cbt_intervention")
                break

        if phase == "listening":
            print("Initial phase set to: listening")

        print(f"Initial phase before invocation: {phase}")

        # Create input state with context and last human message
        input_state = {
            "messages": simple_context_messages + [simple_last_human],
            "phase": phase,
            "last_user_input": True,
        }

        # Invoke the remote graph
        print("\nInvoking CBT bot with the last human message...")
        result = remote_graph.invoke(input_state, config=config)

        # Print the results
        print(f"\n=== Results ===")
        print(f"Final phase: {result.get('phase', 'unknown')}")

        # Check for phase transition
        if phase != result.get("phase"):
            print(f"Phase transition: {phase} -> {result.get('phase')}")

        # Print the bot's response
        if "messages" in result and result["messages"]:
            ai_messages = [
                m
                for m in result["messages"]
                if isinstance(m, dict) and m.get("type") == "ai"
            ]
            if ai_messages:
                latest_ai_msg = ai_messages[-1]
                print("\nBot's response:")
                if "content" in latest_ai_msg and latest_ai_msg["content"]:
                    print(f"{latest_ai_msg['content']}")
                else:
                    print("[No message content]")
            else:
                print("\nNo AI response received")
        else:
            print("\nNo messages in result")

        # Print cognitive analysis if present and in debug mode
        if "cognitive_analysis" in result and result["cognitive_analysis"]:
            print("\nCognitive Analysis:")
            for key, value in result["cognitive_analysis"].items():
                if isinstance(value, str):
                    print(f"  {key}: {value[:100]}{'...' if len(value) > 100 else ''}")
                else:
                    print(f"  {key}: {value}")

        # Print identified distortions
        if "identified_distortions" in result and result["identified_distortions"]:
            print(
                f"\nIdentified Distortions ({len(result['identified_distortions'])}):"
            )
            for i, distortion in enumerate(result["identified_distortions"]):
                distortion_type = distortion.get("type", "Unknown")
                explanation = distortion.get("explanation", "")
                print(
                    f"  {i+1}. {distortion_type}: {explanation[:100]}{'...' if len(explanation) > 100 else ''}"
                )

        # Print recommended techniques
        if "recommended_techniques" in result and result["recommended_techniques"]:
            print(
                f"\nRecommended Techniques ({len(result['recommended_techniques'])}):"
            )
            for i, technique in enumerate(result["recommended_techniques"]):
                technique_name = technique.get("name", "Unknown")
                description = technique.get("description", "")
                print(
                    f"  {i+1}. {technique_name}: {description[:100]}{'...' if len(description) > 100 else ''}"
                )

        print("\nTest completed successfully.")

    except Exception as e:
        import traceback

        print(f"Error during test: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
