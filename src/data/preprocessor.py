import pandas as pd
import re
import logging
from typing import List, Dict, Any, Optional
from src.config import BUDGET_LOW_THRESHOLD, BUDGET_MEDIUM_THRESHOLD
from src.data.models import Restaurant

logger = logging.getLogger(__name__)

class Preprocessor:
    @staticmethod
    def clean_rating(val: Any) -> Optional[float]:
        """Convert ratings formatted as '4.1/5' or '3.5' to float, handling 'NEW', '-' as 0.0."""
        if pd.isna(val) or val is None:
            return None
        val_str = str(val).strip()
        if val_str in ("NEW", "-", ""):
            return 0.0
        
        # Match X.X/5
        match = re.match(r"^([0-9.]+)\s*/\s*5", val_str)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        
        # Direct float conversion
        try:
            return float(val_str)
        except ValueError:
            return None

    @staticmethod
    def clean_cost(val: Any) -> Optional[float]:
        """Parse numeric cost for two people, removing formatting commas/symbols."""
        if pd.isna(val) or val is None:
            return None
        val_str = str(val).strip()
        # Extract numbers and decimal points
        val_str = re.sub(r"[^\d.]", "", val_str)
        if not val_str:
            return None
        try:
            return float(val_str)
        except ValueError:
            return None

    @staticmethod
    def determine_budget_tier(cost: Optional[float]) -> str:
        """Map numeric cost to low, medium, or high budget tier."""
        if cost is None:
            return "medium"  # Fallback tier
        if cost <= BUDGET_LOW_THRESHOLD:
            return "low"
        elif cost <= BUDGET_MEDIUM_THRESHOLD:
            return "medium"
        else:
            return "high"

    @staticmethod
    def parse_cuisines(val: Any) -> List[str]:
        """Parse comma-separated cuisines into a clean list of strings."""
        if pd.isna(val) or val is None:
            return []
        val_str = str(val).strip()
        if not val_str:
            return []
        return [c.strip() for c in val_str.split(",") if c.strip()]

    @classmethod
    def preprocess_row(cls, row: Dict[str, Any], idx: int) -> Optional[Restaurant]:
        """Preprocess a single raw row dictionary into a Restaurant model."""
        # Find column keys regardless of slight spelling/casing variations
        def get_value(possible_keys: List[str]) -> Any:
            for pk in possible_keys:
                for k in row.keys():
                    # Check matching keys case-insensitively, removing spaces and underscores
                    clean_k = k.lower().replace(" ", "").replace("_", "").replace("-", "")
                    clean_pk = pk.lower().replace(" ", "").replace("_", "").replace("-", "")
                    if clean_k == clean_pk:
                        return row[k]
            return None

        name = get_value(["name"])
        if name is not None:
            name = str(name).strip()
        if not name:
            return None

        location = get_value(["location", "city", "listedincity", "listedin(city)"])
        if location is not None:
            location = str(location).strip()
        if not location:
            return None

        # Clean rating
        rate_val = get_value(["rate", "rating"])
        rating = cls.clean_rating(rate_val)
        if rating is None:
            rating = 0.0

        # Clean cost
        cost_val = get_value(["approx_cost(for two people)", "approx_cost", "cost_for_two", "cost"])
        cost = cls.clean_cost(cost_val)

        # Budget tier
        budget_tier = cls.determine_budget_tier(cost)

        # Clean cuisines
        cuisines_val = get_value(["cuisines", "cuisine"])
        cuisines = cls.parse_cuisines(cuisines_val)

        # Build unique ID
        raw_id = get_value(["id", "url"])
        if raw_id:
            restaurant_id = str(raw_id).strip()
        else:
            restaurant_id = f"r_{idx}"

        return Restaurant(
            id=restaurant_id,
            name=name,
            location=location,
            cuisines=cuisines,
            rating=rating,
            cost_for_two=cost,
            budget_tier=budget_tier,
            raw=row
        )

    @classmethod
    def preprocess_df(cls, df: pd.DataFrame) -> List[Restaurant]:
        """Preprocess entire DataFrame, filtering out malformed records."""
        restaurants = []
        for idx, row in df.iterrows():
            try:
                res = cls.preprocess_row(row.to_dict(), idx)
                if res:
                    restaurants.append(res)
            except Exception as e:
                # Log error and continue to make load resilient
                logger.warning(f"Error preprocessing row {idx}: {e}")
        return restaurants
