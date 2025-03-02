import json
from typing import Dict, List, Any
from src.core.llm import llm
from langchain_core.messages import SystemMessage, HumanMessage
from src.core.config import get_settings

settings = get_settings()

# Cognitive distortions from CBT literature
COGNITIVE_DISTORTIONS = {
    "all_or_nothing_thinking": {
        "name": "All-or-Nothing Thinking",
        "description": "Seeing things in black-and-white categories, with no middle ground.",
        "examples": [
            "If I don't get a perfect score, I'm a complete failure.",
            "Either I do this perfectly or not at all.",
        ],
    },
    "overgeneralization": {
        "name": "Overgeneralization",
        "description": "Taking a single negative event as a never-ending pattern of defeat.",
        "examples": ["I always mess things up.", "Nothing ever works out for me."],
    },
    "mental_filter": {
        "name": "Mental Filter",
        "description": "Focusing exclusively on negative details while ignoring positive aspects.",
        "examples": [
            "They pointed out one mistake, so the whole project was terrible.",
            "I only remember the times I failed, not my successes.",
        ],
    },
    "disqualifying_the_positive": {
        "name": "Disqualifying the Positive",
        "description": "Rejecting positive experiences by insisting they don't count.",
        "examples": [
            "I only got the job because they needed someone quickly.",
            "They're only complimenting me to be nice.",
        ],
    },
    "jumping_to_conclusions": {
        "name": "Jumping to Conclusions",
        "description": "Making negative interpretations without supporting facts.",
        "examples": [
            "They didn't text back, so they must be angry with me.",
            "I know they'll reject my idea before I even share it.",
        ],
    },
    "magnification_or_minimization": {
        "name": "Magnification/Minimization",
        "description": "Exaggerating negatives or minimizing positives.",
        "examples": [
            "This mistake will ruin everything.",
            "My accomplishments aren't really that important.",
        ],
    },
    "emotional_reasoning": {
        "name": "Emotional Reasoning",
        "description": "Assuming feelings reflect fact (I feel it, therefore it must be true).",
        "examples": [
            "I feel incompetent, so I must be incompetent.",
            "I feel guilty, so I must have done something wrong.",
        ],
    },
    "should_statements": {
        "name": "Should Statements",
        "description": "Rigid rules about how you or others should behave.",
        "examples": [
            "I should always be productive.",
            "People should always be considerate of my feelings.",
        ],
    },
    "labeling": {
        "name": "Labeling",
        "description": "Attaching a negative label to yourself or others instead of describing behavior.",
        "examples": ["I'm a failure.", "They're a terrible person."],
    },
    "personalization": {
        "name": "Personalization",
        "description": "Taking responsibility for events beyond your control.",
        "examples": [
            "It's my fault the group project failed.",
            "If I had been a better friend, they wouldn't be depressed.",
        ],
    },
}

# CBT techniques and exercises
CBT_TECHNIQUES = {
    "thought_record": {
        "name": "Thought Record",
        "description": "A structured way to identify and challenge negative thoughts.",
        "steps": [
            "Identify the situation that triggered negative feelings",
            "Note your emotions and their intensity (0-100%)",
            "Record your automatic thoughts in that moment",
            "Identify evidence that supports these thoughts",
            "Identify evidence that contradicts these thoughts",
            "Develop a balanced alternative thought",
            "Rate how you feel after considering the balanced view",
        ],
        "applicable_distortions": [
            "all_or_nothing_thinking",
            "overgeneralization",
            "mental_filter",
            "jumping_to_conclusions",
        ],
    },
    "behavioral_activation": {
        "name": "Behavioral Activation",
        "description": "Engaging in positive activities to improve mood and break cycles of inactivity.",
        "steps": [
            "Identify activities that typically bring you pleasure or a sense of accomplishment",
            "Schedule these activities into your week, starting with small, achievable goals",
            "Rate your mood before and after each activity",
            "Gradually increase activity level as motivation improves",
            "Notice and challenge thoughts that discourage activity",
        ],
        "applicable_distortions": [
            "emotional_reasoning",
            "magnification_or_minimization",
        ],
    },
    "cognitive_restructuring": {
        "name": "Cognitive Restructuring",
        "description": "Identifying and challenging irrational thoughts to develop more balanced thinking.",
        "steps": [
            "Notice when you experience a strong negative emotion",
            "Identify the thoughts behind this feeling",
            "Question if these thoughts are realistic or helpful",
            "Consider alternative interpretations",
            "Practice more balanced thinking",
        ],
        "applicable_distortions": [
            "all_or_nothing_thinking",
            "jumping_to_conclusions",
            "should_statements",
            "labeling",
        ],
    },
    "exposure_therapy": {
        "name": "Exposure Therapy",
        "description": "Gradually facing fears in a controlled way to reduce anxiety.",
        "steps": [
            "Create a hierarchy of feared situations, from least to most anxiety-provoking",
            "Start with the least anxiety-provoking situation",
            "Stay in the situation until anxiety reduces naturally",
            "Practice relaxation techniques during exposure",
            "Gradually move up the hierarchy as comfort increases",
        ],
        "applicable_distortions": ["catastrophizing", "emotional_reasoning"],
    },
    "mindfulness_practice": {
        "name": "Mindfulness Practice",
        "description": "Developing awareness of thoughts without judgment or attachment.",
        "steps": [
            "Set aside time for regular mindfulness practice",
            "Focus attention on present-moment experience",
            "Notice thoughts as they arise without judging them",
            "Gently return attention to the present when mind wanders",
            "Practice viewing thoughts as passing events, not facts",
        ],
        "applicable_distortions": [
            "emotional_reasoning",
            "magnification_or_minimization",
            "mental_filter",
        ],
    },
    "socratic_questioning": {
        "name": "Socratic Questioning",
        "description": "Using logical questioning to examine evidence for and against thoughts.",
        "steps": [
            "What evidence supports this thought?",
            "What evidence contradicts it?",
            "Are there alternative explanations?",
            "What's the worst that could happen? How likely is it?",
            "What would I tell a friend who had this thought?",
        ],
        "applicable_distortions": [
            "jumping_to_conclusions",
            "disqualifying_the_positive",
            "personalization",
        ],
    },
    "behavioral_experiment": {
        "name": "Behavioral Experiment",
        "description": "Testing beliefs through real-world experiences to gather evidence.",
        "steps": [
            "Identify a belief you want to test",
            "Design an experiment to test this belief",
            "Predict what will happen based on your current belief",
            "Carry out the experiment and record what actually happens",
            "Compare results with your prediction and adjust beliefs accordingly",
        ],
        "applicable_distortions": [
            "all_or_nothing_thinking",
            "overgeneralization",
            "jumping_to_conclusions",
        ],
    },
}


def identify_cognitive_distortions(input_data: str) -> str:
    """
    Identify potential cognitive distortions in a user's thinking patterns.

    Args:
        input_data: A JSON string containing conversation history or text to analyze

    Returns:
        A JSON string with identified cognitive distortions and examples
    """
    data = json.loads(input_data)
    text_to_analyze = data.get("text", "") or data.get("conversation_history", [""])

    if isinstance(text_to_analyze, list):
        text_to_analyze = " ".join(text_to_analyze)

    system_msg = SystemMessage(
        content=f"""You are a CBT expert trained to identify cognitive distortions in people's thinking.
        
        Here's a list of common cognitive distortions defined in CBT:
        {json.dumps(COGNITIVE_DISTORTIONS, indent=2)}
        
        Analyze the following text and identify any cognitive distortions present.
        For each identified distortion:
        1. Name the distortion
        2. Quote the specific text that demonstrates this pattern
        3. Explain why it fits this cognitive distortion
        4. Rate the confidence of this identification (1-5)
        
        Be thoughtful and nuanced in your analysis. Only identify distortions if they are clearly present.
        Return your response as JSON with an array of identified distortions.
        """
    )

    human_msg = HumanMessage(content=text_to_analyze)
    response = llm.invoke([system_msg, human_msg])

    # Extract JSON from the response
    try:
        # Try to find a JSON block in the response
        content = response.content
        start_idx = content.find("{")
        end_idx = content.rfind("}") + 1

        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            distortions = json.loads(json_str)
        else:
            # If no JSON block, try to parse the whole response
            distortions = json.loads(content)

        return json.dumps(distortions)
    except json.JSONDecodeError:
        # Fallback if we can't parse JSON
        return json.dumps(
            {
                "identified_distortions": [],
                "error": "Could not identify clear cognitive distortions in the text",
            }
        )


def recommend_cbt_techniques(input_data: str) -> str:
    """
    Recommend CBT techniques based on identified cognitive distortions.

    Args:
        input_data: A JSON string containing identified cognitive distortions

    Returns:
        A JSON string with recommended techniques and implementation steps
    """
    data = json.loads(input_data)
    distortions = data.get("identified_distortions", [])

    # Map distortion types to technique recommendations
    distortion_types = [d.get("type", "").lower() for d in distortions]

    system_msg = SystemMessage(
        content=f"""You are a CBT expert who recommends appropriate techniques based on identified cognitive distortions.
        
        Here are common CBT techniques and their applications:
        {json.dumps(CBT_TECHNIQUES, indent=2)}
        
        Based on the identified cognitive distortions, recommend suitable CBT techniques.
        For each recommendation:
        1. Name the technique
        2. Explain why it's appropriate for the identified distortions
        3. Provide clear, actionable steps for implementing the technique
        4. Give a specific example of how to apply it to the user's situation
        
        Return your response as JSON with an array of recommended techniques.
        """
    )

    human_msg = HumanMessage(
        content=json.dumps(
            {
                "identified_distortions": distortions,
                "distortion_types": distortion_types,
            }
        )
    )

    response = llm.invoke([system_msg, human_msg])

    # Extract JSON from the response
    try:
        # Try to find a JSON block in the response
        content = response.content
        start_idx = content.find("{")
        end_idx = content.rfind("}") + 1

        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            recommendations = json.loads(json_str)
        else:
            # If no JSON block, try to parse the whole response
            recommendations = json.loads(content)

        return json.dumps(recommendations)
    except json.JSONDecodeError:
        # Fallback for general CBT techniques
        return json.dumps(
            {
                "recommended_techniques": [
                    {
                        "name": "Thought Record",
                        "description": CBT_TECHNIQUES["thought_record"]["description"],
                        "steps": CBT_TECHNIQUES["thought_record"]["steps"],
                    },
                    {
                        "name": "Cognitive Restructuring",
                        "description": CBT_TECHNIQUES["cognitive_restructuring"][
                            "description"
                        ],
                        "steps": CBT_TECHNIQUES["cognitive_restructuring"]["steps"],
                    },
                ],
                "note": "These are general CBT techniques that can be helpful in most situations.",
            }
        )


def analyze_thought_patterns(input_data: str) -> str:
    """
    Analyze general thought patterns in a conversation for CBT-relevant themes.

    Args:
        input_data: A JSON string containing conversation history

    Returns:
        A JSON string with analyzed themes and patterns
    """
    data = json.loads(input_data)
    conversation_history = data.get("conversation_history", [])

    if not conversation_history:
        return json.dumps(
            {"themes": [], "patterns": [], "error": "No conversation history provided"}
        )

    # Join conversation messages
    if isinstance(conversation_history, list):
        conversation_text = " ".join(conversation_history)
    else:
        conversation_text = conversation_history

    system_msg = SystemMessage(
        content="""You are a CBT expert analyzing conversation patterns for CBT-relevant themes.
        
        Look for the following in the conversation:
        1. Recurring emotional themes (anxiety, depression, frustration, etc.)
        2. Situations that trigger negative emotions
        3. Beliefs about self, others, and the world
        4. Behavioral patterns mentioned
        5. Goals or values expressed
        6. Strengths and resources the person has
        
        Provide a thoughtful analysis that captures the core patterns without making assumptions.
        Return your analysis as JSON with clear, organized sections.
        """
    )

    human_msg = HumanMessage(content=conversation_text)
    response = llm.invoke([system_msg, human_msg])

    # Extract JSON from the response
    try:
        # Try to find a JSON block in the response
        content = response.content
        start_idx = content.find("{")
        end_idx = content.rfind("}") + 1

        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            analysis = json.loads(json_str)
        else:
            # If no JSON block, try to parse the whole response
            analysis = json.loads(content)

        return json.dumps(analysis)
    except json.JSONDecodeError:
        # Create a structured fallback response
        return json.dumps(
            {
                "themes": ["Unable to identify specific themes"],
                "patterns": ["Analysis requires more conversation context"],
                "next_steps": "Continue the conversation to gather more information",
            }
        )
