import json
import logging
from typing import List, Dict, Any, Optional

from src.data.models import LLMResponse, LLMRecommendation
from src.api.schemas import UserPreferences

logger = logging.getLogger(__name__)

class ResponseParser:
    @staticmethod
    def parse_and_validate(content: str, candidates: List[Dict[str, Any]], client: Any) -> LLMResponse:
        """
        Parses LLM JSON output, validates it against candidates, and handles repairs.
        """
        parsed_data = ResponseParser._parse_json(content)
        
        # If parsing failed completely, we could attempt a repair request here.
        # For simplicity, if it's not a dict, we fallback.
        if not isinstance(parsed_data, dict):
            logger.warning("LLM response is not a valid JSON dictionary. Attempting repair.")
            parsed_data = ResponseParser._attempt_repair(content, client)
            if not isinstance(parsed_data, dict):
                raise ValueError("Failed to parse LLM response into JSON.")
                
        # Validate and clean up recommendations
        raw_recommendations = parsed_data.get("recommendations", [])
        if not isinstance(raw_recommendations, list):
            raw_recommendations = []
            
        candidate_ids = {str(c.get("id")) for c in candidates}
        candidate_map = {str(c.get("id")): c for c in candidates}
        
        valid_recommendations = []
        seen_ids: set = set()
        for rec in raw_recommendations:
            if not isinstance(rec, dict):
                continue
                
            rec_id = str(rec.get("restaurant_id"))
            # Reject hallucinations
            if rec_id not in candidate_ids:
                logger.warning(f"Hallucinated restaurant ID: {rec_id}. Discarding.")
                continue

            # Deduplicate: skip if this restaurant_id has already been added
            if rec_id in seen_ids:
                logger.warning(f"Duplicate restaurant_id: {rec_id}. Discarding repeated entry.")
                continue
            seen_ids.add(rec_id)
                
            try:
                rank = int(rec.get("rank", 0))
            except (ValueError, TypeError):
                rank = len(valid_recommendations) + 1
                
            explanation = rec.get("explanation", "Recommended based on your preferences.")
            if not explanation:
                explanation = "Recommended based on your preferences."
                
            # We don't merge full candidate metadata into LLMRecommendation here,
            # as LLMRecommendation only has id, rank, and explanation per schema.
            # The Formatter in Application Layer will merge with full data for display.
            
            valid_recommendations.append(LLMRecommendation(
                restaurant_id=rec_id,
                rank=rank,
                explanation=explanation
            ))
            
        # Re-rank to ensure contiguous ranks 1 to N
        valid_recommendations.sort(key=lambda r: r.rank)
        for i, rec in enumerate(valid_recommendations, start=1):
            rec.rank = i
            
        return LLMResponse(
            summary=parsed_data.get("summary"),
            recommendations=valid_recommendations[:5]  # ensure max 5
        )
        
    @staticmethod
    def _parse_json(content: str) -> Any:
        try:
            # Strip markdown fences if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None

    @staticmethod
    def _attempt_repair(bad_content: str, client: Any) -> Any:
        """
        Attempt to repair bad JSON by asking the LLM to fix it.
        """
        system_message = (
            "You are an expert JSON formatter. The user will provide a broken JSON string. "
            "Please fix it and return ONLY the valid JSON, matching the required schema."
        )
        
        if not hasattr(client, 'client') or not client.client:
            return None
            
        try:
            response = client.client.chat.completions.create(
                model=client.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": bad_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=800,
            )
            content = response.choices[0].message.content
            return ResponseParser._parse_json(content)
        except Exception as e:
            logger.error(f"Repair request failed: {e}")
            return None
