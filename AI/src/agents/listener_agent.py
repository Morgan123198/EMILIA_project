"""
Listener Agent Implementation

This module contains the implementation of the empathetic listener agent
that builds rapport and identifies when to transition to CBT intervention.
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import Tool
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from src.prompts.cbt_prompts import LISTENER_PROMPT_TEMPLATE
from src.schema.cbt_state import CBTBotState
from src.utils.state_utils import get_default_state, extract_conversation_history


def transition_to_cbt(conversation_history: List[str]) -> Dict:
    """
    Transition function that updates the state to switch to CBT intervention mode.

    This function is called when the listener agent detects that the user
    is ready for CBT techniques and interventions.

    Args:
        conversation_history: List of conversation messages as strings

    Returns:
        Dict: State updates with new phase
    """
    try:
        # In a real implementation, you might do some analysis here
        # For now, we'll just transition to the CBT intervention phase

        return {
            "phase": "cbt_intervention",
            "cognitive_analysis": {
                "readiness": "user has requested specific guidance",
                "stage": "initial intervention",
            },
        }
    except Exception as e:
        print(f"Error transitioning to CBT: {e}")
        return {"phase": "cbt_intervention", "cognitive_analysis": {"error": str(e)}}


def listener_agent(
    state: CBTBotState, llm: BaseChatModel, config: Optional[RunnableConfig] = None
) -> Dict:
    """
    Empathetic listener agent that focuses on understanding the user's situation.

    This agent builds rapport, asks open-ended questions, and listens for cues
    that the user is ready for more directive CBT interventions.

    Args:
        state: Current conversation state
        llm: Language model to use
        config: Optional runnable configuration

    Returns:
        Dict: Updated state with agent's response
    """
    # Ensure state has all required keys
    if "phase" not in state:
        print("WARNING: State missing 'phase' key. Initializing default state.")
        default_state = get_default_state()
        # Preserve messages if they exist
        if "messages" in state:
            default_state["messages"] = state["messages"]
        state = default_state

    # Only process if we're in the listening phase and the last message was from the user
    if state["phase"] != "listening" or not state.get("last_user_input", False):
        return {}

    # Create the transition tool for the listener
    listener_tools = [
        Tool(
            name="transition_to_cbt",
            description="Use this tool when the user has expressed readiness for feedback, CBT techniques, or advice. Only use this when you've gathered sufficient context about the user's situation and they've indicated they're ready to receive help or techniques.",
            func=lambda: transition_to_cbt(extract_conversation_history(state)),
        ),
    ]

    # Prepare messages for the LLM
    system_msg = SystemMessage(content=LISTENER_PROMPT_TEMPLATE)
    messages = [system_msg] + state["messages"]

    # Check if the LLM is an actual LLM instance with bind_tools or a dict
    if hasattr(llm, "bind_tools"):
        # Bind tools to the language model
        llm_with_tools = llm.bind_tools(listener_tools)

        # Invoke the LLM with tools
        response = llm_with_tools.invoke(messages)

        # Debug output
        print(f"DEBUG: Listener agent response type: {type(response)}")

        # Check if the response includes tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            print(
                f"DEBUG: Tool calls detected: {[tc.get('name') for tc in response.tool_calls]}"
            )

            # Check specifically for transition_to_cbt tool
            for tool_call in response.tool_calls:
                if tool_call.get("name") == "transition_to_cbt":
                    print("DEBUG: transition_to_cbt tool was called!")

                    # Get the tool's return value
                    tool_output = tool_call.get("output", {})
                    print(f"DEBUG: Tool output: {tool_output}")

                    # Extract AI message content from the response
                    ai_content = (
                        response.content if hasattr(response, "content") else ""
                    )

                    # Create AI message with the response content
                    ai_message = AIMessage(content=ai_content)

                    # Return the transition result plus the AI message
                    return {
                        "messages": [ai_message],
                        "phase": "cbt_intervention",  # Force the phase change
                        "cognitive_analysis": tool_output.get("cognitive_analysis", {}),
                        "last_user_input": False,
                    }
    else:
        # When running in LangGraph server, the llm might be a dict or otherwise not have bind_tools
        print("DEBUG: LLM does not have bind_tools method, running in simplified mode")
        # We'll simulate the response without using tools

        # Default response when in server mode and tools aren't available
        response_text = "I see you're asking for help. Let me switch to providing some practical techniques that might help you."
        ai_message = AIMessage(content=response_text)

        # In this case, we'll always transition to CBT intervention mode since we can't use tools
        # to determine this dynamically
        return {
            "messages": [ai_message],
            "phase": "cbt_intervention",
            "cognitive_analysis": {
                "readiness": "user explicitly requested help",
                "stage": "initial intervention",
            },
            "last_user_input": False,
        }

    # If the response is not already an AIMessage, convert it
    if not isinstance(response, AIMessage):
        ai_message = AIMessage(content=str(response))
    else:
        ai_message = response

    # Return the updated state
    return {"messages": [ai_message], "last_user_input": False}
