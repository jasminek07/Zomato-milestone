import difflib
from typing import Tuple, Dict
from src.data.store import RestaurantStore
from src.api.schemas import UserPreferences

class PreferenceValidator:
    def __init__(self, store: RestaurantStore):
        self.store = store

    def validate(self, prefs: UserPreferences) -> Tuple[bool, Dict[str, str], UserPreferences]:
        """
        Validate UserPreferences against dynamic data inside the RestaurantStore.
        
        Returns:
            Tuple of (is_valid, errors, validated_prefs)
            where:
            - is_valid (bool): True if no errors, False otherwise.
            - errors (Dict[str, str]): Field-level error messages.
            - validated_prefs (UserPreferences): Copy of preferences with normalized/corrected fields.
        """
        errors = {}
        validated_prefs = prefs.model_copy()

        # Validate location
        locations = self.store.get_locations()
        loc_normalized = prefs.location.strip().lower()
        matched_location = None
        for loc in locations:
            if loc.lower() == loc_normalized:
                matched_location = loc
                break

        if not matched_location:
            # Fuzzy match close locations
            close_matches = difflib.get_close_matches(prefs.location, locations, n=3, cutoff=0.6)
            if close_matches:
                errors["location"] = f"Unknown location '{prefs.location}'. Did you mean: {', '.join(close_matches)}?"
            else:
                errors["location"] = f"Unknown location '{prefs.location}'."
        else:
            validated_prefs.location = matched_location

        # Validate rating
        if prefs.min_rating is not None:
            if not (0.0 <= prefs.min_rating <= 5.0):
                errors["min_rating"] = "Rating must be between 0.0 and 5.0."

        # Validate cuisine if provided
        if prefs.cuisine:
            cuisines = self.store.get_cuisines()
            cuisine_normalized = prefs.cuisine.strip().lower()
            matched_cuisine = None
            for cuis in cuisines:
                if cuis.lower() == cuisine_normalized:
                    matched_cuisine = cuis
                    break

            if not matched_cuisine:
                # Fuzzy match close cuisines
                close_cuisines = difflib.get_close_matches(prefs.cuisine, cuisines, n=3, cutoff=0.6)
                if close_cuisines:
                    errors["cuisine"] = f"Unknown cuisine '{prefs.cuisine}'. Did you mean: {', '.join(close_cuisines)}?"
                else:
                    errors["cuisine"] = f"Unknown cuisine '{prefs.cuisine}'."
            else:
                validated_prefs.cuisine = matched_cuisine

        is_valid = len(errors) == 0
        return is_valid, errors, validated_prefs
