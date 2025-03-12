# Deprecated
from typing import Dict, List
import json
from langchain_core.tools import Tool
from src.core.config import get_settings
from src.tools.mental_health_tools import analyze_emotion

settings = get_settings()


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


# Create tool instances for general medical
GENERAL_MEDICAL_TOOLS = [
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

# Create tool instances for emergency medical
EMERGENCY_MEDICAL_TOOLS = [
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
