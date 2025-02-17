from typing import Annotated, TypedDict, List, Dict, Any
from datetime import datetime
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import Tool

from src.core.config import get_settings
from src.core.llm import llm
from src.agents.mental_health_specialist import mental_health_specialist
from src.agents.general_medical import general_medical
from src.agents.emergency_medical import emergency_medical
from src.tools.mental_health_tools import analyze_emotion

settings = get_settings()


# Define state types
class EmiliaState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    current_agent: str
    emotional_state: Dict[str, Any]
    context: Dict[str, Any]
    therapeutic_insights: Dict[str, Any]


# Load content database
try:
    with open(settings.CONTENT_DB_PATH, "r", encoding="utf-8") as f:
        CONTENT_DB = json.load(f)
except FileNotFoundError:
    CONTENT_DB = {"content_categories": {"mindfulness": []}}


# Define tools
def get_content_recommendations(query: Dict) -> str:
    """Get personalized content recommendations based on emotional state and context."""
    try:
        # Extract information from the query
        emotional_state = query.get("emotional_state", {})
        context_tags = query.get("context_tags", [])

        # Initialize recommendations list
        all_recommendations = []

        # Map context tags to content categories
        category_mapping = {
            "academic": ["organization", "motivation"],
            "anxiety": ["anxiety_management", "mindfulness"],
            "crisis": ["crisis_resources"],
            "stress": ["mindfulness", "anxiety_management"],
            "motivation": ["motivation"],
            "general": ["mindfulness"],
        }

        # Collect relevant categories based on context
        relevant_categories = set()
        for tag in context_tags:
            if tag in category_mapping:
                relevant_categories.update(category_mapping[tag])

        # If no specific categories found, use general recommendations
        if not relevant_categories:
            relevant_categories.add("mindfulness")

        # Collect recommendations from relevant categories
        for category in relevant_categories:
            if category in CONTENT_DB["content_categories"]:
                category_content = CONTENT_DB["content_categories"][category]
                # Filter content based on emotional tags if available
                filtered_content = [
                    content
                    for content in category_content
                    if not emotional_state
                    or any(
                        tag in content["emotional_tags"]
                        for tag in [emotional_state, *context_tags]
                    )
                ]
                all_recommendations.extend(filtered_content)

        # Select top 2 most relevant recommendations
        selected_recs = (
            all_recommendations[:2]
            if all_recommendations
            else CONTENT_DB["content_categories"]["mindfulness"][:1]
        )

        # Format recommendations with complete information
        formatted_recs = [
            {
                "type": rec["type"],
                "title": rec["title"],
                "url": rec["url"],
                "duration": rec.get("duration", "5-10 minutos"),
                "creator": rec["creator"],
                "summary": rec["summary"],
                "tags": rec["keywords"],
            }
            for rec in selected_recs
        ]

        return json.dumps({"recommendations": formatted_recs})
    except Exception as e:
        # Fallback to a basic mindfulness exercise
        return json.dumps(
            {"recommendations": [CONTENT_DB["content_categories"]["mindfulness"][0]]}
        )


# Define specialized tools for each agent
def get_medical_info(query: str) -> str:
    """Get verified medical information from trusted sources."""
    # TODO: Implement medical database lookup
    return json.dumps({"info": "Medical information placeholder"})


def get_crisis_resources(location: str) -> str:
    """Get emergency medical resources and contacts for a given location."""
    # TODO: Implement emergency resources lookup
    return json.dumps(
        {
            "emergency": "911",
            "crisis_line": "1-800-273-8255",
            "nearest_hospital": "Local Hospital Info",
        }
    )


def get_wellness_plan(goals: List[str]) -> str:
    """Generate a personalized wellness plan based on goals."""
    # TODO: Implement wellness planning
    return json.dumps({"plan": "Customized wellness plan placeholder"})


# Add new specialized tools for education
def get_study_strategies(subject: str) -> str:
    """Get effective study strategies for specific subjects."""
    return json.dumps(
        {
            "strategies": [
                "Active recall techniques",
                "Spaced repetition",
                "Mind mapping",
                "Pomodoro technique",
                "Practice problems",
            ],
            "resources": ["Khan Academy", "Coursera", "Educational videos"],
        }
    )


def get_academic_plan(grades: Dict[str, str]) -> str:
    """Generate an academic improvement plan based on current grades."""
    return json.dumps(
        {
            "short_term": [
                "Review weak areas",
                "Set specific grade goals",
                "Create study schedule",
            ],
            "long_term": [
                "Build study habits",
                "Seek tutoring if needed",
                "Regular progress checks",
            ],
        }
    )


# Define agent nodes with their specialized tools
def wellness_advisor(state: EmiliaState) -> Dict:
    """Wellness and preventive health advice."""
    tools = [
        Tool(
            name="get_wellness_plan",
            description="Generate personalized wellness plans.",
            func=get_wellness_plan,
        ),
        Tool(
            name="get_recommendations",
            description="Get wellness content recommendations.",
            func=get_content_recommendations,
        ),
        Tool(
            name="analyze_emotion",
            description="Analyze emotional state for wellness context.",
            func=analyze_emotion,
        ),
    ]

    llm_with_wellness_tools = llm.bind_tools(tools)

    messages = [
        SystemMessage(
            content="""You are a wellness and preventive health advisor.
        - Focus on lifestyle and preventive measures
        - Provide evidence-based wellness recommendations
        - Create personalized wellness plans with get_wellness_plan
        - Offer practical health maintenance strategies
        - Support healthy habit formation
        - Maintain encouraging, motivational tone"""
        ),
        *state["messages"],
    ]
    response = llm_with_wellness_tools.invoke(messages)
    return {"messages": [response]}


def education_counselor(state: EmiliaState) -> Dict:
    """Educational support and academic guidance."""
    tools = [
        Tool(
            name="get_study_strategies",
            description="Get effective study strategies and resources for academic improvement.",
            func=get_study_strategies,
        ),
        Tool(
            name="get_academic_plan",
            description="Generate personalized academic improvement plans.",
            func=get_academic_plan,
        ),
        Tool(
            name="get_recommendations",
            description="Get educational content and motivation recommendations.",
            func=get_content_recommendations,
        ),
        Tool(
            name="analyze_emotion",
            description="Analyze emotional state in academic context.",
            func=analyze_emotion,
        ),
    ]

    llm_with_education_tools = llm.bind_tools(tools)

    messages = [
        SystemMessage(
            content="""You are an empathetic education counselor specialized in academic support.
        - Provide practical academic guidance and support
        - Help develop effective study strategies using get_study_strategies
        - Create personalized academic plans with get_academic_plan
        - Address academic stress and anxiety
        - Offer motivational support and resources
        - Maintain a supportive and encouraging tone
        - Recommend educational content when appropriate
        
        Remember to:
        - Acknowledge both academic and emotional challenges
        - Focus on actionable steps for improvement
        - Encourage seeking additional help when needed (tutoring, teacher consultation)
        - Consider both immediate and long-term academic goals"""
        ),
        *state["messages"],
    ]
    response = llm_with_education_tools.invoke(messages)
    return {"messages": [response]}


def medical_router(state: EmiliaState) -> Dict:
    """Routes to appropriate specialist based on query analysis."""
    if not state["messages"]:
        return {"current_agent": "general_medical"}

    last_message = state["messages"][-1]
    if not isinstance(last_message, HumanMessage):
        return {"current_agent": state.get("current_agent", "general_medical")}

    # Analyze the query for context
    analysis = analyze_emotion(last_message.content)
    analysis_dict = json.loads(analysis)

    # Initialize context if it doesn't exist
    if "context" not in state:
        state["context"] = {}

    # Update state
    state["context"].update(
        {
            "tags": analysis_dict.get("context_tags", []),
            "language": analysis_dict.get("language", "en"),
        }
    )

    # Route based on context
    context_tags = analysis_dict.get("context_tags", [])
    if "academic" in context_tags or "performance" in context_tags:
        return {"current_agent": "education_counselor"}
    elif any(tag in context_tags for tag in ["crisis", "emergency", "urgent"]):
        return {"current_agent": "emergency_medical"}
    elif any(tag in context_tags for tag in ["anxiety", "depression", "stress"]):
        return {"current_agent": "mental_health"}
    elif any(tag in context_tags for tag in ["wellness", "lifestyle", "prevention"]):
        return {"current_agent": "wellness_advisor"}
    else:
        return {"current_agent": "general_medical"}


def create_emilia_graph():
    # Initialize graph
    graph = StateGraph(EmiliaState)

    # Add all specialist nodes
    graph.add_node("router", medical_router)
    graph.add_node("general_medical", general_medical)
    graph.add_node("mental_health", mental_health_specialist)
    graph.add_node("emergency_medical", emergency_medical)
    graph.add_node("wellness_advisor", wellness_advisor)
    graph.add_node("education_counselor", education_counselor)

    # Define routing condition
    def route_to_agent(state):
        return [state["current_agent"]]

    # Add conditional edges from router
    graph.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "general_medical": "general_medical",
            "mental_health": "mental_health",
            "emergency_medical": "emergency_medical",
            "wellness_advisor": "wellness_advisor",
            "education_counselor": "education_counselor",
        },
    )

    # Set entry point
    graph.set_entry_point("router")

    return graph.compile()


# Update main chat function
def chat_with_emilia(user_input: str, state: Dict = None) -> Dict:
    if state is None:
        state = {
            "messages": [],
            "current_agent": "router",
            "emotional_state": {},
            "context": {"medical_tags": [], "language": "en"},
            "therapeutic_insights": {},
        }

    state["messages"].append(HumanMessage(content=user_input))
    graph = create_emilia_graph()
    return graph.invoke(state)


if __name__ == "__main__":
    state = None
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "salir"]:
            break

        state = chat_with_emilia(user_input, state)
        ai_message = state["messages"][-1].content
        print(f"Emilia: {ai_message}")

# Create the graph instance
graph = create_emilia_graph()
