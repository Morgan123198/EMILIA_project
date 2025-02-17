from typing import Dict, TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, SystemMessage
from src.tools.medical_tools import EMERGENCY_MEDICAL_TOOLS
from src.core.llm import llm
from langgraph.graph.message import add_messages


class EmiliaState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    current_agent: str
    emotional_state: Dict
    context: Dict
    therapeutic_insights: Dict


def emergency_medical(state: EmiliaState) -> Dict:
    """Emergency medical triage and guidance."""
    llm_with_emergency_tools = llm.bind_tools(EMERGENCY_MEDICAL_TOOLS)

    messages = [
        SystemMessage(
            content="""You are an emergency medical triage specialist.
        - Assess urgency of medical situations
        - Provide clear emergency instructions
        - ALWAYS recommend emergency services for serious conditions
        - Use get_crisis_resources to provide immediate help
        - Give first-aid guidance when appropriate
        - Maintain calm, clear communication"""
        ),
        *state["messages"],
    ]
    response = llm_with_emergency_tools.invoke(messages)
    return {"messages": [response]}
