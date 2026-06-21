import json
from typing import List, Dict, Any
from src.api.schemas import UserPreferences
from src.data.models import LLMResponse, LLMRecommendation

class FallbackRanker:
    @staticmethod
    def rank(prefs: UserPreferences, candidates: List[Dict[str, Any]]) -> LLMResponse:
        """
        Rule-based fallback ranker used when the LLM is unavailable.
        Score = (0.5 × normalized_rating) + (0.3 × cuisine_match_bonus) + (0.2 × budget_exact_match)
        """
        scored_candidates = []
        for candidate in candidates:
            # Normalize rating (0 to 5 -> 0.0 to 1.0)
            rating = float(candidate.get("rating", 0.0))
            normalized_rating = rating / 5.0
            
            # Cuisine match bonus
            cuisine_match = 0.0
            if prefs.cuisine and prefs.cuisine.lower() in candidate.get("cuisine", "").lower():
                cuisine_match = 1.0
            elif not prefs.cuisine:
                # If user didn't specify cuisine, we don't penalize
                cuisine_match = 1.0
                
            # Budget match bonus
            budget_match = 0.0
            if prefs.budget and prefs.budget.lower() == candidate.get("budget_tier", "").lower():
                budget_match = 1.0
                
            score = (0.5 * normalized_rating) + (0.3 * cuisine_match) + (0.2 * budget_match)
            scored_candidates.append((score, candidate))
            
        # Sort by score descending, then by name
        scored_candidates.sort(key=lambda x: (-x[0], x[1].get("name", "")))
        
        # Take top N
        top_n = scored_candidates[:prefs.num_recommendations]
        
        recommendations = []
        for rank, (_, candidate) in enumerate(top_n, start=1):
            recommendations.append(LLMRecommendation(
                restaurant_id=str(candidate.get("id")),
                rank=rank,
                explanation="Recommended based on your location, budget, and rating preferences."
            ))
            
        return LLMResponse(
            summary="Here are our top recommended restaurants based on your preferences.",
            recommendations=recommendations
        )
