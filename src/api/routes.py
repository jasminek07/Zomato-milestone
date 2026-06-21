import sys
from pathlib import Path
# Insert project root to sys.path to allow absolute imports of 'src'
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import APIRouter, HTTPException, Request, status
from src.api.schemas import UserPreferences, RecommendationResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
def health_check(request: Request):
    """Health check endpoint and dataset readiness."""
    store = getattr(request.app.state, "store", None)
    is_loaded = store is not None and len(store.all()) > 0
    
    if not is_loaded:
        return {"status": "starting", "dataset_loaded": False}
        
    return {"status": "ok", "dataset_loaded": True}

@router.get("/meta/locations")
def get_locations(request: Request):
    """Retrieve all distinct parsed locations from the dataset."""
    store = getattr(request.app.state, "store", None)
    if not store:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Store not loaded")
    return {"locations": store.get_locations()}

@router.get("/meta/cuisines")
def get_cuisines(request: Request):
    """Retrieve all distinct parsed cuisines from the dataset."""
    store = getattr(request.app.state, "store", None)
    if not store:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Store not loaded")
    return {"cuisines": store.get_cuisines()}

@router.post("/recommendations", response_model=RecommendationResponse)
def get_recommendations(prefs: UserPreferences, request: Request):
    """
    Core recommendation endpoint.
    Accepts UserPreferences, returns fully formatted RecommendationResponse.
    """
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if not orchestrator:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Orchestrator not loaded")
        
    try:
        response = orchestrator.recommend(prefs)
    except ValueError as ve:
        # Validation errors raised by PreferenceValidator
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error in /recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
    # If response has no recommendations, we still return 200 with empty list,
    # or we could return 404. The plan says "Translates zero candidates into an HTTP 404."
    if not response.recommendations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.model_dump())
        
    return response
