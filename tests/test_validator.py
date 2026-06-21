import pytest
from pydantic import ValidationError
from src.api.schemas import UserPreferences
from src.services.validator import PreferenceValidator

class MockStore:
    def get_locations(self):
        return ["Delhi", "Bangalore", "Mumbai", "Indiranagar", "Koramangala"]

    def get_cuisines(self):
        return ["Italian", "Chinese", "North Indian", "South Indian", "Continental"]

@pytest.fixture
def validator():
    return PreferenceValidator(MockStore())

def test_valid_preferences(validator):
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
        additional="family-friendly"
    )
    is_valid, errors, validated = validator.validate(prefs)
    assert is_valid is True
    assert len(errors) == 0
    assert validated.location == "Bangalore"
    assert validated.cuisine == "Italian"

def test_case_insensitive_normalization(validator):
    prefs = UserPreferences(
        location="bangalore",
        budget="low",
        cuisine="italian"
    )
    is_valid, errors, validated = validator.validate(prefs)
    assert is_valid is True
    assert validated.location == "Bangalore"
    assert validated.cuisine == "Italian"

def test_pydantic_validation_constraints():
    # Test min_rating range constraint (< 0)
    with pytest.raises(ValidationError):
        UserPreferences(location="Delhi", budget="medium", min_rating=-1.0)
        
    # Test min_rating range constraint (> 5)
    with pytest.raises(ValidationError):
        UserPreferences(location="Delhi", budget="medium", min_rating=5.5)

    # Test invalid budget values
    with pytest.raises(ValidationError):
        UserPreferences(location="Delhi", budget="expensive")

def test_unknown_location_fuzzy_match(validator):
    # "Bangalor" -> "Bangalore"
    prefs = UserPreferences(
        location="Bangalor",
        budget="medium"
    )
    is_valid, errors, _ = validator.validate(prefs)
    assert is_valid is False
    assert "location" in errors
    assert "Did you mean: Bangalore" in errors["location"]

def test_unknown_location_no_matches(validator):
    prefs = UserPreferences(
        location="XYZCity",
        budget="medium"
    )
    is_valid, errors, _ = validator.validate(prefs)
    assert is_valid is False
    assert "location" in errors
    assert "Did you mean" not in errors["location"]

def test_unknown_cuisine_fuzzy_match(validator):
    # "Italien" -> "Italian"
    prefs = UserPreferences(
        location="Delhi",
        budget="high",
        cuisine="Italien"
    )
    is_valid, errors, _ = validator.validate(prefs)
    assert is_valid is False
    assert "cuisine" in errors
    assert "Did you mean: Italian" in errors["cuisine"]
