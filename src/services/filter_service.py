from typing import List, Tuple, Dict, Any
from src.api.schemas import UserPreferences
from src.data.models import Restaurant
from src.config import CANDIDATE_CAP

class FilterService:
    def __init__(self, candidate_cap: int = CANDIDATE_CAP):
        self.candidate_cap = candidate_cap

    def filter_candidates(
        self, 
        restaurants: List[Restaurant], 
        prefs: UserPreferences
    ) -> Tuple[List[Restaurant], Dict[str, bool]]:
        """
        Filter restaurants based on user preferences with progressive relaxation.
        
        Args:
            restaurants: List of all restaurants from the store.
            prefs: UserPreferences schema object.
            
        Returns:
            Tuple of:
            - List[Restaurant]: Capped shortlist of restaurants.
            - Dict[str, bool]: Relaxation metadata flags:
              {'cuisine_relaxed': bool, 'budget_relaxed': bool}
        """
        # 1. Location is always a hard constraint
        loc_normalized = prefs.location.strip().lower()
        candidates = [
            r for r in restaurants 
            if r.location.strip().lower() == loc_normalized
        ]

        # 2. Minimum Rating is a hard constraint
        if prefs.min_rating is not None:
            candidates = [r for r in candidates if r.rating >= prefs.min_rating]

        # Save candidates before cuisine & budget filters to allow relaxation
        has_cuisine = bool(prefs.cuisine)
        cuisine_filtered = list(candidates)
        
        if has_cuisine:
            cuisine_normalized = prefs.cuisine.strip().lower()
            cuisine_filtered = [
                r for r in candidates
                if any(cuisine_normalized == c.strip().lower() for c in r.cuisines)
            ]

        # Strict budget filter
        strict_filtered = [r for r in cuisine_filtered if r.budget_tier == prefs.budget]

        # If strict matches are sufficient (>= 3), return them
        if len(strict_filtered) >= 3:
            return strict_filtered[:self.candidate_cap], {"cuisine_relaxed": False, "budget_relaxed": False}

        # Progressive Relaxation:
        # Case A: User specified both cuisine and budget, but we have < 3 matches
        if has_cuisine:
            # 1. Relax cuisine (keep budget)
            cuisine_relaxed = [r for r in candidates if r.budget_tier == prefs.budget]
            if len(cuisine_relaxed) >= 3:
                return cuisine_relaxed[:self.candidate_cap], {"cuisine_relaxed": True, "budget_relaxed": False}

            # 2. Relax budget (keep cuisine)
            budget_relaxed = cuisine_filtered
            if len(budget_relaxed) >= 3:
                return budget_relaxed[:self.candidate_cap], {"cuisine_relaxed": False, "budget_relaxed": True}

            # 3. Relax both
            return candidates[:self.candidate_cap], {"cuisine_relaxed": True, "budget_relaxed": True}
        
        # Case B: User did not specify cuisine (so we only had location, rating, budget)
        # Relax budget
        return candidates[:self.candidate_cap], {"cuisine_relaxed": False, "budget_relaxed": True}


class CandidateBuilder:
    @staticmethod
    def build_candidates_json(restaurants: List[Restaurant]) -> List[Dict[str, Any]]:
        """
        Convert Restaurant models to compact, LLM-ready dictionary representation.
        """
        return [
            {
                "id": r.id,
                "name": r.name,
                "cuisine": ", ".join(r.cuisines),
                "rating": r.rating,
                "cost": r.cost_for_two,
                "budget_tier": r.budget_tier
            }
            for r in restaurants
        ]
