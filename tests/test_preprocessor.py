import pytest
from src.data.preprocessor import Preprocessor

def test_clean_rating():
    # Regular rating formats
    assert Preprocessor.clean_rating("4.1/5") == 4.1
    assert Preprocessor.clean_rating("3.9 /5") == 3.9
    assert Preprocessor.clean_rating("4.5") == 4.5
    assert Preprocessor.clean_rating(4.2) == 4.2

    # Edge cases / text ratings
    assert Preprocessor.clean_rating("NEW") == 0.0
    assert Preprocessor.clean_rating("-") == 0.0
    assert Preprocessor.clean_rating("") == 0.0
    assert Preprocessor.clean_rating("invalid") is None
    assert Preprocessor.clean_rating(None) is None

def test_clean_cost():
    # Formatted costs
    assert Preprocessor.clean_cost("1,200") == 1200.0
    assert Preprocessor.clean_cost("500") == 500.0
    assert Preprocessor.clean_cost("Rs. 450") == 450.0
    assert Preprocessor.clean_cost(" 800 ") == 800.0
    assert Preprocessor.clean_cost(1000) == 1000.0

    # Null / invalid costs
    assert Preprocessor.clean_cost(None) is None
    assert Preprocessor.clean_cost("") is None
    assert Preprocessor.clean_cost("N/A") is None

def test_determine_budget_tier():
    # Low budget (<= 500)
    assert Preprocessor.determine_budget_tier(300) == "low"
    assert Preprocessor.determine_budget_tier(500) == "low"

    # Medium budget (501 to 1500)
    assert Preprocessor.determine_budget_tier(501) == "medium"
    assert Preprocessor.determine_budget_tier(1000) == "medium"
    assert Preprocessor.determine_budget_tier(1500) == "medium"

    # High budget (> 1500)
    assert Preprocessor.determine_budget_tier(1501) == "high"
    assert Preprocessor.determine_budget_tier(2500) == "high"

    # Fallback/missing cost
    assert Preprocessor.determine_budget_tier(None) == "medium"

def test_parse_cuisines():
    # Multiple cuisines
    assert Preprocessor.parse_cuisines("Italian, Pizza, Fast Food") == ["Italian", "Pizza", "Fast Food"]
    # Single cuisine
    assert Preprocessor.parse_cuisines("North Indian") == ["North Indian"]
    # Empty / null cases
    assert Preprocessor.parse_cuisines("") == []
    assert Preprocessor.parse_cuisines(None) == []

def test_preprocess_row():
    row = {
        "name": "The Pizza Palace",
        "location": "Indiranagar",
        "rate": "4.2/5",
        "approx_cost(for two people)": "1,200",
        "cuisines": "Italian, Pizza",
        "url": "https://www.zomato.com/bangalore/the-pizza-palace"
    }

    res = Preprocessor.preprocess_row(row, 0)
    assert res is not None
    assert res.id == "https://www.zomato.com/bangalore/the-pizza-palace"
    assert res.name == "The Pizza Palace"
    assert res.location == "Indiranagar"
    assert res.rating == 4.2
    assert res.cost_for_two == 1200.0
    assert res.budget_tier == "medium"
    assert res.cuisines == ["Italian", "Pizza"]
    assert res.raw == row

def test_preprocess_row_variations():
    # Check fallback for ID, alternative key casings
    row = {
        "Name": "Cafe Coffee Day",
        "Location": "Koramangala",
        "Rating": "3.8",
        "cost": "450",
        "cuisine": "Cafe"
    }

    res = Preprocessor.preprocess_row(row, 42)
    assert res is not None
    assert res.id == "r_42"
    assert res.name == "Cafe Coffee Day"
    assert res.location == "Koramangala"
    assert res.rating == 3.8
    assert res.cost_for_two == 450.0
    assert res.budget_tier == "low"
    assert res.cuisines == ["Cafe"]
