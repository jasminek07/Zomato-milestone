from typing import List, Dict, Any
from src.data.models import LLMResponse, Restaurant
from src.api.schemas import RecommendationDisplay, RecommendationResponse, ResponseMetadata

class ResponseFormatter:
    @staticmethod
    def format_response(
        llm_response: LLMResponse,
        candidates_used: List[Restaurant],
        filters_applied: List[str],
        filters_relaxed: List[str],
        llm_used: bool
    ) -> RecommendationResponse:
        """
        Convert internal LLMResponse and metadata into a final API RecommendationResponse.
        """
        # Create quick lookup
        candidate_map = {r.id: r for r in candidates_used}
        
        display_recs = []
        for rec in llm_response.recommendations:
            restaurant = candidate_map.get(rec.restaurant_id)
            if not restaurant:
                continue # Should be filtered out by ResponseParser already
                
            cost_str = f"₹{int(restaurant.cost_for_two)} for two" if restaurant.cost_for_two else "Not available"
            cuisine_str = ", ".join(restaurant.cuisines) if restaurant.cuisines else "Various"
            
            display_recs.append(RecommendationDisplay(
                rank=rec.rank,
                restaurant_name=restaurant.name,
                cuisine=cuisine_str,
                rating=restaurant.rating,
                estimated_cost=cost_str,
                explanation=rec.explanation
            ))
            
        # Fallback summary if missing
        summary = llm_response.summary or "Here are your recommended restaurants."
        
        meta = ResponseMetadata(
            candidates_considered=len(candidates_used),
            filters_applied=filters_applied,
            filters_relaxed=filters_relaxed,
            llm_used=llm_used
        )
        
        return RecommendationResponse(
            summary=summary,
            recommendations=display_recs,
            meta=meta
        )
