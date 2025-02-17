import json
from typing import Dict, List, Optional
from pathlib import Path
import jsonschema


class ContentManager:
    def __init__(
        self,
        content_path: str = "data/content_database.json",
        schema_path: str = "data/content_schema.json",
    ):
        self.content_path = Path(content_path)
        self.schema_path = Path(schema_path)
        self.content_db = self._load_content()
        self.schema = self._load_schema()
        self._validate_content()

    def _load_schema(self) -> Dict:
        """Load and return the JSON schema"""
        with open(self.schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_content(self) -> Dict:
        """Load and return the content database"""
        with open(self.content_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _validate_content(self):
        """Validate the content database against the schema"""
        jsonschema.validate(instance=self.content_db, schema=self.schema)

    def get_content_by_emotion(self, emotion: str, limit: int = 3) -> List[Dict]:
        """Retrieve content based on emotional tags"""
        matching_content = []
        for category in self.content_db["content_categories"].values():
            for item in category:
                if emotion in item["emotional_tags"]:
                    matching_content.append(item)
        return matching_content[:limit]

    def get_content_by_context(self, context: str, limit: int = 3) -> List[Dict]:
        """Retrieve content based on context"""
        matching_content = []
        for category in self.content_db["content_categories"].values():
            for item in category:
                if context in item["recommended_context"]:
                    matching_content.append(item)
        return matching_content[:limit]

    def get_content_by_category(self, category: str, limit: int = 3) -> List[Dict]:
        """Retrieve content from a specific category"""
        return self.content_db["content_categories"].get(category, [])[:limit]

    def recommend_content(
        self,
        emotional_state: Dict,
        context: Optional[str] = None,
        content_type: Optional[str] = None,
        limit: int = 3,
    ) -> List[Dict]:
        """
        Recommend content based on multiple criteria

        Args:
            emotional_state: Dict containing valence and arousal values
            context: Optional context (e.g., "academic", "personal")
            content_type: Optional content type filter
            limit: Maximum number of recommendations
        """
        # Convert emotional state to tags
        emotional_tags = self._emotional_state_to_tags(emotional_state)

        matching_content = []
        for category in self.content_db["content_categories"].values():
            for item in category:
                score = 0
                # Match emotional tags
                if any(tag in item["emotional_tags"] for tag in emotional_tags):
                    score += 1
                # Match context if provided
                if context and context in item["recommended_context"]:
                    score += 1
                # Match content type if provided
                if content_type and item["type"] == content_type:
                    score += 1

                if score > 0:
                    matching_content.append((score, item))

        # Sort by score and return top matches
        matching_content.sort(key=lambda x: x[0], reverse=True)
        return [item for score, item in matching_content[:limit]]

    def _emotional_state_to_tags(self, emotional_state: Dict) -> List[str]:
        """Convert emotional state values to emotional tags"""
        tags = []
        valence = emotional_state.get("valence", 0)
        arousal = emotional_state.get("arousal", 0)

        # Valence based tags
        if valence < -0.3:
            tags.extend(["depression", "anxiety"])
        elif valence > 0.3:
            tags.append("motivation")

        # Arousal based tags
        if arousal > 0.3:
            tags.append("stress")
        elif arousal < -0.3:
            tags.append("calm")

        return tags

    def format_recommendation(self, content: Dict) -> str:
        """Format a content item for presentation"""
        return f"""
Title: {content['title']}
Type: {content['type'].capitalize()}
{f"Duration: {content['duration']}" if 'duration' in content else ''}
{f"URL: {content['url']}" if 'url' in content else ''}

Summary: {content['summary']}
"""
