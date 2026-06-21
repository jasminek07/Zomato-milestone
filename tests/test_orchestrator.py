import pytest
from unittest.mock import MagicMock, patch

from src.api.schemas import UserPreferences
from src.services.orchestrator import RecommendationOrchestrator
from src.data.models import LLMResponse, LLMRecommendation, Restaurant

@pytest.fixture
def mock_store():
    store = MagicMock()
    # Assume validation passes
    store.get_locations.return_value = ["Delhi"]
    store.get_cuisines.return_value = ["Italian"]
    store.all.return_value = []
    return store

def test_recommend_success(mock_store):
    prefs = UserPreferences(location="Delhi", budget="medium")
    
    # Mock validator
    mock_validator = MagicMock()
    mock_validator.validate.return_value = (True, {}, prefs)
    
    # Mock FilterService
    mock_filter = MagicMock()
    mock_restaurant = Restaurant(
        id="123",
        name="Test Rest",
        location="Delhi",
        cuisines=["Italian"],
        rating=4.5,
        budget_tier="medium",
        cost_for_two=1000
    )
    mock_filter.filter_candidates.return_value = ([mock_restaurant], {"cuisine_relaxed": False, "budget_relaxed": False})
    
    # Mock LLM Client
    mock_llm = MagicMock()
    mock_llm.__class__.__name__ = "GroqClient"
    llm_resp = LLMResponse(
        summary="Here is 1 test restaurant.",
        recommendations=[
            LLMRecommendation(restaurant_id="123", rank=1, explanation="Good test")
        ]
    )
    mock_llm.complete.return_value = llm_resp
    
    with patch("src.services.orchestrator.PreferenceValidator", return_value=mock_validator), \
         patch("src.services.orchestrator.FilterService", return_value=mock_filter), \
         patch("src.services.orchestrator.get_llm_client", return_value=mock_llm):
        
        orchestrator = RecommendationOrchestrator(mock_store)
        response = orchestrator.recommend(prefs)
        
        assert response.summary == "Here is 1 test restaurant."
        assert len(response.recommendations) == 1
        assert response.recommendations[0].restaurant_name == "Test Rest"
        assert response.recommendations[0].estimated_cost == "₹1000 for two"
        assert response.meta.candidates_considered == 1
        assert response.meta.llm_used is True

def test_recommend_zero_candidates(mock_store):
    prefs = UserPreferences(location="Delhi", budget="medium")
    
    # Mock validator
    mock_validator = MagicMock()
    mock_validator.validate.return_value = (True, {}, prefs)
    
    # Mock FilterService to return empty list
    mock_filter = MagicMock()
    mock_filter.filter_candidates.return_value = ([], {"cuisine_relaxed": False, "budget_relaxed": False})
    
    mock_llm = MagicMock()
    
    with patch("src.services.orchestrator.PreferenceValidator", return_value=mock_validator), \
         patch("src.services.orchestrator.FilterService", return_value=mock_filter), \
         patch("src.services.orchestrator.get_llm_client", return_value=mock_llm):
        
        orchestrator = RecommendationOrchestrator(mock_store)
        response = orchestrator.recommend(prefs)
        
        # LLM should not be called
        mock_llm.complete.assert_not_called()
        
        assert len(response.recommendations) == 0
        assert "couldn't find any restaurants" in response.summary.lower()
        assert response.meta.candidates_considered == 0
        assert response.meta.llm_used is False
