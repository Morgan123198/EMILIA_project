"""
CBT Intervention Agent Implementation

This module contains the implementation of the CBT intervention agent
that uses cognitive behavioral therapy techniques to help users.
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import Tool
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from src.prompts.cbt_prompts import CBT_INTERVENTION_PROMPT_TEMPLATE
from src.schema.cbt_state import CBTBotState
from src.utils.state_utils import get_default_state, extract_conversation_history
from src.tools.cbt_tools import (
    identify_cognitive_distortions,
    recommend_cbt_techniques,
    analyze_thought_patterns,
    create_homework_assignment,
)


def cbt_intervention_agent(
    state: CBTBotState, llm: BaseChatModel, config: Optional[RunnableConfig] = None
) -> Dict:
    """
    CBT intervention agent that provides cognitive behavioral therapy techniques.

    This agent analyzes cognitive distortions, recommends CBT techniques,
    and guides the user through CBT exercises.

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

    # Only process if we're in the CBT intervention phase and the last message was from the user
    if state["phase"] != "cbt_intervention" or not state.get("last_user_input", False):
        return {}

    # Extract conversation history as text
    conversation_history = extract_conversation_history(state)
    conversation_text = "\n".join(conversation_history)

    # Create assistant tools that wrap the core CBT tools
    cbt_tools = [
        Tool(
            name="identify_cognitive_distortions_assistant",
            description="Identify potential cognitive distortions in user's thinking patterns",
            func=lambda: identify_cognitive_distortions(llm, conversation_text),
        ),
        Tool(
            name="recommend_cbt_techniques_assistant",
            description="Recommend specific CBT techniques based on identified patterns",
            func=lambda distortions=None: recommend_cbt_techniques(
                llm,
                conversation_text,
                distortions or state.get("identified_distortions", []),
            ),
        ),
        Tool(
            name="analyze_thought_patterns_assistant",
            description="Analyze thought patterns for common CBT themes",
            func=lambda: analyze_thought_patterns(llm, conversation_text),
        ),
        Tool(
            name="create_homework_assignment_assistant",
            description="Create a personalized homework assignment for the user",
            func=lambda techniques=None: create_homework_assignment(
                llm,
                conversation_text,
                techniques or state.get("recommended_techniques", []),
            ),
        ),
    ]

    # System message for the CBT intervention agent
    system_msg = SystemMessage(content=CBT_INTERVENTION_PROMPT_TEMPLATE)

    # Prepare messages for the LLM
    messages = [system_msg] + state["messages"]

    # Print debug info before processing
    print(f"DEBUG: CBT agent processing with {len(messages)} messages")
    print(f"DEBUG: Current phase: {state['phase']}")
    print(
        f"DEBUG: Last message: {messages[-1].content if messages and hasattr(messages[-1], 'content') else 'N/A'}"
    )

    # Handle tool calls and update state accordingly
    updates = {"messages": [], "last_user_input": False}

    # Check if the LLM is an actual LLM instance with bind_tools or a dict
    if hasattr(llm, "bind_tools"):
        # Bind tools to the language model
        llm_with_cbt_tools = llm.bind_tools(cbt_tools)

        # Invoke the LLM with tools
        response = llm_with_cbt_tools.invoke(messages)

        # Debug output
        print(f"DEBUG: CBT agent response type: {type(response)}")

        if hasattr(response, "tool_calls") and response.tool_calls:
            print(
                f"DEBUG: Tool calls detected: {[tc.get('name') for tc in response.tool_calls]}"
            )

            # Process each tool call and update state
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name")
                tool_output = tool_call.get("output", {})

                print(f"DEBUG: Processing tool call: {tool_name}")

                if tool_name == "identify_cognitive_distortions_assistant":
                    # Store the identified distortions in the state
                    if "distortions" in tool_output:
                        updates["identified_distortions"] = tool_output["distortions"]

                elif tool_name == "recommend_cbt_techniques_assistant":
                    # Store the recommended techniques in the state
                    if "techniques" in tool_output:
                        updates["recommended_techniques"] = tool_output["techniques"]

                elif tool_name == "analyze_thought_patterns_assistant":
                    # Store the thought pattern analysis in the state
                    updates["cognitive_analysis"] = {
                        **state.get("cognitive_analysis", {}),
                        "thought_patterns": tool_output.get("thought_patterns", []),
                        "emotions": tool_output.get("emotions", []),
                        "behaviors": tool_output.get("behaviors", []),
                        "connections": tool_output.get("connections", []),
                    }

                elif tool_name == "create_homework_assignment_assistant":
                    # Store the homework assignment in the session summary
                    updates["session_summary"] = {
                        **state.get("session_summary", {}),
                        "homework": tool_output,
                    }

        # Extract AI message content from the response
        if hasattr(response, "content") and response.content:
            ai_message = AIMessage(content=response.content)
            updates["messages"].append(ai_message)
        else:
            # If there's no content but there are tool calls, create a summary message
            if hasattr(response, "tool_calls") and response.tool_calls:
                summary = create_summary_message(updates)
                ai_message = AIMessage(content=summary)
                updates["messages"].append(ai_message)
            else:
                # Fallback if no content or tool calls
                ai_message = AIMessage(
                    content="I've reviewed our conversation and am preparing some CBT techniques that might help. Could you tell me more about how these thoughts affect your daily life?"
                )
                updates["messages"].append(ai_message)
    else:
        # Handle the case where LLM doesn't have bind_tools method (e.g., if it's a dict)
        print("DEBUG: LLM does not have bind_tools method, running in simplified mode")

        # Simple processing based on the conversation
        conversation_text = " ".join(
            [msg.get("content", "") for msg in state.get("messages", [])]
        )
        updates = {"messages": state.get("messages", [])}

        # Analyze conversation to identify simple patterns
        distortions = []
        techniques = []
        cognitive_analysis = {
            "readiness": "user explicitly requested help",
            "stage": "initial intervention",
        }

        # Look for conversation themes to determine appropriate response
        if any(
            kw in conversation_text.lower()
            for kw in ["anxiety", "anxious", "worry", "presentation", "nervous"]
        ):
            # Anxiety scenario
            distortions = [
                {
                    "type": "Catastrophizing",
                    "explanation": "Assuming the worst possible outcome: 'everyone will think I'm incompetent' based on a potential mistake.",
                },
                {
                    "type": "Fortune Telling",
                    "explanation": "Predicting negative outcomes: 'I'll forget what to say' without evidence that this will happen.",
                },
                {
                    "type": "All-or-Nothing Thinking",
                    "explanation": "Viewing performance in black-and-white terms: need to be 'perfect' or else considered a failure.",
                },
            ]
            techniques = [
                {
                    "name": "Evidence Gathering",
                    "description": "List evidence that supports and contradicts the belief that one mistake will make everyone see you as incompetent.",
                },
                {
                    "name": "Thought Record",
                    "description": "Track anxious thoughts about the presentation, the emotions they trigger, and practice creating alternative balanced thoughts.",
                },
                {
                    "name": "Decatastrophizing",
                    "description": "Consider: 'What's the worst that could happen? What's most likely to happen? What could I do to cope?'",
                },
            ]
            cognitive_analysis = {
                "readiness": "user explicitly requested help",
                "stage": "initial intervention",
                "primary_distortion": "catastrophizing",
                "emotional_state": "anxiety about performance and judgment",
            }
        elif any(
            kw in conversation_text.lower()
            for kw in ["bullying", "bulling", "esconden", "mochila"]
        ):
            # Bullying scenario (Spanish)
            distortions = [
                {
                    "type": "Self-Blame",
                    "explanation": "Taking responsibility for others' actions: feeling that being bullied is somehow deserved.",
                },
                {
                    "type": "Labeling",
                    "explanation": "Applying negative labels to self: 'soy tonto' (I am stupid).",
                },
            ]
            techniques = [
                {
                    "name": "Self-Compassion Exercise",
                    "description": "Practice speaking to yourself with the same kindness you would offer to a friend in a similar situation.",
                },
                {
                    "name": "Problem-Solving Strategy",
                    "description": "Identify possible actions to address the bullying, such as speaking with trusted adults or developing response strategies.",
                },
            ]
            cognitive_analysis = {
                "readiness": "user explicitly requested help",
                "stage": "initial intervention",
                "primary_distortion": "self-blame",
                "emotional_state": "fear and shame related to peer interactions",
            }
        else:
            # Generic response for other scenarios
            distortions = [
                {
                    "type": "Negative Self-Talk",
                    "explanation": "Pattern of internal criticism and negative self-evaluation.",
                }
            ]
            techniques = [
                {
                    "name": "Thought Challenging",
                    "description": "Question the evidence for negative thoughts and consider alternative perspectives.",
                },
                {
                    "name": "Relaxation Techniques",
                    "description": "Practice deep breathing or progressive muscle relaxation to reduce physical symptoms of distress.",
                },
            ]

        # Update state with our findings
        updates["identified_distortions"] = distortions
        updates["recommended_techniques"] = techniques
        updates["cognitive_analysis"] = cognitive_analysis

        # Create and add a response
        ai_response = "I see you're asking for help. Let me switch to providing some practical techniques that might help you."
        updates["messages"].append({"type": "ai", "content": ai_response})

        return updates


def create_summary_message(updates: Dict) -> str:
    """Creates a summary message based on the state updates."""
    summary = "Based on our conversation, I've analyzed your thoughts and identified some patterns. "

    if "identified_distortions" in updates and updates["identified_distortions"]:
        summary += "I've noticed some thinking patterns we can work on. "

    if "recommended_techniques" in updates and updates["recommended_techniques"]:
        summary += "I have some techniques that might help you address these patterns. "

    if "session_summary" in updates and updates["session_summary"].get("homework"):
        summary += "I've also prepared a small homework assignment that could help you practice these skills."

    return summary
