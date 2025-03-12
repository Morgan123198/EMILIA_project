"""
CBT Graph Implementation

This module contains the implementation of the LangGraph for the CBT bot,
including routing logic and graph creation.
"""

from typing import Dict, Any, Callable
from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, StateGraph

from src.schema.cbt_state import CBTBotState
from src.agents.listener_agent import listener_agent
from src.agents.cbt_intervention_agent import cbt_intervention_agent
from src.utils.state_utils import get_default_state


def route_based_on_phase(state: CBTBotState) -> str:
    """
    Routes to the appropriate agent based on the current phase.

    This function decides which node in the graph should process the
    current state based on the phase and user input status.

    Args:
        state: Current conversation state

    Returns:
        str: Name of the next node or END
    """
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
    # This prevents infinite loops in the graph
    if not state.get("last_user_input", True):
        print("DEBUG: Ending processing cycle - last_user_input is False")
        return END

    # Route based on the current phase
    if "phase" in state and state["phase"] == "cbt_intervention":
        print("DEBUG: Routing to cbt_intervention phase")
        return "cbt_intervention"

    # Default route to listener
    print("DEBUG: Routing to listener phase")
    return "listener"


def create_cbt_agent_executors(llm: BaseChatModel) -> Dict[str, Callable]:
    """
    Create agent executors for the CBT graph nodes.

    This function creates wrapped agent functions that include the LLM
    in their execution context.

    Args:
        llm: Language model to use with the agents

    Returns:
        Dict[str, Callable]: Dictionary of agent executor functions
    """

    # Create listener agent executor
    def listener_executor(state, config=None):
        return listener_agent(state, llm, config)

    # Create CBT intervention agent executor
    def cbt_intervention_executor(state, config=None):
        return cbt_intervention_agent(state, llm, config)

    return {
        "listener": listener_executor,
        "cbt_intervention": cbt_intervention_executor,
    }


def create_cbt_graph(llm: BaseChatModel) -> StateGraph:
    """
    Create the CBT graph with appropriate nodes and edges.

    This function creates a LangGraph StateGraph with listener and CBT
    intervention nodes, connected according to the routing logic.

    Args:
        llm: Language model to use with the agents

    Returns:
        StateGraph: Configured graph ready for execution
    """
    # Initialize graph with the state type
    graph = StateGraph(CBTBotState)

    # Get the agent executors
    agents = create_cbt_agent_executors(llm)

    # Add nodes for each phase
    graph.add_node("listener", agents["listener"])
    graph.add_node("cbt_intervention", agents["cbt_intervention"])

    # Add conditional edges based on the current phase
    graph.add_conditional_edges(
        "listener",
        route_based_on_phase,
        {
            "listener": "listener",
            "cbt_intervention": "cbt_intervention",
            END: END,
        },
    )

    # Add conditional edges to route from CBT intervention
    graph.add_conditional_edges(
        "cbt_intervention",
        route_based_on_phase,
        {
            "listener": "listener",
            "cbt_intervention": "cbt_intervention",
            END: END,
        },
    )

    # Always start with the listener agent
    graph.set_entry_point("listener")

    # Both nodes can be finish points
    graph.set_finish_point("listener")
    graph.set_finish_point("cbt_intervention")

    return graph
