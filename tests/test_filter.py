import pytest
from src.api.schemas import UserPreferences
from src.data.models import Restaurant
from src.services.filter_service import FilterService, CandidateBuilder
from src.llm.prompt_builder import PromptAssembler

# Mock Restaurant list
SAMPLE_RESTAURANTS = [
    Restaurant(id="1", name="Italian Bistro", location="Indiranagar", cuisines=["Italian"], rating=4.5, cost_for_two=800.0, budget_tier="medium"),
    Restaurant(id="2", name="Indie Pizzeria", location="Indiranagar", cuisines=["Italian", "Pizza"], rating=4.2, cost_for_two=600.0, budget_tier="medium"),
    Restaurant(id="3", name="Pasta Place", location="Indiranagar", cuisines=["Italian"], rating=4.0, cost_for_two=1200.0, budget_tier="medium"),
    Restaurant(id="4", name="Cheap Bites", location="Indiranagar", cuisines=["Fast Food"], rating=3.5, cost_for_two=300.0, budget_tier="low"),
    Restaurant(id="5", name="Spicy Curry", location="Indiranagar", cuisines=["North Indian"], rating=4.1, cost_for_two=1000.0, budget_tier="medium"),
    Restaurant(id="6", name="Fine Dine", location="Indiranagar", cuisines=["Continental"], rating=4.7, cost_for_two=2000.0, budget_tier="high"),
    # Koramangala
    Restaurant(id="7", name="Kora Cafe", location="Koramangala", cuisines=["Cafe", "Italian"], rating=4.3, cost_for_two=500.0, budget_tier="low"),
    Restaurant(id="8", name="Biryani House", location="Koramangala", cuisines=["North Indian", "Biryani"], rating=4.4, cost_for_two=600.0, budget_tier="medium"),
    Restaurant(id="9", name="Street Foods", location="Koramangala", cuisines=["Fast Food"], rating=3.0, cost_for_two=150.0, budget_tier="low")
]

@pytest.fixture
def filter_service():
    return FilterService(candidate_cap=5)

def test_strict_filtering(filter_service):
    # Indiranagar, medium budget, Italian, rating >= 4.0
    prefs = UserPreferences(
        location="Indiranagar",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0
    )
    candidates, metadata = filter_service.filter_candidates(SAMPLE_RESTAURANTS, prefs)
    
    assert len(candidates) == 3
    assert all(r.location == "Indiranagar" for r in candidates)
    assert all(r.budget_tier == "medium" for r in candidates)
    assert all("Italian" in r.cuisines for r in candidates)
    assert all(r.rating >= 4.0 for r in candidates)
    assert metadata["cuisine_relaxed"] is False
    assert metadata["budget_relaxed"] is False

def test_capping(filter_service):
    # Capped at 5 (due to fixture config)
    prefs = UserPreferences(
        location="indiranagar",
        budget="medium"
    )
    candidates, _ = filter_service.filter_candidates(SAMPLE_RESTAURANTS, prefs)
    assert len(candidates) <= 5

def test_relaxation_cuisine(filter_service):
    # Indiranagar, medium budget, Continental, min_rating >= 4.0
    # There is only 1 Continental (Fine Dine id=6) which is high budget,
    # so strict filter returns 0 candidates.
    # If we relax cuisine (keep budget), we have:
    # Indiranagar, medium budget, min_rating >= 4.0 -> ids: 1, 2, 3, 5 (4 candidates).
    # Since 4 >= 3, it should return these 4 and set cuisine_relaxed=True, budget_relaxed=False
    prefs = UserPreferences(
        location="Indiranagar",
        budget="medium",
        cuisine="Continental",
        min_rating=4.0
    )
    candidates, metadata = filter_service.filter_candidates(SAMPLE_RESTAURANTS, prefs)
    
    assert len(candidates) == 4
    assert metadata["cuisine_relaxed"] is True
    assert metadata["budget_relaxed"] is False

def test_relaxation_budget(filter_service):
    # Koramangala, low budget, Biryani, min_rating >= 4.0
    # There is no low budget Biryani in Koramangala (Biryani House is medium).
    # If we relax budget (keep cuisine: North Indian/Biryani in Koramangala) -> yields 1 candidate (id=8) which is still < 3.
    # So we relax both cuisine and budget -> returns all Koramangala rating >= 4.0 (ids: 7, 8)
    prefs = UserPreferences(
        location="Koramangala",
        budget="low",
        cuisine="Biryani",
        min_rating=4.0
    )
    candidates, metadata = filter_service.filter_candidates(SAMPLE_RESTAURANTS, prefs)
    
    assert len(candidates) == 2
    assert metadata["cuisine_relaxed"] is True
    assert metadata["budget_relaxed"] is True

def test_no_cuisine_specified_relax_budget(filter_service):
    # Koramangala, high budget, no cuisine specified, min_rating >= 4.0
    # Koramangala has zero high budget restaurants.
    # It should relax budget and return all Koramangala rating >= 4.0 (ids: 7, 8)
    prefs = UserPreferences(
        location="Koramangala",
        budget="high",
        min_rating=4.0
    )
    candidates, metadata = filter_service.filter_candidates(SAMPLE_RESTAURANTS, prefs)
    assert len(candidates) == 2
    assert metadata["cuisine_relaxed"] is False
    assert metadata["budget_relaxed"] is True

def test_candidate_builder():
    candidates = SAMPLE_RESTAURANTS[:2]
    compact = CandidateBuilder.build_candidates_json(candidates)
    assert len(compact) == 2
    assert compact[0]["id"] == "1"
    assert compact[0]["name"] == "Italian Bistro"
    assert compact[0]["cuisine"] == "Italian"
    assert compact[0]["rating"] == 4.5
    assert compact[0]["cost"] == 800.0
    assert compact[0]["budget_tier"] == "medium"

def test_prompt_assembler():
    prefs = UserPreferences(
        location="Koramangala",
        budget="low"
    )
    compact_candidates = [{"id": "7", "name": "Kora Cafe", "cuisine": "Cafe, Italian", "rating": 4.3, "cost": 500.0, "budget_tier": "low"}]
    prompt = PromptAssembler.assemble_prompt(prefs, compact_candidates)
    assert "User Preferences:" in prompt
    assert "- Location: Koramangala" in prompt
    assert "- Budget: low" in prompt
    assert "Kora Cafe" in prompt
