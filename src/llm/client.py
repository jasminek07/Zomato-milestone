import os
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from src.api.schemas import UserPreferences
from src.data.models import LLMResponse
from src.llm.fallback_ranker import FallbackRanker
from src.llm.prompt_builder import PromptAssembler
from src.llm.response_parser import ResponseParser

logger = logging.getLogger(__name__)

class LLMClient(ABC):
    @abstractmethod
    def complete(self, prefs: UserPreferences, candidates: List[Dict[str, Any]]) -> LLMResponse:
        pass

class GroqClient(LLMClient):
    def __init__(self):
        try:
            from groq import Groq
            api_key = os.getenv("LLM_API_KEY")
            if not api_key:
                logger.warning("LLM_API_KEY is not set. GroqClient will fail or fallback.")
            else:
                api_key = api_key.strip()
            self.client = Groq(api_key=api_key)
            self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        except ImportError:
            logger.error("groq package not installed. GroqClient unavailable.")
            self.client = None

    def complete(self, prefs: UserPreferences, candidates: List[Dict[str, Any]]) -> LLMResponse:
        if not self.client:
            logger.warning("GroqClient not initialized properly, using fallback ranker.")
            return FallbackRanker.rank(prefs, candidates)

        prompt = PromptAssembler.assemble_prompt(prefs, candidates)
        
        system_message = (
            "You are a restaurant recommendation assistant for an app like Zomato.\n"
            "Given a user's preferences and a list of candidate restaurants (JSON),\n"
            f"rank the top {prefs.num_recommendations} restaurants and explain why each fits the user.\n"
            "Respond ONLY with valid JSON matching the exact schema requested.\n"
            "Do not invent restaurants not in the candidate list.\n"
            "Each restaurant_id must appear at most ONCE in the recommendations array — do not repeat the same restaurant."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=800,
            )
            
            content = response.choices[0].message.content
            return ResponseParser.parse_and_validate(content, candidates, self)
        except Exception as e:
            logger.error(f"Groq LLM call failed: {e}")
            logger.info("Using FallbackRanker.")
            return FallbackRanker.rank(prefs, candidates)

def get_llm_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    if provider == "groq":
        return GroqClient()
    else:
        logger.warning(f"Unknown or fallback provider '{provider}'. Using FallbackRanker directly.")
        # Create a dummy client that just uses fallback
        class DummyFallbackClient(LLMClient):
            def complete(self, prefs: UserPreferences, candidates: List[Dict[str, Any]]) -> LLMResponse:
                return FallbackRanker.rank(prefs, candidates)
        return DummyFallbackClient()
