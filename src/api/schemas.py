from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict

class UserPreferences(BaseModel):
    location: str = Field(
        ..., 
        min_length=1, 
        description="Location or neighborhood of interest (e.g., Indiranagar, Koramangala)"
    )
    budget: Literal["low", "medium", "high"] = Field(
        ..., 
        description="Budget tier of the restaurant: low, medium, or high"
    )
    cuisine: Optional[str] = Field(
        default=None, 
        description="Optional preferred cuisine (e.g., Italian, Chinese)"
    )
    min_rating: Optional[float] = Field(
        default=None, 
        ge=0.0, 
        le=5.0, 
        description="Minimum restaurant rating (0.0 to 5.0)"
    )
    additional: Optional[str] = Field(
        default=None, 
        description="Additional preferences in free-text (e.g., family-friendly, rooftop seating)"
    )
    num_recommendations: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of recommendations to return (1 to 10)"
    )

class ErrorResponse(BaseModel):
    message: str = Field(..., description="Overall error message summary")
    errors: Dict[str, str] = Field(default_factory=dict, description="Field-level validation error details")

class RecommendationDisplay(BaseModel):
    rank: int = Field(description="Recommendation rank (1 to N)")
    restaurant_name: str = Field(description="Name of the restaurant")
    cuisine: str = Field(description="Primary cuisines available")
    rating: float = Field(description="Average rating")
    estimated_cost: str = Field(description="Estimated cost string, e.g., '₹1200 for two'")
    explanation: str = Field(description="LLM generated explanation for why this fits the user")

class ResponseMetadata(BaseModel):
    candidates_considered: int = Field(description="Number of candidates evaluated by LLM")
    filters_applied: list[str] = Field(description="Filters strictly applied")
    filters_relaxed: list[str] = Field(description="Filters relaxed to find enough candidates")
    llm_used: bool = Field(description="True if LLM was used, False if fallback was used")

class RecommendationResponse(BaseModel):
    summary: str = Field(description="1-2 sentence overview of the recommendations")
    recommendations: list[RecommendationDisplay] = Field(description="Ranked list of restaurants")
    meta: ResponseMetadata = Field(description="Metadata about the recommendation process")
