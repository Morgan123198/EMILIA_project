from typing import Annotated, TypedDict, List, Dict, Any, Literal
from datetime import datetime
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import os
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import Tool

# Load environment variables
load_dotenv()


# Define state types
class EmiliaState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    current_agent: str
    emotional_state: Dict[str, Any]
    context: Dict[str, Any]
    therapeutic_insights: Dict[str, Any]


# Initialize LLM
llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="google/gemini-2.0-flash-001",
)


# Load content database
with open("src/data/content_database.json", "r", encoding="utf-8") as f:
    CONTENT_DB = json.load(f)


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


def analyze_emotion(text: str) -> str:
    """Analyze the emotional state and context from text."""
    try:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert at analyzing emotions and mental states.
                Analyze the emotional content of the text and output a JSON with:
                - valence: emotional positivity/negativity (-1 to 1)
                - arousal: emotional intensity/energy (-1 to 1)
                - dominant_emotion: primary emotion detected
                - context_tags: relevant context keywords from [anxiety, depression, stress, academic, 
                  performance, existential, identity, meaning, purpose, self-criticism, shame, trauma, grief, loneliness]
                - language: detected language code (en/es)""",
                ),
                ("user", "{text}"),
            ]
        )

        chain = prompt | llm | JsonOutputParser()
        result = chain.invoke({"text": text})
        return json.dumps(result)
    except Exception as e:
        return json.dumps(
            {
                "valence": 0.0,
                "arousal": 0.0,
                "dominant_emotion": "neutral",
                "context_tags": [],
                "language": "en",
            }
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


def get_mental_health_exercises(type: str) -> str:
    """Get specific mental health exercises and techniques."""
    # TODO: Implement exercises database
    return json.dumps(
        {
            "exercises": [
                "Breathing exercise",
                "Grounding technique",
                "Mindfulness practice",
            ]
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
def general_medical(state: EmiliaState) -> Dict:
    """General medical support and information."""
    tools = [
        Tool(
            name="get_medical_info",
            description="Get verified medical information about conditions, symptoms, and treatments.",
            func=get_medical_info,
        ),
        Tool(
            name="analyze_emotion",
            description="Analyze emotional state for medical context.",
            func=analyze_emotion,
        ),
    ]

    llm_with_medical_tools = llm.bind_tools(tools)

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


def mental_health_specialist(state: EmiliaState) -> Dict:
    """Mental health support and guidance."""
    tools = [
        Tool(
            name="get_mental_health_exercises",
            description="Get specific mental health exercises and coping techniques.",
            func=get_mental_health_exercises,
        ),
        Tool(
            name="get_recommendations",
            description="Get personalized content recommendations.",
            func=get_content_recommendations,
        ),
        Tool(
            name="analyze_emotion",
            description="Analyze emotional state for therapeutic context.",
            func=analyze_emotion,
        ),
    ]

    llm_with_mental_tools = llm.bind_tools(tools)

    # Get language from context
    language = state.get("context", {}).get("language", "en")

    messages = [
        SystemMessage(
            content="""You are an empathetic mental health specialist focused on therapeutic dialogue.
            
        Therapeutic Approach:
        1. Initial Assessment:
           - Begin with open-ended questions about their feelings and experiences
           - Use active listening techniques to understand their situation
           - Pay attention to emotional cues and underlying concerns
        
        2. Building Rapport:
           - Show genuine empathy and understanding
           - Validate their feelings and experiences
           - Create a safe space for open dialogue
        
        3. Therapeutic Process:
           - Ask follow-up questions to deepen understanding
           - Help identify patterns and triggers
           - Guide self-reflection through thoughtful questions
           - Suggest relevant coping strategies using get_mental_health_exercises
        
        4. Support and Resources:
           - Provide appropriate mental health resources
           - Teach practical coping techniques
           - Recommend content that supports their journey
        
        Communication Guidelines:
        - Always respond in the user's language (Spanish/English)
        - Use therapeutic questioning techniques
        - Practice reflective listening
        - Maintain professional boundaries while being warm
        - Ask for clarification when needed
        
        Remember:
        - Every response should include at least one thoughtful question
        - Focus on understanding before suggesting solutions
        - Create continuity between sessions by referencing previous insights
        - Recognize signs that require professional intervention"""
        ),
        *state["messages"],
    ]
    response = llm_with_mental_tools.invoke(messages)
    return {"messages": [response]}


def emergency_medical(state: EmiliaState) -> Dict:
    """Emergency medical triage and guidance."""
    tools = [
        Tool(
            name="get_crisis_resources",
            description="Get emergency medical resources and contacts.",
            func=get_crisis_resources,
        ),
        Tool(
            name="get_medical_info",
            description="Get critical medical information.",
            func=get_medical_info,
        ),
    ]

    llm_with_emergency_tools = llm.bind_tools(tools)

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


# Define agent nodes
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
