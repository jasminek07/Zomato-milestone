import streamlit as st
import logging
from src.data.store import RestaurantStore
from src.services.orchestrator import RecommendationOrchestrator
from src.api.schemas import UserPreferences

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit Page Settings
st.set_page_config(
    page_title="Zomato AI Recommender",
    page_icon="🍽️",
    layout="wide",
)

# Custom Premium Styling matching Zomato's aesthetic
st.markdown(
    """
    <style>
    /* Premium Theme Colors */
    :root {
        --bg: #131317;
        --primary: #e23744;
        --surface: #1f1f23;
        --on-surface: #e4e1e7;
    }
    
    /* Main container styling */
    .stApp {
        background-color: #131317;
        color: #e4e1e7;
        font-family: 'Outfit', system-ui, sans-serif;
    }
    
    /* Title styles */
    .title-ai {
        color: #e23744;
        font-weight: 800;
        text-shadow: 0 0 15px rgba(226, 55, 68, 0.3);
    }
    
    /* Banner/Cards */
    .rec-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        transition: transform 0.2s;
    }
    
    .rec-card:hover {
        transform: translateY(-2px);
        border-color: #e23744;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }
    
    .rec-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    
    .rec-name {
        font-size: 20px;
        font-weight: 600;
        color: #ffffff;
    }
    
    .rec-rating {
        background: rgba(245, 166, 35, 0.15);
        color: #f5a623;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 14px;
    }
    
    .rec-tag {
        font-size: 12px;
        padding: 3px 10px;
        border-radius: 4px;
        background: #1f1f23;
        color: #9a9aae;
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin-right: 6px;
        display: inline-block;
    }
    
    .rec-tag.cost {
        color: #22c55e;
        background: rgba(34, 197, 94, 0.12);
        border-color: #22c55e;
    }
    
    .rec-explanation {
        font-size: 14px;
        font-style: italic;
        color: #9a9aae;
        margin-top: 10px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        padding-top: 10px;
    }
    
    .summary-box {
        background: rgba(255, 255, 255, 0.03);
        border-left: 4px solid #e23744;
        padding: 16px;
        border-radius: 0 12px 12px 0;
        margin-bottom: 24px;
        font-size: 16px;
        line-height: 1.6;
        color: #9a9aae;
    }
    
    .meta-pill {
        display: inline-block;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 12px;
        background: #1f1f23;
        color: #9a9aae;
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin-right: 8px;
        margin-bottom: 8px;
    }
    
    .meta-pill.green {
        color: #22c55e;
        border-color: #22c55e;
        background: rgba(34, 197, 94, 0.12);
    }
    
    .meta-pill.amber {
        color: #f5a623;
        border-color: #f5a623;
        background: rgba(245, 166, 35, 0.15);
    }
    
    .meta-pill.red {
        color: #fca5a5;
        border-color: #fca5a5;
        background: rgba(252, 165, 165, 0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Cache Resource to load the dataset and instantiate the orchestrator
@st.cache_resource
def load_orchestrator():
    logger.info("Initializing RestaurantStore for Streamlit...")
    store = RestaurantStore()
    store.load()
    orchestrator = RecommendationOrchestrator(store)
    return store, orchestrator

try:
    store, orchestrator = load_orchestrator()
except Exception as e:
    st.error(f"Failed to load dataset: {e}")
    st.stop()

# Header
st.markdown('# 🍽️ Zomato <span class="title-ai">AI</span> Assistant', unsafe_allow_html=True)
st.markdown("India's smartest AI-powered dining helper. Discover curated restaurant suggestions in seconds.")
st.markdown("---")

# Sidebar - User Inputs
st.sidebar.markdown("### ✨ Your Preferences")

locations = store.get_locations()
cuisines = store.get_cuisines()

location = st.sidebar.selectbox(
    "Location (Required)",
    options=[""] + locations,
    format_func=lambda x: "Select a location..." if x == "" else x,
    index=0,
)

budget = st.sidebar.radio(
    "Budget Tier",
    options=["low", "medium", "high"],
    format_func=lambda x: {"low": "₹ Low", "medium": "₹₹ Medium", "high": "₹₹₹ High"}[x],
    index=1,
)

cuisine = st.sidebar.selectbox(
    "Cuisine (Optional)",
    options=[""] + cuisines,
    format_func=lambda x: "Any Cuisine" if x == "" else x,
    index=0,
)

min_rating = st.sidebar.slider(
    "Minimum Rating",
    min_value=0.0,
    max_value=5.0,
    value=4.0,
    step=0.1,
    format="%.1f ⭐",
)

num_recommendations = st.sidebar.selectbox(
    "Recommendations Count",
    options=[3, 5, 7, 10],
    index=1,
)

additional = st.sidebar.text_area(
    "Additional Requests (Optional)",
    placeholder="e.g. rooftop seating, family-friendly, quick service...",
)

submit = st.sidebar.button("✨ Find My Restaurant", use_container_width=True)

# Main Dashboard logic
if submit:
    if not location:
        st.warning("Please select a location in the sidebar preferences.")
    else:
        # Build Preferences schema
        prefs = UserPreferences(
            location=location,
            budget=budget,
            cuisine=cuisine if cuisine != "" else None,
            min_rating=min_rating,
            num_recommendations=num_recommendations,
            additional=additional if additional.strip() != "" else None,
        )

        with st.spinner("Consulting the AI Chef..."):
            try:
                response = orchestrator.recommend(prefs)
            except Exception as e:
                st.error(f"Something went wrong while generating recommendations: {e}")
                st.stop()

        # Render Results
        if len(response.recommendations) == 0:
            st.markdown("### ⚠️ No restaurants found!")
            st.markdown(response.summary)
            st.info("Try relaxing your filters or choosing a different location.")
        else:
            # Summary Banner
            st.markdown(f'<div class="summary-box">✨ {response.summary}</div>', unsafe_allow_html=True)
            
            # Recommendation list
            for rec in response.recommendations:
                is_first = rec.rank == 1
                border_color = "#f5a623" if is_first else "#e23744"
                
                # Parse cuisines
                cuisine_tags = [c.strip() for c in rec.cuisine.split(",") if c.strip()]
                tags_html = "".join([f'<span class="rec-tag">{c}</span>' for c in cuisine_tags])
                tags_html += f'<span class="rec-tag cost">💰 {rec.estimated_cost}</span>'

                card_html = f"""
                <div class="rec-card" style="border-left: 5px solid {border_color};">
                    <div class="rec-header">
                        <div class="rec-name">#{rec.rank} &nbsp; {rec.restaurant_name}</div>
                        <div class="rec-rating">{rec.rating} ⭐</div>
                    </div>
                    <div style="margin-bottom: 8px;">
                        {tags_html}
                    </div>
                    <div class="rec-explanation">
                        <strong>🤖 AI explanation:</strong> {rec.explanation}
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
            
            # Metadata Banner
            st.markdown("---")
            meta = response.meta
            st.markdown(
                f"""
                <div>
                    <span class="meta-pill">📊 Candidates Considered: <b>{meta.candidates_considered}</b></span>
                    <span class="meta-pill {'green' if meta.llm_used else 'amber'}">🤖 AI Ranked: <b>{'Yes' if meta.llm_used else 'Fallback'}</b></span>
                    {f'<span class="meta-pill red">⚠️ Filters Relaxed: {", ".join(meta.filters_relaxed)}</span>' if meta.filters_relaxed else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    # Welcome / Idle state
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("🍽️ What are you craving today?")
        st.markdown(
            """
            Use the sidebar preferences panel on the left to set:
            - **Your Location** (Indiranagar, Bellandur, Brigade Road, etc.)
            - **Your Budget** (Low, Medium, or High)
            - **Any Cuisine** or dietary preference
            - **Minimum rating** and count of recommendations
            - **Additional custom notes** (e.g., "family-friendly", "romantic date night", "fast service")
            
            Once ready, click **Find My Restaurant** to get personalized, AI-ranked suggestions!
            """
        )
    with col2:
        st.image("https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=600&auto=format&fit=crop", caption="Find your next favorite dining spot")
