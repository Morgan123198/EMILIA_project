#!/usr/bin/env python3
"""
CBT Bot Interactive Client

This script provides an interactive command-line client for the CBT bot.
"""

import os
import sys
import argparse
import json
from dotenv import load_dotenv
from langgraph.pregel.remote import RemoteGraph, get_sync_client
from langchain_core.messages import HumanMessage

from src.utils.state_utils import get_default_state
from src.core.config import get_settings


def main():
    """Main function for interactive CBT bot client."""

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Interactive CBT bot client.")
    parser.add_argument(
        "--server",
        type=str,
        default="http://localhost:2024",
        help="LangGraph server URL",
    )
    parser.add_argument(
        "--graph", type=str, default="cbt_bot", help="Name of the graph on the server"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Get settings
    settings = get_settings()

    # Check API key
    if not settings.OPENROUTER_API_KEY:
        print(
            "Warning: OPENROUTER_API_KEY not found. Server may not be able to process requests."
        )

    # Initialize variables
    client = None
    remote_graph = None
    thread_id = None
    config = None
    current_state = None

    # Print welcome message
    print("\n=== CBT Bot Interactive Client ===")
    print(f"Using model: {settings.LLM_MODEL}")
    print("Type 'exit', 'quit', or 'bye' to end the conversation.")
    print("Type 'debug' to view the current conversation state.")
    print("Starting conversation...\n")

    # Connect to LangGraph server
    try:
        # Initialize the client
        client = get_sync_client(url=args.server)

        # Create a RemoteGraph instance
        remote_graph = RemoteGraph(args.graph, url=args.server)
        print(f"Connected to LangGraph server at {args.server}")
        print(f"Successfully connected to graph: {args.graph}")

        # Create a conversation thread
        thread = client.threads.create()
        thread_id = thread["thread_id"]
        print(f"Started new conversation thread: {thread_id}\n")

        # Configure the thread for conversation
        config = {"configurable": {"thread_id": thread_id}}

        # Initialize state
        current_state = get_default_state()

        # Display initial bot message
        print(
            "CBT Bot: Hello! I'm here to listen and help. What's been on your mind recently?"
        )

    except Exception as e:
        print(f"Error connecting to LangGraph server: {e}")
        return

    # Main conversation loop
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()

            # Handle special commands
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\nExiting conversation. Goodbye!")
                break
            elif user_input.lower() == "debug":
                print("\n=== Debug Information ===")
                print(f"Current phase: {current_state.get('phase', 'unknown')}")
                print(
                    f"Last user input: {current_state.get('last_user_input', 'unknown')}"
                )
                print(f"Message count: {len(current_state.get('messages', []))}")

                if "cognitive_analysis" in current_state:
                    print("\nCognitive Analysis:")
                    for key, value in current_state["cognitive_analysis"].items():
                        print(f"  {key}: {value}")

                if (
                    "identified_distortions" in current_state
                    and current_state["identified_distortions"]
                ):
                    print("\nIdentified Distortions:")
                    for i, distortion in enumerate(
                        current_state["identified_distortions"]
                    ):
                        print(
                            f"  {i+1}. {distortion.get('type')}: {distortion.get('explanation', '')[:100]}..."
                        )

                if (
                    "recommended_techniques" in current_state
                    and current_state["recommended_techniques"]
                ):
                    print("\nRecommended Techniques:")
                    for i, technique in enumerate(
                        current_state["recommended_techniques"]
                    ):
                        print(f"  {i+1}. {technique.get('name')}")

                print("=== End Debug Info ===\n")
                continue

            # Create a state for this invocation
            state_for_invocation = get_default_state()

            # If we have an existing state, use it as the base
            if current_state and "messages" in current_state:
                state_for_invocation["messages"] = current_state["messages"]
                state_for_invocation["phase"] = current_state.get("phase", "listening")
                state_for_invocation["cognitive_analysis"] = current_state.get(
                    "cognitive_analysis", {}
                )
                state_for_invocation["identified_distortions"] = current_state.get(
                    "identified_distortions", []
                )
                state_for_invocation["recommended_techniques"] = current_state.get(
                    "recommended_techniques", []
                )
                state_for_invocation["session_summary"] = current_state.get(
                    "session_summary", {}
                )

            # Add the human message
            state_for_invocation["messages"].append(HumanMessage(content=user_input))
            state_for_invocation["last_user_input"] = True

            # Print debug info if enabled
            if args.debug:
                print("\nSending state to LangGraph:")
                print(f"Phase: {state_for_invocation.get('phase')}")
                print(
                    f"Messages: {len(state_for_invocation.get('messages', []))} message(s)"
                )
                print(f"Last user input: {state_for_invocation.get('last_user_input')}")

            # Invoke the remote graph
            print("\nCBT Bot is thinking...")
            result = remote_graph.invoke(state_for_invocation, config=config)

            # Update our local state
            current_state = result

            # Print debug info if enabled
            if args.debug:
                print(f"\nReceived response from LangGraph:")
                print(f"Result has {len(result.get('messages', []))} message(s)")
                print(f"Phase: {result.get('phase')}")

                # Print a message if we transitioned to CBT intervention
                if (
                    result.get("phase") == "cbt_intervention"
                    and state_for_invocation.get("phase") == "listening"
                ):
                    print("*** TRANSITION DETECTED: Now in CBT intervention phase ***")

            # Print the bot's response - only the latest response
            if result and "messages" in result and result["messages"]:
                # Find all messages that aren't from the user
                ai_messages = [
                    m for m in result["messages"] if not isinstance(m, HumanMessage)
                ]

                if ai_messages:
                    # Get the most recent AI message
                    latest_message = ai_messages[-1]
                    if hasattr(latest_message, "content"):
                        print(f"\nCBT Bot: {latest_message.content}")
                    else:
                        print("\nCBT Bot: [No message content]")
                else:
                    print("\nCBT Bot: [No response]")
            else:
                print("\nCBT Bot: [No response]")

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nError during conversation: {e}")
            if args.debug:
                import traceback

                traceback.print_exc()

    print("\nConversation ended.")


if __name__ == "__main__":
    main()
