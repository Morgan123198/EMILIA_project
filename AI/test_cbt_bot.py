#!/usr/bin/env python3
"""
Test script for the CBT Bot implementation using LangGraph.
This script provides a simple command line interface to interact with the CBT bot.
"""

from dotenv import load_dotenv
import os
import sys
import traceback

# Add the current directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from src.core.cbt_bot import chat_with_cbt_bot
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this script from the project root directory")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

# Load environment variables
load_dotenv()


def main():
    """Run a simple interactive session with the CBT bot."""
    print("=" * 70)
    print("CBT Bot - Cognitive Behavioral Therapy Conversation Agent")
    print("=" * 70)
    print("This bot will listen to your concerns and then offer CBT-based feedback.")
    print("Type 'exit', 'quit', or 'bye' to end the conversation.")
    print("Type 'debug' to see current state information.")
    print("=" * 70)
    print(
        "\nCBT Bot: Hello! I'm here to listen and help. What's been on your mind recently?"
    )

    state = None

    while True:
        try:
            user_input = input("\nYou: ")

            # Handle special commands
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\nCBT Bot: Thank you for talking with me today. Take care!")
                break
            elif user_input.lower() == "debug":
                if state:
                    print("\n----- Current State -----")
                    print(f"Phase: {state.get('phase', 'None')}")
                    print(
                        f"Ready for feedback: {state.get('ready_for_feedback', False)}"
                    )
                    print(f"Number of messages: {len(state.get('messages', []))}")
                    print(f"Cognitive analysis: {state.get('cognitive_analysis', {})}")
                    print("------------------------\n")
                else:
                    print("\nNo state available yet.")
                continue

            # Process normal input
            state = chat_with_cbt_bot(user_input, state)

            if state and "messages" in state and state["messages"]:
                last_message = state["messages"][-1]
                print(f"\nCBT Bot: {last_message.content}")
                print(f"[DEBUG] Current phase: {state.get('phase', 'unknown')}")
            else:
                print("\nError: No valid response from the bot.")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Details:")
            traceback.print_exc()
            print("\nPlease try again.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
