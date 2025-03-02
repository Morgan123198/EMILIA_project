#!/usr/bin/env python3
"""
Test script to simulate a conversation with the CBT bot using a predefined conversation.
This helps verify the bot correctly transitions to CBT intervention when asked for help.
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

# Try to import the get_default_state from cbt_bot
try:
    from src.core.cbt_bot import get_default_state
except ImportError:
    print("Warning: Could not import get_default_state from src.core.cbt_bot")

    # Fallback to a local definition
    def get_default_state():
        return {
            "messages": [],
            "phase": "listening",
            "cognitive_analysis": {},
            "session_summary": {},
            "last_user_input": True,
        }


# Predefined conversation from the Spanish-speaking user dealing with bullying
CONVERSATION = [
    "hola",  # Hello
    "me siento mal, me hacen bulling en el cole",  # I feel bad, I'm being bullied at school
    "me esconden la mochila todos los dias y no se que hacer quiero llorar",  # They hide my backpack every day and I don't know what to do, I want to cry
    "no, me da miedo y no se como expresarme, cuando hago exploto y digo cosas feas, soy tonto",  # No, I'm afraid and don't know how to express myself, when I do I explode and say ugly things, I'm dumb
    "no sé cómo decirlo y siento verguenza, no se que hacer",  # I don't know how to say it and I feel ashamed, I don't know what to do
    "ok me siento hostigado porque hay niños mayores que juegan conmigo y yo soy el mas chiquito del saon y los profes parece quie hacen como que no ven y eso me da rabia, mis papas estan todo el dia en el trabajo y cuando vienen a casa solo prenden la tele. quiero llorar",  # I feel harassed because older kids play with me and I'm the smallest in the class and the teachers seem to pretend they don't see and that makes me angry, my parents are at work all day and when they come home they just turn on the TV. I want to cry
    "no, me ayudas?",  # No, can you help me?
    "si dame ideas",  # Yes, give me ideas
    "si",  # Yes
]


def main():
    """Main function to test the CBT bot with a simulated conversation."""
    # Print welcome message
    print("\n=== CBT Bot Conversation Test ===")
    print("Testing with a predefined conversation to check phase transitions...")

    # Connect to the LangGraph server
    try:
        # Get LangGraph server URL from environment variable or use default
        server_url = os.getenv("LANGGRAPH_SERVER_URL", "http://localhost:2024")
        print(f"\nConnecting to LangGraph server at {server_url}")

        # Create a sync client for working with the LangGraph server
        sync_client = get_sync_client(url=server_url)

        # Get graph name from environment variable or use default
        graph_name = os.getenv("LANGGRAPH_GRAPH_NAME", "cbt_bot")

        # Create a RemoteGraph instance for the CBT bot
        remote_graph = RemoteGraph(graph_name, url=server_url)
        print(f"Successfully created remote graph: {graph_name}")

        # Create a conversation thread
        thread = sync_client.threads.create()
        thread_id = thread["thread_id"]
        print(f"Started new conversation thread: {thread_id}")

        # Configure the thread for the conversation
        config = {"configurable": {"thread_id": thread_id}}

        # Initialize current state
        current_state = get_default_state()

        # Save AI responses for review
        ai_responses = []

        # Send greeting message from the bot
        print("\nStarting conversation simulation...")
        print(
            "\nCBT Bot: Hello! I'm here to listen and help. What's been on your mind recently?"
        )

        # Process each message in the conversation
        for i, user_input in enumerate(CONVERSATION):
            print(f"\n[Message {i+1}/{len(CONVERSATION)}] You: {user_input}")

            # Create a state for this invocation, preserving history
            fresh_state = get_default_state()

            # Use existing state as base if available
            if current_state and "messages" in current_state:
                fresh_state["messages"] = current_state["messages"]
                fresh_state["phase"] = current_state.get("phase", "listening")
                fresh_state["cognitive_analysis"] = current_state.get(
                    "cognitive_analysis", {}
                )
                fresh_state["session_summary"] = current_state.get(
                    "session_summary", {}
                )

            # Add the user's message
            fresh_state["messages"].append(HumanMessage(content=user_input))
            fresh_state["last_user_input"] = True

            # Print debug info
            print(f"Sending state to LangGraph:")
            print(f"Phase: {fresh_state.get('phase')}")
            print(f"Messages: {len(fresh_state.get('messages', []))} message(s)")

            # Invoke the remote graph
            print("\nCBT Bot is thinking...")
            try:
                result = remote_graph.invoke(fresh_state, config=config)

                # Update our local state with the result
                current_state = result

                # Print debug info about the result
                print(f"\nReceived response from LangGraph:")
                print(f"Result has {len(result.get('messages', []))} message(s)")
                print(f"Current phase: {result.get('phase', 'unknown')}")

                # Find and display the bot's response
                if result and "messages" in result and result["messages"]:
                    # Try different methods to find AI messages
                    ai_messages = []

                    # Method 1: Direct instance check
                    ai_messages = [
                        m for m in result["messages"] if isinstance(m, AIMessage)
                    ]

                    # Method 2: Check type attribute if available
                    if not ai_messages:
                        ai_messages = [
                            m
                            for m in result["messages"]
                            if hasattr(m, "type") and m.type == "ai"
                        ]

                    # Method 3: Check dictionary for type key
                    if not ai_messages:
                        ai_messages = [
                            m
                            for m in result["messages"]
                            if isinstance(m, dict) and m.get("type") == "ai"
                        ]

                    # Method 4: Check for content key in dictionaries
                    if not ai_messages:
                        ai_messages = [
                            m
                            for m in result["messages"]
                            if isinstance(m, dict) and "content" in m
                        ]

                    # Method 5: Get all non-user messages as a fallback
                    if not ai_messages:
                        # First identify human messages
                        human_messages = [
                            m
                            for m in result["messages"]
                            if isinstance(m, HumanMessage)
                            or (hasattr(m, "type") and m.type == "human")
                            or (isinstance(m, dict) and m.get("type") == "human")
                        ]
                        # Then get everything that's not a human message
                        ai_messages = [
                            m for m in result["messages"] if m not in human_messages
                        ]

                    # Print debug info about the messages
                    print(f"DEBUG: Found {len(ai_messages)} AI messages")

                    if ai_messages:
                        last_ai_message = ai_messages[-1]

                        # Get content based on message type
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
                        ai_responses.append(message_content)
                    else:
                        print("\nWarning: No AI messages found in response.")
                        ai_responses.append("NO RESPONSE")

                    # Check if we've transitioned to CBT intervention
                    if result.get("phase") == "cbt_intervention":
                        print(
                            "\n*** TRANSITION DETECTED: Now in CBT intervention phase ***"
                        )
                        print(
                            f"Cognitive analysis: {json.dumps(result.get('cognitive_analysis', {}), indent=2)}"
                        )

                # Add a pause between messages to avoid overwhelming the server
                time.sleep(2)

            except Exception as e:
                print(f"\nError during graph invocation: {e}")
                import traceback

                traceback.print_exc()
                break

        # Summary of the conversation
        print("\n=== Conversation Summary ===")
        print(f"Total messages exchanged: {len(CONVERSATION)}")
        print(f"Final phase: {current_state.get('phase', 'unknown')}")

        if current_state.get("phase") == "cbt_intervention":
            print("✅ Successfully transitioned to CBT intervention phase")
        else:
            print("❌ Failed to transition to CBT intervention phase")

        print("\n=== Test Complete ===")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
