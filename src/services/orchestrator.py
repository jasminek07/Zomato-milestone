import logging
from typing import Dict, Any

from src.api.schemas import UserPreferences, RecommendationResponse
from src.data.store import RestaurantStore
from src.services.validator import PreferenceValidator
from src.services.filter_service import FilterService, CandidateBuilder
from src.services.formatter import ResponseFormatter
from src.llm.client import get_llm_client

logger = logging.getLogger(__name__)

class RecommendationOrchestrator:
    def __init__(self, store: RestaurantStore):
        self.store = store
        self.validator = PreferenceValidator(store)
        self.filter_service = FilterService()
        self.llm_client = get_llm_client()

    def recommend(self, prefs: UserPreferences) -> RecommendationResponse:
        logger.info(f"Received recommendation request: {prefs}")
        
        # 1. Validate Preferences
        is_valid, errors, validated_prefs = self.validator.validate(prefs)
        if not is_valid:
            # Raise value error for now, Phase 6 will handle gracefully in API
            logger.error(f"Validation failed: {errors}")
            raise ValueError(f"Validation errors: {errors}")

        # 2. Filter Candidates
        all_restaurants = self.store.all()
        candidates, relaxation_flags = self.filter_service.filter_candidates(all_restaurants, validated_prefs)
        logger.info(f"Filtering yielded {len(candidates)} candidates.")

        # Prepare metadata fields
        filters_applied = ["location", "budget"]
        if validated_prefs.cuisine:
            filters_applied.append("cuisine")
        if validated_prefs.min_rating is not None:
            filters_applied.append("min_rating")
            
        filters_relaxed = []
        if relaxation_flags.get("cuisine_relaxed"):
            filters_relaxed.append("cuisine")
        if relaxation_flags.get("budget_relaxed"):
            filters_relaxed.append("budget")
            
        # Determine if LLM is actually being used
        # If client is DummyFallbackClient, it's False.
        llm_used = self.llm_client.__class__.__name__ == "GroqClient"

        # 3. Handle Zero Candidates
        if not candidates:
            logger.warning("No candidates found after filtering.")
            from src.api.schemas import ResponseMetadata
            meta = ResponseMetadata(
                candidates_considered=0,
                filters_applied=filters_applied,
                filters_relaxed=filters_relaxed,
                llm_used=False
            )
            return RecommendationResponse(
                summary="We couldn't find any restaurants matching your strict criteria.",
                recommendations=[],
                meta=meta
            )

        # 4. Build JSON Payload for LLM
        candidates_json = CandidateBuilder.build_candidates_json(candidates)

        # 5. Get LLM Ranking
        try:
            llm_response = self.llm_client.complete(validated_prefs, candidates_json)
        except Exception as e:
            logger.error(f"LLM Client encountered an unhandled error: {e}")
            raise

        # 6. Format Response
        return ResponseFormatter.format_response(
            llm_response=llm_response,
            candidates_used=candidates,
            filters_applied=filters_applied,
            filters_relaxed=filters_relaxed,
            llm_used=llm_used
        )
