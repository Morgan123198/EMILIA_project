from typing import Dict, Any, List
from abc import ABC, abstractmethod
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI


class TherapistAgent(ABC):
    """Base class for therapist agents with different therapeutic approaches."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.name = self.get_name()
        self.approach = self.get_approach()
        self.specialties = self.get_specialties()

    @abstractmethod
    def get_name(self) -> str:
        """Return the name of the therapist."""
        pass

    @abstractmethod
    def get_approach(self) -> str:
        """Return the therapeutic approach."""
        pass

    @abstractmethod
    def get_specialties(self) -> List[str]:
        """Return the therapist's specialties."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this therapist."""
        pass

    def analyze_case(
        self,
        emotional_state: Dict[str, Any],
        context: Dict[str, Any],
        message_history: List[Dict],
    ) -> Dict[str, Any]:
        """Analyze the case and provide therapeutic insights."""
        system_prompt = self.get_system_prompt()

        # Format the case information
        case_info = f"""
        Emotional State Analysis:
        - Valence: {emotional_state.get('valence')}
        - Arousal: {emotional_state.get('arousal')}
        - Dominant Emotion: {emotional_state.get('dominant_emotion')}
        - Context Tags: {', '.join(emotional_state.get('context_tags', []))}
        
        Recent Conversation History:
        {self._format_history(message_history)}
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=case_info),
        ]

        response = self.llm.invoke(messages)
        return {
            "therapist": self.name,
            "approach": self.approach,
            "analysis": response.content,
            "recommendations": self._extract_recommendations(response.content),
        }

    def _format_history(self, history: List[Dict]) -> str:
        """Format conversation history for analysis."""
        formatted = []
        for msg in history[-3:]:  # Last 3 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role.capitalize()}: {content}")
        return "\n".join(formatted)

    def _extract_recommendations(self, analysis: str) -> List[str]:
        """Extract specific recommendations from the analysis."""
        # This could be enhanced with better parsing
        recommendations = []
        for line in analysis.split("\n"):
            if any(
                keyword in line.lower()
                for keyword in ["recommend", "suggest", "try", "consider"]
            ):
                recommendations.append(line.strip())
        return recommendations
