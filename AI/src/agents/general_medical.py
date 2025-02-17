from typing import Dict, TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, SystemMessage
from src.tools.medical_tools import GENERAL_MEDICAL_TOOLS
from src.core.llm import llm
from langgraph.graph.message import add_messages


class EmiliaState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    current_agent: str
    emotional_state: Dict
    context: Dict
    therapeutic_insights: Dict


def general_medical(state: EmiliaState) -> Dict:
    """General medical support and information."""
    llm_with_medical_tools = llm.bind_tools(GENERAL_MEDICAL_TOOLS)

    # Get language from context
    language = state.get("context", {}).get("language", "en")

    messages = [
        SystemMessage(
            content="""You are a knowledgeable and empathetic healthcare assistant who adapts to the user's language.
        Core Responsibilities:
        - Start by asking open-ended questions to understand the user's situation better
        - Always respond in the same language as the user (Spanish or English)
        - Build rapport through active listening and follow-up questions
        - Show empathy and understanding before providing information
        - Use get_medical_info to verify any medical information you provide
        
        Conversation Flow:
        1. If this is the first interaction, ask general wellness questions
        2. Listen actively and ask relevant follow-up questions
        3. Show understanding of their situation
        4. Provide verified information when appropriate
        5. Check if they have additional concerns
        
        Remember:
        - Include appropriate medical disclaimers
        - Maintain professional but warm communication
        - Ask questions to gather more context
        - Never assume complete information from a short response"""
        ),
        *state["messages"],
    ]
    response = llm_with_medical_tools.invoke(messages)
    return {"messages": [response]}
