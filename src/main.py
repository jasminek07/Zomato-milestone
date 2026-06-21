import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.data.store import RestaurantStore
from src.services.orchestrator import RecommendationOrchestrator
from src.api.routes import router as api_router

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    logger.info("Initializing Application State...")
    store = RestaurantStore()
    
    # Load dataset into memory
    # Note: store.load() might block if downloading from HF, which is fine for startup.
    store.load()
    
    app.state.store = store
    app.state.orchestrator = RecommendationOrchestrator(store)
    logger.info("Application State Initialized Successfully.")
    
    yield
    
    # Cleanup on shutdown (if any)
    logger.info("Shutting down application...")
    app.state.store = None
    app.state.orchestrator = None

# Initialize FastAPI App
app = FastAPI(
    title="Zomato Recommendation Engine API",
    description="AI-powered restaurant recommendation system REST API.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS (allow all for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core API routes
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    # Allow programmatic execution of uvicorn for debugging
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
