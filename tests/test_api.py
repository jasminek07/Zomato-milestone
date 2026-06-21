import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from src.main import app
from src.api.schemas import RecommendationResponse, RecommendationDisplay, ResponseMetadata

# We mock the lifespan to avoid loading the full dataset during unit tests
@pytest.fixture(autouse=True)
def mock_app_state(monkeypatch):
    # Mocking the lifespan directly is tricky, so we inject state directly
    # and override the dependencies if needed. Since we use app.state, we can just set it.
    
    # Store Mock
    mock_store = MagicMock()
    mock_store.all.return_value = ["mock_restaurant"]
    mock_store.get_locations.return_value = ["Delhi", "Mumbai"]
    mock_store.get_cuisines.return_value = ["Italian", "Indian"]
    
    # Orchestrator Mock
    mock_orchestrator = MagicMock()
    
    # Define a default successful recommendation response
    success_resp = RecommendationResponse(
        summary="Test summary",
        recommendations=[
            RecommendationDisplay(
                rank=1,
                restaurant_name="Test Rest",
                cuisine="Italian",
                rating=4.5,
                estimated_cost="₹1000 for two",
                explanation="Test why"
            )
        ],
        meta=ResponseMetadata(
            candidates_considered=1,
            filters_applied=["location"],
            filters_relaxed=[],
            llm_used=True
        )
    )
    mock_orchestrator.recommend.return_value = success_resp
    
    app.state.store = mock_store
    app.state.orchestrator = mock_orchestrator
    
    yield
    
    # Cleanup
    app.state.store = None
    app.state.orchestrator = None

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "dataset_loaded": True}

def test_get_locations():
    response = client.get("/meta/locations")
    assert response.status_code == 200
    assert response.json() == {"locations": ["Delhi", "Mumbai"]}

def test_get_cuisines():
    response = client.get("/meta/cuisines")
    assert response.status_code == 200
    assert response.json() == {"cuisines": ["Italian", "Indian"]}

def test_recommendations_success():
    payload = {
        "location": "Delhi",
        "budget": "medium",
        "cuisine": "Italian",
        "min_rating": 4.0
    }
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Test summary"
    assert len(data["recommendations"]) == 1
    assert data["recommendations"][0]["restaurant_name"] == "Test Rest"

def test_recommendations_validation_error():
    # Make the orchestrator raise a ValueError
    app.state.orchestrator.recommend.side_effect = ValueError("Validation errors: {'location': 'Unknown location'}")
    
    payload = {
        "location": "UnknownCity",
        "budget": "medium"
    }
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 400
    assert "Unknown location" in response.json()["detail"]

def test_recommendations_zero_candidates():
    # Make the orchestrator return an empty recommendation response
    empty_resp = RecommendationResponse(
        summary="No matches",
        recommendations=[],
        meta=ResponseMetadata(
            candidates_considered=0,
            filters_applied=["location"],
            filters_relaxed=[],
            llm_used=False
        )
    )
    app.state.orchestrator.recommend.return_value = empty_resp
    app.state.orchestrator.recommend.side_effect = None # Clear side effect
    
    payload = {
        "location": "Delhi",
        "budget": "low"
    }
    response = client.post("/recommendations", json=payload)
    # The route returns 404 if recommendations is empty
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["summary"] == "No matches"
    assert len(data["detail"]["recommendations"]) == 0
