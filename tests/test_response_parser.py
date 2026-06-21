import json
import pytest
from src.llm.response_parser import ResponseParser
from src.data.models import LLMResponse, LLMRecommendation
from src.api.schemas import UserPreferences

class DummyClient:
    pass

@pytest.fixture
def candidates():
    return [
        {"id": "1", "name": "Rest A"},
        {"id": "2", "name": "Rest B"},
        {"id": "3", "name": "Rest C"}
    ]

def test_valid_json(candidates):
    valid_json = json.dumps({
        "summary": "Great places",
        "recommendations": [
            {"restaurant_id": "2", "rank": 1, "explanation": "Good food"},
            {"restaurant_id": "1", "rank": 2, "explanation": "Nice ambiance"}
        ]
    })
    client = DummyClient()
    
    response = ResponseParser.parse_and_validate(valid_json, candidates, client)
    
    assert isinstance(response, LLMResponse)
    assert response.summary == "Great places"
    assert len(response.recommendations) == 2
    assert response.recommendations[0].restaurant_id == "2"
    assert response.recommendations[0].rank == 1
    assert response.recommendations[1].restaurant_id == "1"

def test_hallucinated_id_rejected(candidates):
    hallucinated_json = json.dumps({
        "summary": "Places",
        "recommendations": [
            {"restaurant_id": "99", "rank": 1, "explanation": "Hallucinated"},
            {"restaurant_id": "1", "rank": 2, "explanation": "Valid"}
        ]
    })
    client = DummyClient()
    
    response = ResponseParser.parse_and_validate(hallucinated_json, candidates, client)
    
    assert len(response.recommendations) == 1
    assert response.recommendations[0].restaurant_id == "1"
    assert response.recommendations[0].rank == 1 # re-ranked to 1

def test_malformed_json_raises_value_error(candidates):
    bad_content = "This is just plain text, not JSON at all."
    client = DummyClient()
    
    with pytest.raises(ValueError, match="Failed to parse LLM response into JSON"):
        ResponseParser.parse_and_validate(bad_content, candidates, client)

def test_markdown_json_stripped(candidates):
    markdown_json = "```json\n" + json.dumps({
        "summary": "Stripped",
        "recommendations": [
            {"restaurant_id": "3", "rank": 1, "explanation": "Good"}
        ]
    }) + "\n```"
    client = DummyClient()
    
    response = ResponseParser.parse_and_validate(markdown_json, candidates, client)
    assert len(response.recommendations) == 1
    assert response.recommendations[0].restaurant_id == "3"

def test_fallback_ranker():
    from src.llm.fallback_ranker import FallbackRanker
    
    prefs = UserPreferences(location="Delhi", budget="medium", cuisine="Italian")
    cands = [
        {"id": "1", "name": "Rest A", "rating": "4.0", "cuisine": "Chinese", "budget_tier": "low"},
        {"id": "2", "name": "Rest B", "rating": "4.5", "cuisine": "Italian", "budget_tier": "medium"},
        {"id": "3", "name": "Rest C", "rating": "5.0", "cuisine": "Indian", "budget_tier": "medium"}
    ]
    
    response = FallbackRanker.rank(prefs, cands)
    
    assert len(response.recommendations) == 3
    # Rest B has highest match: rating (4.5/5)=0.45, cuisine(Italian)=0.3, budget(medium)=0.2 -> 0.95
    # Rest C: rating (5.0/5)=0.5, cuisine(0), budget(0.2) -> 0.70
    # Rest A: rating (4.0/5)=0.4, cuisine(0), budget(0) -> 0.40
    assert response.recommendations[0].restaurant_id == "2"
    assert response.recommendations[1].restaurant_id == "3"
    assert response.recommendations[2].restaurant_id == "1"
