import json
import logging
from pathlib import Path
from typing import List, Optional, Set
from src.config import CACHE_DIR
from src.data.loader import DatasetLoader
from src.data.preprocessor import Preprocessor
from src.data.models import Restaurant

logger = logging.getLogger(__name__)

class RestaurantStore:
    def __init__(self):
        self._restaurants: List[Restaurant] = []
        self._by_id: dict[str, Restaurant] = {}
        self._locations: Set[str] = set()
        self._cuisines: Set[str] = set()

    def load(self, force_refresh: bool = False) -> None:
        """Load data from cache, or download and preprocess if missing."""
        cache_path = Path(CACHE_DIR) / "processed_restaurants.json"
        
        if cache_path.exists() and not force_refresh:
            try:
                logger.info(f"Loading preprocessed restaurants from cache: {cache_path}")
                self._load_from_cache(cache_path)
            except Exception as e:
                logger.warning(f"Failed to load from cache: {e}. Downloading dataset fresh...")
                self._load_and_preprocess_new(cache_path)
        else:
            self._load_and_preprocess_new(cache_path)

        # Build quick lookups and helpers
        self._by_id = {r.id: r for r in self._restaurants}
        self._locations = {r.location for r in self._restaurants if r.location}
        
        self._cuisines = set()
        for r in self._restaurants:
            for c in r.cuisines:
                self._cuisines.add(c)
        
        logger.info(f"RestaurantStore loaded: {len(self._restaurants)} restaurants, "
                    f"{len(self._locations)} locations, {len(self._cuisines)} cuisines.")

    def _load_from_cache(self, cache_path: Path) -> None:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self._restaurants = [Restaurant(**item) for item in data]

    def _load_and_preprocess_new(self, cache_path: Path) -> None:
        # Fetch raw df
        df = DatasetLoader.load_from_hf()
        # Preprocess
        self._restaurants = Preprocessor.preprocess_df(df)
        
        # Write to cache
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump([r.model_dump() for r in self._restaurants], f, indent=2, ensure_ascii=False)
            logger.info(f"Cached preprocessed dataset at: {cache_path}")
        except Exception as e:
            logger.error(f"Failed to save processed cache: {e}")

    def all(self) -> List[Restaurant]:
        """Return list of all preprocessed restaurants."""
        return self._restaurants

    def get_by_id(self, restaurant_id: str) -> Optional[Restaurant]:
        """Get restaurant by unique ID."""
        return self._by_id.get(restaurant_id)

    def get_locations(self) -> List[str]:
        """Return alphabetically sorted list of unique locations."""
        return sorted(list(self._locations))

    def get_cuisines(self) -> List[str]:
        """Return alphabetically sorted list of unique cuisines."""
        return sorted(list(self._cuisines))
