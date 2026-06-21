import logging
import time
import pandas as pd
from datasets import load_dataset

logger = logging.getLogger(__name__)

class DatasetLoader:
    DATASET_NAME = "ManikaSaini/zomato-restaurant-recommendation"

    @classmethod
    def load_from_hf(cls, retries: int = 3, delay: float = 2.0) -> pd.DataFrame:
        """Download dataset from Hugging Face with automatic retries."""
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"Downloading dataset {cls.DATASET_NAME} from Hugging Face (attempt {attempt}/{retries})...")
                dataset = load_dataset(cls.DATASET_NAME)
                
                # Check for train split or select first available split
                if "train" in dataset:
                    split_name = "train"
                else:
                    split_name = list(dataset.keys())[0]
                
                logger.info(f"Successfully loaded dataset split: {split_name}")
                return pd.DataFrame(dataset[split_name])
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed: {e}")
                if attempt < retries:
                    time.sleep(delay * attempt)
                else:
                    logger.error("All download attempts failed.")
                    raise RuntimeError(f"Failed to load Zomato dataset from Hugging Face after {retries} retries.") from e
