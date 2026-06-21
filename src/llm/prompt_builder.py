import json
from typing import List, Dict, Any
from src.api.schemas import UserPreferences

class PromptAssembler:
    @staticmethod
    def assemble_prompt(prefs: UserPreferences, candidates: List[Dict[str, Any]]) -> str:
        """
        Merge user preferences and preprocessed candidate JSON lists into a unified prompt context.
        """
        candidates_str = json.dumps(candidates, indent=2, ensure_ascii=False)
        cuisine_str = prefs.cuisine if prefs.cuisine else "any"
        min_rating_str = str(prefs.min_rating) if prefs.min_rating is not None else "none"
        additional_str = prefs.additional if prefs.additional else "none"

        return f"""User Preferences:
- Location: {prefs.location}
- Budget: {prefs.budget}
- Cuisine: {cuisine_str}
- Minimum Rating: {min_rating_str}
- Number of Recommendations: {prefs.num_recommendations}
- Additional: {additional_str}

Candidates:
{candidates_str}

Return JSON:
{{
  "summary": "<1-2 sentence overview of recommendations>",
  "recommendations": [
    {{
      "restaurant_id": "<id from candidates>",
      "rank": 1,
      "explanation": "<why this restaurant fits>"
    }}
  ]
}}
"""
