from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Restaurant(BaseModel):
    id: str = Field(description="Unique identifier for the restaurant")
    name: str = Field(description="Name of the restaurant")
    location: str = Field(description="Normalized area/locality name")
    cuisines: List[str] = Field(default_factory=list, description="Parsed list of cuisine tags")
    rating: float = Field(default=0.0, description="Average rating between 0.0 and 5.0")
    cost_for_two: Optional[float] = Field(default=None, description="Average cost for two people in INR")
    budget_tier: str = Field(description="Budget categorization: low, medium, or high")
    raw: Optional[Dict[str, Any]] = Field(default=None, description="Original raw record data for debug/fallback tracking")

class LLMRecommendation(BaseModel):
    restaurant_id: str = Field(description="The unique identifier from the candidates list")
    rank: int = Field(description="The rank from 1 to 5")
    explanation: str = Field(description="Why this restaurant fits the user's preferences")

class LLMResponse(BaseModel):
    summary: Optional[str] = Field(default=None, description="1-2 sentence overview of recommendations")
    recommendations: List[LLMRecommendation] = Field(description="List of ranked recommendations")
