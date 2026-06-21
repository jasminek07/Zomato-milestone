import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# Streamlit secrets helper
def get_config_val(key, default):
    # Try environment variables first
    val = os.getenv(key)
    if val is not None:
        return val
    # Try streamlit secrets next
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = Path(get_config_val("CACHE_DIR", str(DATA_DIR / "cache")))

# Budget thresholds (INR)
BUDGET_LOW_THRESHOLD = int(get_config_val("BUDGET_LOW_THRESHOLD", "500"))
BUDGET_MEDIUM_THRESHOLD = int(get_config_val("BUDGET_MEDIUM_THRESHOLD", "1500"))

# Filtering settings
CANDIDATE_CAP = int(get_config_val("CANDIDATE_CAP", "30"))

# LLM Configuration
LLM_PROVIDER = get_config_val("LLM_PROVIDER", "groq")
LLM_API_KEY = get_config_val("LLM_API_KEY", "")
