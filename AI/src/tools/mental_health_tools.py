# Deprecated
from typing import Dict, List
import json
from langchain_core.tools import Tool
from src.core.config import get_settings
from src.core.llm import llm

settings = get_settings()

# Load content database
try:
    with open(settings.CONTENT_DB_PATH, "r", encoding="utf-8") as f:
        CONTENT_DB = json.load(f)
except FileNotFoundError:
    CONTENT_DB = {"content_categories": {"mindfulness": []}}


def get_mental_health_exercises(type: str) -> str:
    """Get specific mental health exercises and coping techniques."""
    exercises = {
        "anxiety": [
            "Deep breathing exercises",
            "Progressive muscle relaxation",
            "Grounding techniques",
        ],
        "depression": [
            "Behavioral activation exercises",
            "Gratitude practices",
            "Mindful movement",
        ],
        "stress": [
            "Mindfulness meditation",
            "Stress journaling",
            "Time management techniques",
        ],
        "general": [
            "Basic mindfulness practice",
            "Self-compassion exercise",
            "Emotional awareness check-in",
        ],
    }

    selected_type = type.lower() if type.lower() in exercises else "general"
    return json.dumps(
        {
            "exercises": exercises[selected_type],
            "instructions": "Start with 5-10 minutes per exercise, gradually increasing duration as comfortable.",
        }
    )


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
            "anxiety": ["anxiety_management", "mindfulness"],
            "depression": ["mood_improvement", "motivation"],
            "stress": ["mindfulness", "anxiety_management"],
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

        # Format recommendations
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
        from langchain.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import JsonOutputParser

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


# Create tool instances
MENTAL_HEALTH_TOOLS = [
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
