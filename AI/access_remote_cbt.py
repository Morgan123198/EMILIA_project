#!/usr/bin/env python3
"""
Script to interact with a remotely deployed CBT bot through LangGraph Studio.
Handles conversation state and ensures proper request/response flow.
"""

import os
import sys
import json
import time
from dotenv import load_dotenv
from langgraph.pregel.remote import RemoteGraph, get_sync_client
from langchain_core.messages import HumanMessage, AIMessage

# Load environment variables
load_dotenv()

# Add the current directory to the path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Try to import get_default_state from the CBT bot module
try:
    from src.core.cbt_bot import get_default_state
except ImportError:
    print("Warning: Could not import get_default_state from src.core.cbt_bot")

    # Define a fallback default state function
    def get_default_state():
        return {
            "messages": [],
            "phase": "listening",
            "cognitive_analysis": {},
            "session_summary": {},
            "last_user_input": True,
        }


def main():
    """Main function to interact with the remote CBT bot."""
    # Print welcome message
    print("\n=== CBT Bot Remote Client ===")
    print("Type 'exit', 'quit', or 'bye' to end the conversation.")
    print("Type 'debug' to view the current conversation state.")
    print("Starting conversation...\n")

    # Connect to the LangGraph server
    try:
        # Get LangGraph server URL from environment variable or use default
        server_url = os.getenv("LANGGRAPH_SERVER_URL", "http://localhost:2024")

        # Create a sync client for working with the LangGraph server
        sync_client = get_sync_client(url=server_url)
        print(f"Connected to LangGraph server at {server_url}")

        # Get graph name from environment variable or use default
        graph_name = os.getenv("LANGGRAPH_GRAPH_NAME", "cbt_bot")

        # Create a RemoteGraph instance for the CBT bot
        remote_graph = RemoteGraph(graph_name, url=server_url)
        print(f"Successfully created remote graph: {graph_name}")

        # Create a conversation thread
        thread = sync_client.threads.create()
        thread_id = thread["thread_id"]
        print(f"Started new conversation thread: {thread_id}\n")

        # Configure the thread for the conversation
        config = {"configurable": {"thread_id": thread_id}}

        # Initial bot message
        print(
            "CBT Bot: Hello! I'm here to listen and help. What's been on your mind recently?"
        )

        # Initialize state for first invocation
        current_state = get_default_state()

        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()

                # Handle special commands
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\nExiting conversation. Goodbye!")
                    break
                elif user_input.lower() == "debug":
                    # Get the current state of the conversation
                    try:
                        state_snapshot = remote_graph.get_state(config)
                        if state_snapshot and hasattr(state_snapshot, "values"):
                            debug_state = state_snapshot.values
                            print("\n=== Debug Information ===")
                            print(
                                f"Current phase: {debug_state.get('phase', 'unknown')}"
                            )
                            print(
                                f"Last user input: {debug_state.get('last_user_input', 'unknown')}"
                            )
                            print(
                                f"Message count: {len(debug_state.get('messages', []))}"
                            )
                            print(
                                f"Cognitive analysis: {json.dumps(debug_state.get('cognitive_analysis', {}), indent=2)}"
                            )
                            print("=== End Debug Info ===\n")
                        else:
                            print("\nNo state available yet, using local state:")
                            print("\n=== Debug Information (Local) ===")
                            print(
                                f"Current phase: {current_state.get('phase', 'unknown')}"
                            )
                            print(
                                f"Last user input: {current_state.get('last_user_input', 'unknown')}"
                            )
                            print(
                                f"Message count: {len(current_state.get('messages', []))}"
                            )
                            print(
                                f"Cognitive analysis: {json.dumps(current_state.get('cognitive_analysis', {}), indent=2)}"
                            )
                            print("=== End Debug Info ===\n")
                    except Exception as e:
                        print(f"\nError retrieving state: {e}")
                        print("\nUsing local state:")
                        print("\n=== Debug Information (Local) ===")
                        print(f"Current phase: {current_state.get('phase', 'unknown')}")
                        print(
                            f"Last user input: {current_state.get('last_user_input', 'unknown')}"
                        )
                        print(
                            f"Message count: {len(current_state.get('messages', []))}"
                        )
                        print(
                            f"Cognitive analysis: {json.dumps(current_state.get('cognitive_analysis', {}), indent=2)}"
                        )
                        print("=== End Debug Info ===\n")
                    continue

                # Create a fresh state for each invocation to avoid state conflicts
                fresh_state = get_default_state()

                # If we have an existing state from previous responses, use that as the base
                if current_state and "messages" in current_state:
                    # Preserve all existing messages
                    fresh_state["messages"] = current_state["messages"]
                    # Preserve the phase from current state
                    fresh_state["phase"] = current_state.get("phase", "listening")
                    # Preserve cognitive analysis if available
                    fresh_state["cognitive_analysis"] = current_state.get(
                        "cognitive_analysis", {}
                    )
                    # Preserve session summary if available
                    fresh_state["session_summary"] = current_state.get(
                        "session_summary", {}
                    )

                # Add the user's message to the messages list
                fresh_state["messages"].append(HumanMessage(content=user_input))

                # Set the last_user_input flag to True
                fresh_state["last_user_input"] = True

                # Print debug info before invoking the graph
                print("\nSending state to LangGraph:")
                print(f"Phase: {fresh_state.get('phase')}")
                print(f"Messages: {len(fresh_state.get('messages', []))} message(s)")
                print(f"Last user input: {fresh_state.get('last_user_input')}")

                # Invoke the remote graph with the fresh state
                print("\nCBT Bot is thinking...")
                try:
                    result = remote_graph.invoke(fresh_state, config=config)

                    # Update our local state with the result
                    current_state = result

                    # Print debug info about the result
                    print(f"\nReceived response from LangGraph:")
                    print(f"Result has {len(result.get('messages', []))} message(s)")
                    print(f"Phase: {result.get('phase')}")

                    # Display the bot's response
                    if result and "messages" in result and result["messages"]:
                        # Get all messages
                        all_messages = result["messages"]
                        print(f"DEBUG: All messages count: {len(all_messages)}")
                        print(
                            f"DEBUG: Message types: {[type(m).__name__ for m in all_messages]}"
                        )

                        # Try to find AI messages by different methods
                        ai_messages = []

                        # Method 1: Direct instance check
                        ai_messages = [
                            m for m in all_messages if isinstance(m, AIMessage)
                        ]

                        # Method 2: Check type attribute if available
                        if not ai_messages:
                            ai_messages = [
                                m
                                for m in all_messages
                                if hasattr(m, "type") and m.type == "ai"
                            ]

                        # Method 3: Check dictionary for type
                        if not ai_messages:
                            ai_messages = [
                                m
                                for m in all_messages
                                if isinstance(m, dict) and m.get("type") == "ai"
                            ]

                        # Method 4: Check any message that's not from the user
                        if not ai_messages:
                            human_messages = [
                                m for m in all_messages if isinstance(m, HumanMessage)
                            ]
                            ai_messages = [
                                m for m in all_messages if m not in human_messages
                            ]

                        if ai_messages:
                            last_ai_message = ai_messages[-1]

                            # Get the content based on the message type
                            if hasattr(last_ai_message, "content"):
                                message_content = last_ai_message.content
                            elif (
                                isinstance(last_ai_message, dict)
                                and "content" in last_ai_message
                            ):
                                message_content = last_ai_message["content"]
                            else:
                                message_content = str(last_ai_message)

                            print(f"\nCBT Bot: {message_content}")
                            if "phase" in result:
                                print(f"[DEBUG] Current phase: {result['phase']}")
                        else:
                            print("\nWarning: No AI response in the messages.")
                            # Print all messages for debugging
                            print(f"All messages: {all_messages}")
                    else:
                        print("\nWarning: No valid messages in the response.")
                        print(f"Result keys: {result.keys() if result else 'None'}")

                except Exception as e:
                    print(f"\nError during graph invocation: {e}")
                    import traceback

                    traceback.print_exc()

                    # Try a simpler approach as fallback
                    print("\nAttempting fallback approach...")
                    try:
                        # Try to update the state first
                        remote_graph.update_state(config, fresh_state)
                        time.sleep(1)  # Give the server some time

                        # Then get the updated state
                        state_snapshot = remote_graph.get_state(config)
                        if state_snapshot and hasattr(state_snapshot, "values"):
                            result = state_snapshot.values

                            # Display the bot's response
                            if result and "messages" in result and result["messages"]:
                                # Find the last AI message
                                ai_messages = [
                                    m
                                    for m in result["messages"]
                                    if isinstance(m, AIMessage)
                                ]

                                if ai_messages:
                                    last_ai_message = ai_messages[-1]
                                    print(
                                        f"\nCBT Bot (fallback): {last_ai_message.content}"
                                    )
                            else:
                                print("\nNo messages found in fallback response.")
                    except Exception as fallback_error:
                        print(f"\nFallback approach failed: {fallback_error}")

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"\nUnexpected error: {e}")
                import traceback

                traceback.print_exc()

        print("\nConversation ended.")

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nError connecting to LangGraph server: {e}")
        print(f"Please ensure the LangGraph server is running at {server_url}")
        print("You can start it with: poetry run langgraph dev")


if __name__ == "__main__":
    main()
