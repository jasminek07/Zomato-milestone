# Architecture: AI-Powered Restaurant Recommendation System

This document describes the detailed system architecture for the Zomato-inspired restaurant recommendation service defined in [context.md](./context.md). The design combines structured restaurant data from Hugging Face with an LLM to produce ranked, explainable recommendations.

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Component Breakdown](#3-component-breakdown)
4. [Data Architecture](#4-data-architecture)
5. [Request Lifecycle](#5-request-lifecycle)
6. [Filtering & Ranking Strategy](#6-filtering--ranking-strategy)
7. [LLM Integration](#7-llm-integration)
8. [API Design](#8-api-design)
9. [Frontend / Output Layer](#9-frontend--output-layer)
10. [Technology Stack](#10-technology-stack)
11. [Deployment Architecture](#11-deployment-architecture)
12. [Non-Functional Requirements](#12-non-functional-requirements)
13. [Error Handling & Fallbacks](#13-error-handling--fallbacks)
14. [Future Extensions](#14-future-extensions)

---

## 1. Design Principles

| Principle | Description |
|-----------|-------------|
| **Structured-first, LLM-second** | Use deterministic filtering on the dataset before invoking the LLM. The LLM ranks and explains a curated shortlist—not the entire corpus. |
| **Explainability** | Every recommendation must include a human-readable reason tied to user preferences. |
| **Separation of concerns** | Data ingestion, filtering, LLM orchestration, and presentation are isolated modules. |
| **Cost efficiency** | Minimize LLM token usage by passing only filtered, compact JSON to the model. |
| **Graceful degradation** | If the LLM is unavailable, return filtered results with rule-based ranking. |

---

## 2. High-Level Architecture

The system follows a **layered pipeline architecture** with five logical tiers:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │  Web UI / CLI  —  preference form, results cards, loading states     │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION LAYER                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐   │
│  │  Preference      │  │  Recommendation  │  │  Response Formatter      │   │
│  │  Validator       │  │  Orchestrator    │  │  (DTO → display model)   │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌──────────────────────┐ ┌────────────────────┐ ┌────────────────────────────┐
│   DATA LAYER         │ │  INTEGRATION LAYER │ │  RECOMMENDATION ENGINE     │
│                      │ │                    │ │                            │
│  Dataset Loader      │ │  Filter Service    │ │  Prompt Builder            │
│  Preprocessor        │ │  Candidate Builder │ │  LLM Client                │
│  In-Memory / Cache   │ │  Prompt Assembler  │ │  Response Parser           │
└──────────────────────┘ └────────────────────┘ └────────────────────────────┘
                    │                 │                 │
                    └─────────────────┼─────────────────┘
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL SERVICES                                  │
│  Hugging Face Datasets API          LLM Provider (Groq / Anthropic)          │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Role |
|-------|------|
| **Presentation** | Collects user input and renders recommendation cards |
| **Application** | Validates requests, orchestrates the pipeline, formats responses |
| **Data** | Loads, cleans, and stores restaurant records |
| **Integration** | Filters candidates and prepares LLM-ready context |
| **Recommendation Engine** | Builds prompts, calls the LLM, parses structured output |
| **External Services** | Dataset source and LLM inference |

---

## 3. Component Breakdown

### 3.1 Data Ingestion Module

**Purpose:** Load the Zomato dataset from Hugging Face and produce a normalized in-memory collection of restaurant records.

```
Hugging Face Dataset
        │
        ▼
┌───────────────────┐
│  DatasetLoader    │  — fetch via `datasets` library
└─────────┬─────────┘
          ▼
┌───────────────────┐
│  Preprocessor     │  — normalize fields, handle nulls, parse cost ranges
└─────────┬─────────┘
          ▼
┌───────────────────┐
│  RestaurantStore  │  — list[Restaurant] held in memory or cached to disk
└───────────────────┘
```

**Responsibilities:**

- Download dataset from `ManikaSaini/zomato-restaurant-recommendation`
- Map raw columns to a canonical `Restaurant` schema
- Normalize location strings (case, whitespace)
- Parse cost into a numeric range or budget tier (`low` / `medium` / `high`)
- Coerce ratings to floats; drop or flag invalid rows
- Cache processed data locally to avoid repeated downloads

**Suggested module structure:**

```
src/
  data/
    loader.py          # Hugging Face fetch
    preprocessor.py    # cleaning & normalization
    models.py          # Restaurant dataclass / Pydantic model
    store.py           # in-memory access + optional disk cache
```

---

### 3.2 User Input Module

**Purpose:** Accept and validate user preferences before they enter the pipeline.

**Input schema:**

```python
UserPreferences:
  location: str              # required — e.g. "Delhi", "Bangalore"
  budget: Literal["low", "medium", "high"]  # required
  cuisine: str | None        # optional — e.g. "Italian"
  min_rating: float | None   # optional — e.g. 4.0
  additional: str | None     # optional free-text — e.g. "family-friendly, quick service"
  num_recommendations: int   # optional — default 5, max 10
```

**Validation rules:**

| Field | Rule |
|-------|------|
| `location` | Non-empty; matched against known cities in dataset |
| `budget` | Must be one of `low`, `medium`, `high` |
| `cuisine` | Optional; fuzzy-matched against dataset cuisine values |
| `min_rating` | Optional; range 0.0–5.0 |
| `additional` | Optional; passed verbatim to LLM for semantic reasoning |
| `num_recommendations` | Optional; default 5, max 10 |

---

### 3.3 Integration Layer (Filter & Prepare)

**Purpose:** Reduce the full dataset to a relevant candidate set and serialize it for the LLM.

```
UserPreferences + RestaurantStore
              │
              ▼
     ┌────────────────┐
     │ FilterService  │
     │  - by location │
     │  - by budget   │
     │  - by cuisine  │
     │  - by rating   │
     └───────┬────────┘
             ▼
     ┌────────────────┐
     │ CandidateBuilder│  — cap at N candidates (e.g. 20–30)
     └───────┬────────┘
             ▼
     ┌────────────────┐
     │ PromptAssembler │  — compact JSON + user prefs → prompt string
     └────────────────┘
```

**Filter order (recommended):**

1. **Location** — exact or case-insensitive match on city/location field
2. **Minimum rating** — `rating >= min_rating`
3. **Cuisine** — substring or token match on cuisine field
4. **Budget** — map restaurant cost to tier and compare

If fewer than a minimum threshold of candidates remain (e.g. < 3), progressively relax constraints (cuisine first, then budget) and note relaxations in the LLM prompt.

---

### 3.4 Recommendation Engine (LLM)

**Purpose:** Rank filtered candidates and generate explanations using an LLM.

**Sub-components:**

| Component | Responsibility |
|-----------|----------------|
| **PromptBuilder** | Constructs system + user messages with candidate JSON and preferences |
| **LLMClient** | Abstracts provider API (Groq, Anthropic, local model) |
| **ResponseParser** | Parses LLM JSON output into typed `Recommendation` objects |
| **FallbackRanker** | Rule-based ranking when LLM call fails |

See [Section 7](#7-llm-integration) for prompt design and output schema.

---

### 3.5 Output Display Module

**Purpose:** Transform engine output into a user-friendly presentation.

**Display model per recommendation:**

```python
RecommendationDisplay:
  rank: int
  restaurant_name: str
  cuisine: str
  rating: float
  estimated_cost: str
  explanation: str          # AI-generated
  summary: str | None       # optional overall summary from LLM
```

---

## 4. Data Architecture

### 4.1 Canonical Restaurant Model

```python
Restaurant:
  id: str | int
  name: str
  location: str               # city or area
  cuisines: list[str]         # parsed from raw cuisine string
  rating: float               # 0.0 – 5.0
  cost_for_two: int | None    # numeric if available
  budget_tier: str            # "low" | "medium" | "high" (derived)
  raw: dict                   # optional — preserve original row for debugging
```

### 4.2 Budget Tier Mapping

Since the dataset may express cost as ranges or rupee amounts, define explicit tier boundaries at preprocessing time:

| Tier | Cost for Two (INR) |
|------|---------------------|
| **Low** | ≤ 500 |
| **Medium** | 501 – 1500 |
| **High** | > 1500 |

*(Adjust thresholds after inspecting actual dataset distribution.)*

### 4.3 Dataset Source

| Attribute | Value |
|-----------|-------|
| Name | Zomato Restaurant Recommendation |
| Provider | Hugging Face |
| Identifier | `ManikaSaini/zomato-restaurant-recommendation` |
| Load strategy | One-time download + local cache (JSON/Parquet) |
| Refresh | Manual or on startup if cache missing |

### 4.4 Data Flow Diagram

```
┌─────────────┐    load     ┌──────────────┐   normalize   ┌─────────────┐
│ HuggingFace │ ──────────▶ │ Raw Records  │ ────────────▶ │ Restaurant  │
│   Dataset   │             │  (DataFrame) │               │   Store     │
└─────────────┘             └──────────────┘               └──────┬──────┘
                                                                    │
                              filter by prefs                       │
                                                                    ▼
                                                             ┌─────────────┐
                                                             │ Candidates  │
                                                             │  (≤ 30)     │
                                                             └──────┬──────┘
                                                                    │
                              serialize to JSON                     │
                                                                    ▼
                                                             ┌─────────────┐
                                                             │ LLM Prompt  │
                                                             │  Context    │
                                                             └─────────────┘
```

---

## 5. Request Lifecycle

End-to-end sequence for a single recommendation request:

```
User          UI/API       Orchestrator    FilterService    LLMClient       Formatter
 │              │              │                │               │              │
 │── submit ───▶│              │                │               │              │
 │  preferences │              │                │               │              │
 │              │── validate ─▶│                │               │              │
 │              │              │── filter ─────▶│               │              │
 │              │              │◀─ candidates ──│               │              │
 │              │              │── build prompt ────────────────▶│              │
 │              │              │◀─ ranked JSON ─────────────────│              │
 │              │              │── format ─────────────────────────────────────▶│
 │              │◀─ response ──│                │               │              │
 │◀── display ──│              │                │               │              │
```

**Steps:**

1. User submits preferences via form or API
2. **Orchestrator** validates input against schema
3. **FilterService** returns 20–30 candidate restaurants
4. **PromptBuilder** assembles system + user messages
5. **LLMClient** sends request; receives ranked recommendations with explanations
6. **ResponseParser** validates and maps to display DTOs
7. **Formatter** returns JSON (API) or renders UI cards

**Target latency:** < 5 seconds (dominated by LLM inference).

---

## 6. Filtering & Ranking Strategy

### 6.1 Two-Stage Ranking

| Stage | Method | Purpose |
|-------|--------|---------|
| **Stage 1 — Hard filter** | Deterministic SQL-like filters on structured fields | Reduce search space; guarantee constraint satisfaction |
| **Stage 2 — Soft rank** | LLM reasoning over shortlist | Personalize order; incorporate free-text preferences; generate explanations |

### 6.2 Hard Filter Logic

```python
def filter_restaurants(store, prefs):
    results = store.all()

    results = [r for r in results
               if prefs.location.lower() in r.location.lower()]

    if prefs.min_rating:
        results = [r for r in results if r.rating >= prefs.min_rating]

    if prefs.cuisine:
        results = [r for r in results
                   if prefs.cuisine.lower() in " ".join(r.cuisines).lower()]

    results = [r for r in results if r.budget_tier == prefs.budget]

    return results[:30]  # cap for LLM context window
```

### 6.3 Fallback Ranking (No LLM)

When the LLM is unavailable, rank by a weighted score:

```
score = (0.5 × normalized_rating)
      + (0.3 × cuisine_match_bonus)
      + (0.2 × budget_exact_match)
```

Return top 5 with a generic explanation: *"Recommended based on your location, budget, and rating preferences."*

---

## 7. LLM Integration

### 7.1 Provider Abstraction

```
┌─────────────────────────────────────┐
│           LLMClient (interface)     │
│  complete(prompt) → LLMResponse     │
└─────────────────┬───────────────────┘
                  │
            ┌─────┴─────┐
            ▼           ▼
        GroqClient  LocalModelClient
```

Environment variable `LLM_PROVIDER` selects the implementation (e.g. `groq` or `fallback`). All providers receive the same prompt structure and must return parseable JSON.

### 7.2 Prompt Design

**System message:**

```
You are a restaurant recommendation assistant for an app like Zomato.
Given a user's preferences and a list of candidate restaurants (JSON),
rank the top {num_recommendations} restaurants and explain why each fits the user.
Respond ONLY with valid JSON matching the schema provided.
Do not invent restaurants not in the candidate list.
Each restaurant_id must appear at most ONCE in the recommendations array — do not repeat the same restaurant.
```

**User message template:**

```
User Preferences:
- Location: {location}
- Budget: {budget}
- Cuisine: {cuisine or "any"}
- Minimum Rating: {min_rating or "none"}
- Additional: {additional or "none"}

Candidates:
{candidates_json}

Return JSON:
{
  "summary": "<1-2 sentence overview of recommendations>",
  "recommendations": [
    {
      "restaurant_id": "<id from candidates>",
      "rank": 1,
      "explanation": "<why this restaurant fits>"
    }
  ]
}
```

### 7.3 Token Budget

| Input | Estimated tokens |
|-------|------------------|
| System prompt | ~150 |
| User preferences | ~50 |
| 30 candidates (compact JSON) | ~1,500 – 2,500 |
| **Total input** | ~2,000 – 3,000 |
| **Expected output** | ~500 – 800 |

Cap candidates at 30 and include only essential fields (`id`, `name`, `cuisine`, `rating`, `cost`, `budget_tier`) to stay within context limits.

### 7.4 Response Validation

After LLM response:

1. Parse JSON; retry once on malformed output with a repair prompt
2. Verify every `restaurant_id` exists in the candidate set
3. **Deduplicate** — keep only the first occurrence of each `restaurant_id`; discard any subsequent entries for the same restaurant to prevent duplicate cards in the UI
4. Merge LLM explanations with full restaurant metadata from the store
5. Reject hallucinated restaurants not in candidates

---

## 8. API Design

### 8.1 REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health check |
| `GET` | `/meta/locations` | List supported cities from dataset |
| `GET` | `/meta/cuisines` | List available cuisines |
| `POST` | `/recommendations` | Submit preferences; receive ranked results |

### 8.2 Request / Response Contract

**POST `/recommendations`**

Request:

```json
{
  "location": "Bangalore",
  "budget": "medium",
  "cuisine": "Italian",
  "min_rating": 4.0,
  "additional": "family-friendly, quick service"
}
```

Response:

```json
{
  "summary": "Here are five Italian restaurants in Bangalore that balance quality, value, and family-friendly dining.",
  "recommendations": [
    {
      "rank": 1,
      "restaurant_name": "Example Bistro",
      "cuisine": "Italian, Continental",
      "rating": 4.5,
      "estimated_cost": "₹800 for two",
      "explanation": "Highly rated Italian spot within your medium budget, known for quick service and a welcoming atmosphere for families."
    }
  ],
  "meta": {
    "candidates_considered": 18,
    "filters_applied": ["location", "budget", "cuisine", "min_rating"]
  }
}
```

### 8.3 Error Responses

| Status | Condition |
|--------|-----------|
| `400` | Invalid or missing required fields |
| `404` | No restaurants match after filtering |
| `502` | LLM provider error (fallback ranking may still return `200`) |
| `503` | Dataset not loaded |

---

## 9. Frontend / Output Layer

### 9.1 UI Structure

```
┌─────────────────────────────────────────────────────────┐
│  🍽 Restaurant Recommender                              │
├─────────────────────────────────────────────────────────┤
│  Location:    [ Bangalore          ▼ ]                  │
│  Budget:      ( ) Low  (•) Medium  ( ) High             │
│  Cuisine:     [ Italian            ▼ ]                  │
│  Min Rating:  [ 4.0                ]                    │
│  Count:       [ 5                  ▼ ]                  │
│  Notes:       [ family-friendly, quick service ]        │
│                                                         │
│              [ Get Recommendations ]                    │
├─────────────────────────────────────────────────────────┤
│  Summary: "Here are five Italian restaurants..."       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ #1  Example Bistro          ⭐ 4.5  ₹800       │   │
│  │ Italian, Continental                            │   │
│  │ "Highly rated Italian spot within your..."      │   │
│  └─────────────────────────────────────────────────┘   │
│  ... (cards #2–#5)                                      │
└─────────────────────────────────────────────────────────┘
```

### 9.2 UI States

| State | Behavior |
|-------|----------|
| **Idle** | Form ready for input |
| **Loading** | Spinner while LLM processes (~2–5 s) |
| **Success** | Render summary + recommendation cards |
| **Empty** | "No restaurants found — try relaxing your filters" |
| **Error** | User-friendly message; offer retry |

### 9.3 Frontend Options

| Option | Best for |
|--------|----------|
| **Streamlit** | Fast prototype; minimal frontend code |
| **React + FastAPI** | Production-style separation; reusable API |
| **CLI** | Development and automated testing |

### 9.4 Asset and Icon Loading

To ensure web assets, typography, and icon libraries (such as Google Material Symbols) render correctly and avoid displaying raw text placeholders (e.g. `location_on`, `restaurant_menu`, `arrow_forward`), external stylesheets must be imported directly using `<link>` tags within the HTML `<head>` in the root layout rather than CSS `@import` rules, which can fail to resolve in Server-Side Rendering (SSR) environments.

---

## 10. Technology Stack

### Recommended Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Language** | Python 3.11+ | Rich ML/data ecosystem; Hugging Face `datasets` support |
| **Data loading** | `datasets`, `pandas` | Native Hugging Face integration |
| **Validation** | `pydantic` v2 | Typed request/response models |
| **API** | FastAPI | Async, auto OpenAPI docs, Pydantic integration |
| **LLM** | Groq SDK | Structured output; easy swap via interface |
| **Frontend** | Streamlit or React | Streamlit for MVP; React for polished UI |
| **Config** | `python-dotenv` | API keys via environment variables |
| **Testing** | `pytest` | Unit tests for filter logic and parsers |

### Project Layout

```
zomato-milestone/
├── docs/
│   ├── context.md
│   ├── architecture.md
│   └── problemstatement.txt
├── src/
│   ├── main.py                 # FastAPI or Streamlit entry point
│   ├── config.py               # env vars, tier thresholds
│   ├── data/
│   │   ├── loader.py
│   │   ├── preprocessor.py
│   │   ├── models.py
│   │   └── store.py
│   ├── services/
│   │   ├── filter_service.py
│   │   ├── orchestrator.py
│   │   └── formatter.py
│   ├── llm/
│   │   ├── client.py
│   │   ├── prompt_builder.py
│   │   └── response_parser.py
│   └── api/
│       ├── routes.py
│       └── schemas.py
├── tests/
│   ├── test_filter.py
│   ├── test_preprocessor.py
│   └── test_response_parser.py
├── data/
│   └── cache/                  # processed dataset cache
├── .env.example
├── requirements.txt
└── README.md
```

---

## 11. Deployment Architecture

### 11.1 Local / Development

```
Developer Machine
├── Python app (FastAPI + Streamlit)
├── Local dataset cache (data/cache/)
└── LLM API key in .env
```

### 11.2 Production (Optional)

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Browser    │────▶│  Web Server  │────▶│  App Container  │
│              │     │  (nginx)     │     │  (FastAPI)      │
└──────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                                    ┌──────────────┼──────────────┐
                                    ▼              ▼              ▼
                              Dataset Cache   LLM Provider    Logs / Metrics
                              (volume mount)  (HTTPS API)
```

**Container considerations:**

- Bake or mount preprocessed dataset cache to avoid cold-start downloads
- Set `LLM_API_KEY` via secrets manager
- Health check on `/health` includes dataset-loaded flag

---

## 12. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| **Response time** | < 5 s p95 (LLM-bound) |
| **Availability** | Fallback ranking if LLM fails |
| **Scalability** | Stateless API; dataset loaded once at startup |
| **Maintainability** | Modular packages; provider-agnostic LLM interface |
| **Security** | API keys in env only; no secrets in code or logs |
| **Observability** | Log filter counts, LLM latency, parse failures |

---

## 13. Error Handling & Fallbacks

| Scenario | Handling |
|----------|----------|
| Dataset download fails | Retry 3×; serve from stale cache if available |
| Zero candidates after filter | Return `404` with suggestions to relax filters |
| LLM timeout / rate limit | Use fallback rule-based ranker; flag `llm_used: false` in response |
| Malformed LLM JSON | Retry with repair prompt; fallback if second attempt fails |
| Hallucinated restaurant ID | Discard entry; fill rank from next valid recommendation |
| Invalid user input | Return `400` with field-level validation errors |

---

## 14. Future Extensions

| Extension | Description |
|-----------|-------------|
| **Vector search** | Embed restaurant descriptions; semantic match on `additional` preferences before LLM |
| **User history** | Persist past searches; personalize prompts |
| **Multi-location** | Support "near me" with geocoding |
| **Streaming responses** | Stream LLM explanations token-by-token in UI |
| **A/B testing** | Compare prompt variants for recommendation quality |
| **Feedback loop** | Thumbs up/down on recommendations to refine ranking |

---

## Appendix: Mapping to Context Requirements

| Context Requirement | Architecture Component |
|---------------------|------------------------|
| Load Zomato dataset from Hugging Face | `Data Ingestion Module` → `DatasetLoader` |
| Preprocess restaurant fields | `Preprocessor` → `Restaurant` model |
| Collect user preferences | `User Input Module` → `UserPreferences` schema |
| Filter by user input | `Integration Layer` → `FilterService` |
| LLM prompt for ranking | `Recommendation Engine` → `PromptBuilder` |
| LLM integration | `LLMClient` + `ResponseParser` |
| Display name, cuisine, rating, cost, explanation | `Output Display Module` → `RecommendationDisplay` |

---

*Derived from [context.md](./context.md) — AI-Powered Restaurant Recommendation System (Zomato Use Case).*
