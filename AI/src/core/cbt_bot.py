#!/usr/bin/env python3
import json
from typing import Annotated, TypedDict, List, Dict, Any, Literal
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    AIMessage,
)
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.tools import Tool
from langchain_core.runnables import RunnableConfig

# Try importing the settings and LLM, but provide a fallback for local testing
try:
    from src.core.config import get_settings
    from src.core.llm import llm
    from src.tools.cbt_tools import (
        identify_cognitive_distortions,
        recommend_cbt_techniques,
        analyze_thought_patterns,
    )

    settings = get_settings()
    print("Loaded LLM configuration from settings")
except Exception as e:
    print(f"Warning: Error loading LLM configuration: {e}")
    print("Using fallback LLM for local testing")
    # Fallback to a basic LLM for local testing
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model="Gemini Flash 2.0")

    # Mock tools for local testing
    def identify_cognitive_distortions(text):
        return json.dumps(
            {
                "distortions": ["black and white thinking", "catastrophizing"],
                "explanation": "This is a mock response for testing",
            }
        )

    def recommend_cbt_techniques(text):
        return json.dumps(
            {
                "techniques": ["thought records", "cognitive restructuring"],
                "explanation": "This is a mock response for testing",
            }
        )

    def analyze_thought_patterns(text):
        return json.dumps(
            {
                "patterns": ["negative self-talk", "fortune telling"],
                "recommendations": "This is a mock response for testing",
            }
        )


# Define state types
class CBTBotState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    phase: Literal["listening", "cbt_intervention"]
    cognitive_analysis: Dict[str, Any]
    session_summary: Dict[str, Any]
    last_user_input: bool  # Flag to track if the last message was from the user


# Default state initialization function
def get_default_state() -> CBTBotState:
    """Return a default initialized state dictionary with all required keys."""
    return {
        "messages": [],
        "phase": "listening",
        "cognitive_analysis": {},
        "session_summary": {},
        "last_user_input": True,  # Start with True to trigger the first response
    }


# Transition function for switching to CBT intervention
def transition_to_cbt(conversation_history: List[str]) -> Dict:
    """
    Transition function that updates the state to switch to CBT intervention mode.

    Args:
        conversation_history: List of conversation messages as strings

    Returns:
        Dict: State updates with new phase and analysis
    """
    # Analyze the conversation before transitioning
    try:
        analyze_result = analyze_thought_patterns(
            json.dumps({"conversation_history": conversation_history})
        )

        # Return the updated state keys
        return {
            "phase": "cbt_intervention",
            "cognitive_analysis": json.loads(analyze_result),
        }
    except Exception as e:
        print(f"Error analyzing thought patterns: {e}")
        return {"phase": "cbt_intervention", "cognitive_analysis": {"error": str(e)}}


# Listener Agent - Focuses on empathetic conversation and information gathering
def listener_agent(state: CBTBotState, config: RunnableConfig = None) -> Dict:
    """Empathetic listener that focuses on understanding the user's situation."""

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

    # Remove the hardcoded phrases check - we don't want that

    # Create the transition tool for the listener
    listener_tools = [
        Tool(
            name="transition_to_cbt",
            description="Use this tool when the user has expressed readiness for feedback, CBT techniques, or advice. Only use this when you've gathered sufficient context about the user's situation and they've indicated they're ready to receive help or techniques.",
            func=lambda: transition_to_cbt(
                [
                    m.content
                    for m in state["messages"]
                    if hasattr(m, "content") and isinstance(m.content, str)
                ]
            ),
        ),
    ]

    llm_with_tools = llm.bind_tools(listener_tools)

    # System message for the listener agent
    system_msg = SystemMessage(
        content="""You are an empathetic therapist focused on understanding the user's thoughts, feelings, and experiences. 
        Your goal is to build rapport and gather information through thoughtful questions.
        
        Guidelines:
        1. Ask open-ended questions that encourage the user to share more
        2. Show genuine empathy and understanding for their situation
        3. Reflect back what you hear to show you're listening
        4. Gently explore underlying thoughts and feelings
        5. Be patient and allow the user to express themselves fully
        6. Look for patterns in their thinking without immediately labeling them
        7. IMPORTANT: Always respond in the same language the user is using. If they write in Spanish, respond in Spanish. If they write in English, respond in English, etc.
        
        TRANSITION INSTRUCTIONS:
        When the user asks for help, ideas, suggestions, or techniques, you MUST use the transition_to_cbt tool.
        Look for any expressions that indicate they want specific guidance, techniques, or advice.
        
        When the user indicates any readiness for feedback or advice, use the transition_to_cbt tool immediately.
        Don't ask additional questions if they've clearly requested help or advice - just make the transition.
        
        If the user expresses interest in receiving feedback, CBT techniques, or advice, use the 
        transition_to_cbt tool to transition to the CBT specialist. Use your judgment to determine
        when the user is ready - don't just look for specific phrases, but understand their intent.
        
        IMPORTANT: DO NOT announce the transition or mention that you're calling another specialist.
        Instead, just respond naturally to their request for help with a brief acknowledgment and
        immediately use the transition_to_cbt tool.
        
        Example transition response: "Entiendo que necesitas ayuda concreta. Te voy a ofrecer algunas técnicas específicas."
        """
    )

    messages = [system_msg] + state["messages"]
    response = llm_with_tools.invoke(messages)

    # Debug output
    print(f"DEBUG: Listener agent response type: {type(response)}")

    # Check if the response includes tool calls
    if hasattr(response, "tool_calls") and response.tool_calls:
        print(f"DEBUG: Tool calls detected: {response.tool_calls}")

        # Check specifically for transition_to_cbt tool
        for tool_call in response.tool_calls:
            if tool_call.get("name") == "transition_to_cbt":
                print("DEBUG: transition_to_cbt tool was called!")

                # Get the tool's return value
                tool_output = tool_call.get("output", {})
                print(f"DEBUG: Tool output: {tool_output}")

                # Extract AI message content from the response
                ai_content = response.content if hasattr(response, "content") else ""

                # Create AI message with the response content
                ai_message = AIMessage(content=ai_content)

                # Return the transition result plus the AI message
                return {
                    "messages": [ai_message],
                    "phase": "cbt_intervention",  # Force the phase change
                    "cognitive_analysis": tool_output.get("cognitive_analysis", {}),
                    "last_user_input": False,
                }

    # If the response is not already an AIMessage, convert it
    if not isinstance(response, AIMessage):
        ai_message = AIMessage(content=str(response))
    else:
        ai_message = response

    # Set the last_user_input flag to False since we just processed a user input
    return {"messages": [ai_message], "last_user_input": False}


# CBT Intervention Agent - Analyzes conversation and provides CBT techniques
def cbt_intervention_agent(state: CBTBotState, config: RunnableConfig = None) -> Dict:
    """CBT specialist that provides cognitive behavioral therapy techniques and insights."""

    # Ensure state has all required keys
    if "phase" not in state:
        print("WARNING: State missing 'phase' key. Initializing default state.")
        default_state = get_default_state()
        # Preserve messages if they exist
        if "messages" in state:
            default_state["messages"] = state["messages"]
        state = default_state

    # Only process if we're in the CBT intervention phase and the last message was from the user
    if state["phase"] != "cbt_intervention" or not state.get("last_user_input", False):
        return {}

    # Create tools for the CBT agent
    cbt_tools = [
        Tool(
            name="identify_cognitive_distortions",
            description="Identify potential cognitive distortions in user's thinking patterns",
            func=identify_cognitive_distortions,
        ),
        Tool(
            name="recommend_cbt_techniques",
            description="Recommend specific CBT techniques based on identified patterns",
            func=recommend_cbt_techniques,
        ),
        Tool(
            name="analyze_thought_patterns",
            description="Analyze thought patterns for common CBT themes",
            func=analyze_thought_patterns,
        ),
    ]

    llm_with_cbt_tools = llm.bind_tools(cbt_tools)

    # System message for the CBT intervention agent
    system_msg = SystemMessage(
        content="""You are a CBT specialist trained in Dr. Aaron Beck's Cognitive Behavioral Therapy methods. 
        Your goal is to help the user identify and challenge cognitive distortions and develop healthier thinking patterns.
        
        Guidelines:
        1. Review the conversation history thoughtfully
        2. Use the identify_cognitive_distortions tool to recognize potential distortions in their thinking
        3. Explain identified cognitive distortions in a non-judgmental, educational way
        4. Use the recommend_cbt_techniques tool to suggest specific techniques that address their needs
        5. Provide clear, actionable guidance on how to implement CBT techniques
        6. Maintain a supportive, collaborative approach
        7. Focus on practical skills the user can apply in their daily life
        8. IMPORTANT: Always respond in the same language the user is using. If they write in Spanish, respond in Spanish. If they write in English, respond in English, etc.
        
        Remember to:
        - Explain the connection between thoughts, feelings, and behaviors
        - Normalize their experiences while offering a path forward
        - Validate their feelings while gently challenging unhelpful thought patterns
        - Provide specific examples relevant to their situation
        - Encourage practice and self-monitoring of thoughts 
        Remember to review all previous messages to maintain context and provide relevant techniques based on their entire situation.
        """
    )

    # Get all the messages from the state and add our system message at the beginning
    messages = [system_msg] + state["messages"]

    # Print debug info before calling the LLM
    print(f"DEBUG: CBT agent processing with {len(messages)} messages")
    print(f"DEBUG: Current phase: {state['phase']}")
    print(
        f"DEBUG: Last message: {messages[-1].content if messages and hasattr(messages[-1], 'content') else 'N/A'}"
    )

    response = llm_with_cbt_tools.invoke(messages)

    # Debug output
    print(f"DEBUG: CBT agent response type: {type(response)}")

    # If the response is not already an AIMessage, convert it
    if not isinstance(response, AIMessage):
        ai_message = AIMessage(content=str(response))
    else:
        ai_message = response

    # Set the last_user_input flag to False since we just processed a user input
    return {"messages": [ai_message], "last_user_input": False}


# Conditional routing based on phase
def route_based_on_phase(state: CBTBotState) -> str:
    """Routes to the appropriate agent based on the current phase."""

    # Ensure state has the phase key
    if "phase" not in state:
        print("WARNING: State missing 'phase' key. Initializing default state.")
        default_state = get_default_state()
        # Preserve messages if they exist
        if "messages" in state:
            default_state["messages"] = state["messages"]
        state = default_state

    # Print debug info about the current routing state
    message_count = len(state.get("messages", []))
    print(
        f"DEBUG: Routing with phase '{state.get('phase')}' and {message_count} messages"
    )
    print(f"DEBUG: last_user_input = {state.get('last_user_input')}")

    # If we've already processed this input (last_user_input is False), we're done
    # This is crucial to prevent recursion
    if not state.get("last_user_input", True):
        # Use the actual END constant, not a string
        print("DEBUG: Ending processing cycle - last_user_input is False")
        return END

    # Extra check - ensure we're enforcing the phase
    if "phase" in state and state["phase"] == "cbt_intervention":
        print("DEBUG: Routing to cbt_intervention phase")
        return "cbt_intervention"

    # Default route to listener
    print("DEBUG: Routing to listener phase")
    return "listener"


# Create the CBT bot graph
def create_cbt_graph():
    # Initialize graph
    graph = StateGraph(CBTBotState)

    # Add nodes for each phase
    graph.add_node("listener", listener_agent)
    graph.add_node("cbt_intervention", cbt_intervention_agent)

    # Add conditional edges based on the current phase
    graph.add_conditional_edges(
        "listener",
        route_based_on_phase,
        {
            "listener": "listener",
            "cbt_intervention": "cbt_intervention",
            END: END,  # Map the END constant to itself
        },
    )

    # Add conditional edges to route from CBT intervention
    graph.add_conditional_edges(
        "cbt_intervention",
        route_based_on_phase,
        {
            "listener": "listener",
            "cbt_intervention": "cbt_intervention",
            END: END,  # Map the END constant to itself
        },
    )

    # Always start with the listener agent
    graph.set_entry_point("listener")

    # Set finish points
    graph.set_finish_point("listener")
    graph.set_finish_point("cbt_intervention")

    return graph.compile()


# Create a single compiled graph instance
# This is important - we should reuse the same graph instance
compiled_graph = create_cbt_graph()


# Chat function for interacting with the bot
def chat_with_cbt_bot(user_input: str, state: Dict = None) -> Dict:
    """Main function to interact with the CBT bot."""
    if state is None:
        state = get_default_state()

    # Add the user message and set the last_user_input flag to True
    state["messages"].append(HumanMessage(content=user_input))
    state["last_user_input"] = True

    # Use the global compiled graph instead of creating a new one each time
    # This is an important fix for state persistence
    result = compiled_graph.invoke(state)
    return result


if __name__ == "__main__":
    state = None
    print(
        "CBT Bot: Hello! I'm here to listen and help. What's been on your mind recently?"
    )

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["quit", "exit", "bye"]:
                break

            state = chat_with_cbt_bot(user_input, state)
            last_message = state["messages"][-1]
            print(f"CBT Bot: {last_message.content}")
            print(f"[DEBUG] Current phase: {state['phase']}")
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again.")
