from typing import Dict, Any, Type
from ..agents.therapist_base import TherapistAgent
from ..agents.therapist_agents import (
    JungianTherapist,
    CBTTherapist,
    CompassionTherapist,
)


class TherapistSelector:
    def __init__(self):
        self.therapist_mapping = {
            # Emotional patterns that benefit from Jungian approach
            "existential": JungianTherapist,
            "identity": JungianTherapist,
            "meaning": JungianTherapist,
            "purpose": JungianTherapist,
            # Patterns that benefit from CBT
            "anxiety": CBTTherapist,
            "depression": CBTTherapist,
            "stress": CBTTherapist,
            "academic": CBTTherapist,
            "performance": CBTTherapist,
            # Patterns that benefit from Compassion-Focused Therapy
            "self-criticism": CompassionTherapist,
            "shame": CompassionTherapist,
            "trauma": CompassionTherapist,
            "grief": CompassionTherapist,
            "loneliness": CompassionTherapist,
        }

    def select_therapist(
        self, emotional_state: Dict[str, Any], context: Dict[str, Any]
    ) -> Type[TherapistAgent]:
        """Select the most appropriate therapist based on emotional state and context."""
        # Get all relevant tags
        tags = set(emotional_state.get("context_tags", []))
        emotion = emotional_state.get("dominant_emotion", "").lower()
        tags.add(emotion)

        # Count matches for each therapist type
        therapist_scores = {
            JungianTherapist: 0,
            CBTTherapist: 0,
            CompassionTherapist: 0,
        }

        # Score each tag
        for tag in tags:
            if tag in self.therapist_mapping:
                therapist_class = self.therapist_mapping[tag]
                therapist_scores[therapist_class] += 1

        # Consider emotional valence and arousal
        valence = emotional_state.get("valence", 0)
        arousal = emotional_state.get("arousal", 0)

        # Adjust scores based on emotional dimensions
        if valence < -0.5 and arousal > 0.5:  # High negative arousal -> CBT
            therapist_scores[CBTTherapist] += 1
        elif valence < -0.5 and arousal < -0.5:  # Low negative arousal -> Compassion
            therapist_scores[CompassionTherapist] += 1
        elif abs(valence) < 0.3:  # Neutral/questioning -> Jungian
            therapist_scores[JungianTherapist] += 1

        # Return the therapist with the highest score
        return max(therapist_scores.items(), key=lambda x: x[1])[0]
