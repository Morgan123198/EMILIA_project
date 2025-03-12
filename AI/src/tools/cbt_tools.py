"""
CBT Tools

This module contains tools for cognitive behavioral therapy, implementing
techniques from clinical CBT practices.
"""

import json
from typing import Dict, List, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser

from src.utils.state_utils import extract_conversation_history


# Model for cognitive distortion analysis output
class DistortionAnalysis(BaseModel):
    distortions: List[Dict[str, Any]] = Field(
        description="List of identified cognitive distortions"
    )
    summary: str = Field(description="Summary of the overall thought patterns")


# Model for CBT technique recommendations
class TechniqueRecommendation(BaseModel):
    techniques: List[Dict[str, Any]] = Field(
        description="List of recommended CBT techniques"
    )
    rationale: str = Field(
        description="Explanation of why these techniques were chosen"
    )
    priority: List[str] = Field(
        description="Ordered list of technique names by priority"
    )


# Model for thought pattern analysis
class ThoughtPatternAnalysis(BaseModel):
    thought_patterns: List[Dict[str, Any]] = Field(
        description="Identified thought patterns"
    )
    emotions: List[Dict[str, Any]] = Field(description="Associated emotions")
    behaviors: List[Dict[str, Any]] = Field(description="Associated behaviors")
    connections: List[Dict[str, Any]] = Field(
        description="Connections between thoughts, emotions, and behaviors"
    )


# CBT tool implementations
def identify_cognitive_distortions(llm: BaseChatModel, text: str) -> Dict[str, Any]:
    """
    Identify cognitive distortions in the provided text using CBT principles.

    This function uses a specialized prompt based on clinical CBT resources to
    identify specific cognitive distortions present in the text.

    Args:
        llm: Language model to use for analysis
        text: Text to analyze (typically conversation history)

    Returns:
        Dict: Analysis of cognitive distortions
    """
    # Create a parser for structured output
    parser = JsonOutputParser(pydantic_object=DistortionAnalysis)

    # Create a prompt with comprehensive cognitive distortion definitions
    prompt = PromptTemplate.from_template(
        """You are a CBT specialist trained to identify cognitive distortions in text.
        
        Here are the common cognitive distortions from CBT practice:
        
        1. All-or-Nothing Thinking: Seeing things in black and white categories. If your performance falls short of perfect, you see yourself as a total failure.
           Example: "I made a mistake on that report, so I'm completely incompetent."
        
        2. Overgeneralization: Viewing a negative event as a never-ending pattern of defeat.
           Example: "I got rejected for this job, I'll never find employment."
        
        3. Mental Filter: Picking out a single negative detail and dwelling on it exclusively.
           Example: "I received mostly positive feedback, but my boss mentioned one small area for improvement, so I'm failing."
        
        4. Disqualifying the Positive: Rejecting positive experiences by insisting they "don't count."
           Example: "People said they liked my presentation, but they were just being nice."
        
        5. Jumping to Conclusions: Making negative interpretations without definite facts. This includes:
           - Mind Reading: Assuming you know what people are thinking
           - Fortune Telling: Predicting things will turn out badly
           Example: "They didn't smile at me, so they must hate me."
        
        6. Magnification or Minimization: Exaggerating the importance of problems and shortcomings, or minimizing strengths.
           Example: "My mistake was catastrophic" or "My accomplishment wasn't a big deal."
        
        7. Emotional Reasoning: Assuming your negative emotions reflect reality.
           Example: "I feel like a failure, so I must be one."
        
        8. Should Statements: Using "should," "must," or "ought" statements that set up unrealistic expectations.
           Example: "I should never feel tired" or "I must always please everyone."
        
        9. Labeling: Attaching global labels to yourself or others instead of describing specific behaviors.
           Example: "I'm a loser" instead of "I didn't do well in this situation."
        
        10. Personalization and Blame: Taking responsibility for events outside your control, or blaming others for your own actions.
            Example: "It's my fault my friend is unhappy" or "I failed because my teacher didn't explain it well."
            
        Analyze the following text and identify any cognitive distortions present:
        
        {text}
        
        For each distortion you identify:
        1. Specify the exact type of distortion
        2. Quote the specific text showing this distortion
        3. Explain why it qualifies as this type of distortion
        4. Rate the severity (1-5, where 5 is most severe)
        
        Also provide an overall summary of the thought patterns.
        
        {format_instructions}
        """
    ).partial(format_instructions=parser.get_format_instructions())

    # Process the text through the LLM
    chain = prompt | llm | parser
    result = chain.invoke({"text": text})

    return result.dict()


def recommend_cbt_techniques(
    llm: BaseChatModel, text: str, distortions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Recommend appropriate CBT techniques based on identified cognitive distortions.

    This function matches effective CBT techniques to the specific cognitive distortions
    identified in the conversation.

    Args:
        llm: Language model to use
        text: Conversation text
        distortions: List of identified cognitive distortions

    Returns:
        Dict: Recommended techniques and rationale
    """
    # Create a parser for structured output
    parser = JsonOutputParser(pydantic_object=TechniqueRecommendation)

    # Format the distortions for inclusion in the prompt
    distortions_json = json.dumps(distortions, indent=2)

    # Create a prompt with CBT technique descriptions
    prompt = PromptTemplate.from_template(
        """You are a CBT specialist recommending appropriate techniques based on identified cognitive distortions.
        
        Here are effective CBT techniques:
        
        1. Thought Records: Systematically examining and challenging negative thoughts.
           Steps: Identify situation, identify automatic thought, identify emotions, identify evidence for and against thought, develop balanced alternative thought, rate new emotion.
           
        2. Behavioral Activation: Increasing engagement in activities that provide positive reinforcement.
           Steps: Identify valued activities, schedule activities, monitor mood before and after, gradually increase difficulty.
           
        3. Exposure Therapy: Gradually facing feared situations to reduce anxiety.
           Steps: Create anxiety hierarchy, begin with least anxiety-provoking situation, practice until anxiety decreases, move to next item.
           
        4. Cognitive Restructuring: Identifying and modifying unhelpful thoughts and beliefs.
           Steps: Identify automatic thoughts, evaluate evidence, generate alternative explanations, practice realistic thinking.
           
        5. Behavioral Experiments: Testing beliefs through real-world experiments.
           Steps: Identify belief to test, design experiment, predict outcome, conduct experiment, evaluate results.
           
        6. Problem-Solving: Systematic approach to addressing practical problems.
           Steps: Define problem, generate solutions, evaluate options, implement solution, review outcome.
           
        7. Mindfulness: Developing non-judgmental awareness of present moment experiences.
           Steps: Practice focused attention, observe thoughts without judgment, return to present when mind wanders.
           
        8. Relaxation Training: Techniques to reduce physical tension.
           Steps: Progressive muscle relaxation, deep breathing, visualization, body scan.
           
        9. Self-Monitoring: Tracking thoughts, emotions, behaviors to identify patterns.
           Steps: Record situation, thoughts, emotions, behaviors, identify triggers and patterns.
           
        10. Activity Scheduling: Planning activities to improve mood and build mastery.
            Steps: Schedule activities, rate expected pleasure/mastery, complete activities, rate actual pleasure/mastery.
            
        11. Socratic Questioning: Using questions to examine evidence and logic behind thoughts.
            Steps: What evidence supports this thought? Is there evidence against it? Are there alternative explanations?
            
        12. The ABCD Method: Analyzing Activating events, Beliefs, Consequences, and Disputing unhelpful beliefs.
            Steps: Identify triggering event, identify belief about event, identify consequences, dispute irrational beliefs.
            
        The user has shared the following conversation:
        
        {text}
        
        These cognitive distortions have been identified:
        
        {distortions}
        
        Based on this information, recommend appropriate CBT techniques.
        For each technique:
        1. Name the technique
        2. Explain why it's appropriate for this situation
        3. Provide specific steps tailored to the user's situation
        4. Suggest how to introduce it to the user
        
        Order the techniques by priority for this situation.
        
        {format_instructions}
        """
    ).partial(format_instructions=parser.get_format_instructions())

    # Process through the LLM
    chain = prompt | llm | parser
    result = chain.invoke({"text": text, "distortions": distortions_json})

    return result.dict()


def analyze_thought_patterns(llm: BaseChatModel, text: str) -> Dict[str, Any]:
    """
    Analyze thought patterns and their connection to emotions and behaviors.

    This function examines the cognitive-behavioral connections in the user's
    conversation, identifying core thought patterns and their impact.

    Args:
        llm: Language model to use
        text: Conversation text to analyze

    Returns:
        Dict: Analysis of thought patterns, emotions, behaviors, and their connections
    """
    # Create a parser for structured output
    parser = JsonOutputParser(pydantic_object=ThoughtPatternAnalysis)

    # Create a prompt for thought pattern analysis
    prompt = PromptTemplate.from_template(
        """You are a CBT specialist analyzing the connections between thoughts, emotions, and behaviors.
        
        In CBT, we understand that:
        - Thoughts influence emotions and behaviors
        - Emotions influence thoughts and behaviors
        - Behaviors influence thoughts and emotions
        
        Analyze the following conversation to identify:
        
        {text}
        
        In your analysis:
        1. Identify recurring thought patterns (what the person believes about themselves, others, and their situation)
        2. Identify emotional responses and their intensity
        3. Identify behavioral patterns (what the person does or avoids doing)
        4. Analyze how these elements connect and reinforce each other
        
        Be specific and reference exact examples from the text.
        
        {format_instructions}
        """
    ).partial(format_instructions=parser.get_format_instructions())

    # Process through the LLM
    chain = prompt | llm | parser
    result = chain.invoke({"text": text})

    return result.dict()


def create_homework_assignment(
    llm: BaseChatModel, text: str, techniques: List[Dict[str, Any]]
) -> str:
    """
    Create a personalized homework assignment based on recommended techniques.

    This function develops appropriate practice exercises for the user to
    implement between sessions, based on their specific situation.

    Args:
        llm: Language model to use
        text: Conversation text
        techniques: List of recommended techniques

    Returns:
        str: Personalized homework assignment
    """
    # Format the techniques for inclusion in the prompt
    techniques_json = json.dumps(techniques, indent=2)

    # Create a prompt for homework assignment creation
    prompt = PromptTemplate.from_template(
        """You are a CBT specialist creating a personalized homework assignment.
        
        The user has shared the following conversation:
        
        {text}
        
        You've recommended these techniques:
        
        {techniques}
        
        Create a specific, achievable homework assignment that:
        1. Focuses on one or two priority techniques
        2. Gives clear instructions that the user can follow independently
        3. Is appropriate for a beginner to CBT
        4. Can be completed within the next week
        5. Will provide a foundation for further work
        
        Format your response as a direct message to the user, explaining:
        - What you're asking them to do
        - Why this assignment will help
        - How to record their progress
        - What to pay attention to while doing the assignment
        
        Keep the tone supportive and collaborative.
        """
    )

    # Process through the LLM
    result = llm.invoke(prompt.format(text=text, techniques=techniques_json))

    return result.content
