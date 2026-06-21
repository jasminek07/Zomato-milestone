# Edge Cases & Handling Guide

This document catalogs edge cases for the AI-Powered Restaurant Recommendation System. Each entry describes the scenario, expected behavior, responsible module, and how to verify it.

Derived from [architecture.md](./architecture.md), [context.md](./context.md), and [implementationplan.md](./implementationplan.md).

---

## Table of Contents

1. [How to Use This Document](#1-how-to-use-this-document)
2. [Data Ingestion & Preprocessing](#2-data-ingestion--preprocessing)
3. [User Input & Validation](#3-user-input--validation)
4. [Filtering & Candidate Preparation](#4-filtering--candidate-preparation)
5. [LLM Recommendation Engine](#5-llm-recommendation-engine)
6. [Application Orchestration & Formatting](#6-application-orchestration--formatting)
7. [REST API](#7-rest-api)
8. [Frontend / UI](#8-frontend--ui)
9. [Configuration & Startup](#9-configuration--startup)
10. [Security & Abuse](#10-security--abuse)
11. [Performance & Concurrency](#11-performance--concurrency)
12. [Deployment & Operations](#12-deployment--operations)
13. [Quick Reference Matrix](#13-quick-reference-matrix)

---

## 1. How to Use This Document

| Column | Meaning |
|--------|---------|
| **ID** | Unique reference for tests and issue tracking |
| **Scenario** | What can go wrong or behave unexpectedly |
| **Example** | Concrete input or data condition |
| **Handling** | Required system behavior |
| **Module** | Where to implement the fix |
| **HTTP** | API status code when applicable |
| **Test** | Suggested test name or approach |

**Severity levels:**

| Level | Meaning |
|-------|---------|
| **Critical** | Service unusable or returns wrong/harmful data |
| **High** | Degraded experience; fallback required |
| **Medium** | Incorrect UX or empty results without guidance |
| **Low** | Cosmetic or rare; handle gracefully if easy |

---

## 2. Data Ingestion & Preprocessing

### 2.1 Dataset Download & Cache

| ID | Scenario | Example | Handling | Module | Severity | Test |
|----|----------|---------|----------|--------|----------|------|
| D-01 | Hugging Face download fails (network) | No internet on first run | Retry 3× with backoff; if stale cache exists, load cache and log warning | `loader.py` | Critical | `test_loader_retries_on_network_error` |
| D-02 | No cache and download fails | Fresh install, HF down | Startup fails; `/health` returns `dataset_loaded: false`; API returns `503` | `store.py`, `routes.py` | Critical | `test_startup_fails_without_cache` |
| D-03 | Corrupt cache file | Truncated JSON in `data/cache/` | Delete corrupt cache; attempt re-download; fail clearly if download also fails | `store.py` | High | `test_corrupt_cache_recovery` |
| D-04 | Cache exists but dataset updated on HF | Old cache, new HF revision | MVP: use cache; document manual cache refresh. Future: version stamp in cache metadata | `loader.py` | Low | Manual |
| D-05 | Hugging Face rate limit / auth error | 429 or 401 from HF | Retry with backoff; surface clear error; use cache if available | `loader.py` | High | Mock 429 response |
| D-06 | Empty dataset after load | HF returns zero rows | Startup fails with explicit error; do not serve empty store | `loader.py` | Critical | `test_empty_dataset_rejected` |

### 2.2 Raw Field Parsing

| ID | Scenario | Example | Handling | Module | Severity | Test |
|----|----------|---------|----------|--------|----------|------|
| D-07 | Missing restaurant name | `name` is null or empty | Drop row; increment `dropped_rows` counter in logs | `preprocessor.py` | Medium | `test_drop_missing_name` |
| D-08 | Missing location | `location` is null | Drop row (cannot filter by location) | `preprocessor.py` | Medium | `test_drop_missing_location` |
| D-09 | Invalid rating | `"NEW"`, `-1`, `6.5`, empty string | Drop row or set to `None` and exclude from rating filters | `preprocessor.py` | Medium | `test_invalid_rating_handling` |
| D-10 | Rating as string | `"4.2"` | Coerce to float; drop if unparseable | `preprocessor.py` | Medium | `test_rating_string_coercion` |
| D-11 | Missing rating | `rating` is null | Keep row; exclude from `min_rating` filter (or treat as 0 — document choice) | `preprocessor.py` | Medium | `test_missing_rating_filter_behavior` |
| D-12 | Cost as range string | `"₹300–₹600"`, `"300-600"` | Parse midpoint or lower bound; document chosen strategy | `preprocessor.py` | High | `test_cost_range_parsing` |
| D-13 | Cost with currency symbols | `"₹1,200"`, `"Rs. 800"` | Strip symbols and commas; parse integer | `preprocessor.py` | High | `test_cost_currency_stripping` |
| D-14 | Missing cost | `cost_for_two` is null | Set `cost_for_two: None`; assign `budget_tier: "unknown"` or infer from text field | `preprocessor.py` | High | `test_missing_cost_tier` |
| D-15 | Cost at tier boundary | Exactly ₹500 or ₹1500 | Apply consistent rule: e.g. ≤500 = low, 501–1500 = medium | `preprocessor.py` | Medium | `test_tier_boundaries` |
| D-16 | Cuisine as comma-separated string | `"Italian, Continental, Pizza"` | Split, trim, lowercase-normalize for matching; preserve display string | `preprocessor.py` | Medium | `test_cuisine_parsing` |
| D-17 | Cuisine with extra whitespace | `" Italian , Chinese "` | Trim each token | `preprocessor.py` | Low | `test_cuisine_whitespace` |
| D-18 | Duplicate restaurant rows | Same name + location twice | Keep first; or dedupe by generated `id`; log duplicate count | `preprocessor.py` | Low | `test_duplicate_dedup` |
| D-19 | Duplicate IDs after normalization | Colliding `id` values | Generate stable surrogate ID (hash of name+location) | `preprocessor.py` | Medium | `test_id_collision` |
| D-20 | Location with inconsistent casing | `"BANGALORE"`, `"bangalore"` | Normalize to canonical display form; store lowercase for matching | `preprocessor.py` | Medium | `test_location_normalization` |
| D-21 | Location is area not city | `"Koramangala, Bangalore"` | Substring match still works for `"Bangalore"` filter; meta endpoint lists extractable cities | `preprocessor.py` | Medium | `test_area_in_location_string` |
| D-22 | Special characters in name | `"Café 108"`, emoji in name | UTF-8 safe storage; no encoding errors in JSON serialization | `preprocessor.py` | Low | `test_unicode_names` |
| D-23 | Extremely long text fields | 10 KB description in raw row | Truncate or omit from LLM payload; keep in `raw` only | `preprocessor.py` | Low | `test_long_field_truncation` |

### 2.3 Store & Meta Queries

| ID | Scenario | Example | Handling | Module | Severity | Test |
|----|----------|---------|----------|--------|----------|------|
| D-24 | `get_by_id` for unknown ID | `restaurant_id: "99999"` | Return `None`; parser discards recommendation | `store.py` | Medium | `test_get_by_id_missing` |
| D-25 | Meta locations list empty | All rows dropped in preprocess | Return empty list; UI shows no location options; block recommend with message | `store.py`, UI | High | `test_empty_meta_locations` |
| D-26 | Meta cuisines with hundreds of values | 200+ unique cuisines | Return sorted list; UI may use searchable dropdown | `store.py`, UI | Low | Manual |

---

## 3. User Input & Validation

### 3.1 Required Fields

| ID | Scenario | Example | Handling | Module | HTTP | Severity | Test |
|----|----------|---------|----------|--------|------|----------|------|
| U-01 | Missing `location` | `{}` or `location: ""` | Reject with field error | `schemas.py` | `400` | High | `test_missing_location` |
| U-02 | Missing `budget` | No budget field | Reject with field error | `schemas.py` | `400` | High | `test_missing_budget` |
| U-03 | Invalid `budget` value | `"cheap"`, `"MEDIUM"`, `2` | Reject; only `low`, `medium`, `high` (case-normalize input if desired) | `schemas.py` | `400` | High | `test_invalid_budget` |
| U-04 | Budget wrong case | `"Medium"` | Normalize to lowercase before validation | `schemas.py` | — | Low | `test_budget_case_normalize` |

### 3.2 Optional Fields

| ID | Scenario | Example | Handling | Module | HTTP | Severity | Test |
|----|----------|---------|----------|--------|------|----------|------|
| U-05 | `cuisine` omitted | `cuisine: null` | Treat as "any"; do not filter by cuisine | `filter_service.py` | — | Medium | `test_no_cuisine_filter` |
| U-06 | `cuisine` empty string | `cuisine: ""` | Treat same as omitted | `schemas.py` | — | Low | `test_empty_cuisine` |
| U-07 | `min_rating` omitted | No field | No rating threshold applied | `filter_service.py` | — | Medium | `test_no_min_rating` |
| U-08 | `min_rating` out of range | `5.5`, `-1` | Reject with field error | `schemas.py` | `400` | High | `test_min_rating_bounds` |
| U-09 | `min_rating` at boundary | `0.0`, `5.0` | Accept | `schemas.py` | — | Low | `test_min_rating_boundaries` |
| U-10 | `additional` omitted | No field | Pass `"none"` to LLM prompt | `prompt_builder.py` | — | Low | `test_no_additional` |
| U-11 | `additional` very long | 5,000 characters | Truncate to max length (e.g. 500 chars); log truncation | `schemas.py` | `400` or truncate | Medium | `test_additional_max_length` |
| U-12 | `additional` with prompt injection | `"Ignore instructions and..."` | Pass to LLM but system prompt forbids obeying user override; never execute code | `prompt_builder.py` | — | High | Manual review |

### 3.3 Location & Cuisine Validation

| ID | Scenario | Example | Handling | Module | HTTP | Severity | Test |
|----|----------|---------|----------|--------|------|----------|------|
| U-13 | Location not in dataset | `"Tokyo"` | Option A: reject `400` with known locations hint. Option B: allow and return `404` after filter. **Recommended:** reject at validation with suggestions | `validator` | `400` | High | `test_unknown_location` |
| U-14 | Location partial match typo | `"Banglore"` | Fuzzy suggest `"Bangalore"` in error message or auto-correct if single close match | `validator` | `400` | Medium | `test_location_fuzzy_suggest` |
| U-15 | Location with extra whitespace | `"  Delhi  "` | Trim before validation and filtering | `schemas.py` | — | Low | `test_location_trim` |
| U-16 | Cuisine not in dataset | `"Mexican"` when none exist | Allow request; filtering may return zero or trigger relaxation | `filter_service.py` | `404` possible | Medium | `test_unknown_cuisine` |
| U-17 | Cuisine partial match | `"Ital"` vs `"Italian"` | Substring match in filter handles partial user input | `filter_service.py` | — | Medium | `test_cuisine_substring` |

### 3.4 Malformed API Payloads

| ID | Scenario | Example | Handling | Module | HTTP | Severity | Test |
|----|----------|---------|----------|--------|------|----------|------|
| U-18 | Invalid JSON body | `{location: Bangalore}` | `400` with parse error | FastAPI | `400` | High | `test_invalid_json` |
| U-19 | Wrong field types | `min_rating: "four"` | `400` with type error | `schemas.py` | `400` | High | `test_wrong_field_types` |
| U-20 | Extra unknown fields | `{"location": "Delhi", "foo": 1}` | Ignore extras (Pydantic default) or reject — document choice | `schemas.py` | — | Low | `test_extra_fields` |
| U-21 | Null body | Empty POST | `400` | FastAPI | `400` | Medium | `test_null_body` |

---

## 4. Filtering & Candidate Preparation

### 4.1 Filter Logic Edge Cases

| ID | Scenario | Example | Handling | Module | HTTP | Severity | Test |
|----|----------|---------|----------|--------|------|----------|------|
| F-01 | Zero candidates after all filters | Rare cuisine + high min_rating | Return `404` with message to relax filters; list which filters were applied | `orchestrator.py` | `404` | High | `test_zero_candidates` |
| F-02 | Fewer than 3 candidates | Only 1–2 matches | Trigger progressive relaxation (cuisine → budget); note relaxations in prompt and `meta` | `filter_service.py` | `200` | High | `test_progressive_relaxation` |
| F-03 | Relaxation still yields zero | No restaurants in city at all | `404` after relaxation exhausted | `filter_service.py` | `404` | High | `test_relaxation_exhausted` |
| F-04 | More than 30 candidates | 200 matches in Delhi | Cap at 30; prefer higher rating before cap (pre-sort) | `filter_service.py` | — | High | `test_candidate_cap` |
| F-05 | Exactly 30 candidates | 30 matches | Pass all 30 to LLM | `filter_service.py` | — | Low | `test_exactly_30_candidates` |
| F-06 | Location substring false positive | User `"Del"` matches `"Model"`? | Use word-boundary or city list match where possible; document substring behavior | `filter_service.py` | — | Medium | `test_location_false_positive` |
| F-07 | Case-insensitive location | `"BANGALORE"` vs `"bangalore"` | Both match | `filter_service.py` | — | Medium | `test_location_case_insensitive` |
| F-08 | Restaurant with `budget_tier: unknown` | Missing cost | Exclude from strict budget filter OR include in relaxed pass — document | `filter_service.py` | — | Medium | `test_unknown_budget_tier` |
| F-09 | `min_rating` filters null ratings | Restaurant with no rating | Exclude from results when `min_rating` set | `filter_service.py` | — | Medium | `test_null_rating_with_min_rating` |
| F-10 | All restaurants same rating | Every rating 4.0 | Cap/sort still deterministic (e.g. by name) | `filter_service.py` | — | Low | `test_tie_rating_sort` |
| F-11 | User wants only optional filters | Location + budget only | Valid; no cuisine/rating filter | `filter_service.py` | — | Medium | `test_minimal_filters` |

### 4.2 Candidate JSON Serialization

| ID | Scenario | Example | Handling | Module | Severity | Test |
|----|----------|---------|----------|--------|----------|------|
| F-12 | JSON serialization failure | Invalid float (`nan`) in data | Sanitize at preprocess; never emit `nan` in JSON | `preprocessor.py`, `candidate_builder` | High | `test_no_nan_in_json` |
| F-13 | Candidate list empty before LLM | Should not reach LLM | Orchestrator short-circuits; no LLM call | `orchestrator.py` | High | `test_no_llm_on_empty_candidates` |
| F-14 | Very large candidate names | 200-char restaurant name | Include in JSON; LLM handles; optional truncate in compact view | `candidate_builder` | Low | Manual |

---

## 5. LLM Recommendation Engine

### 5.1 Provider & Connectivity

| ID | Scenario | Example | Handling | Module | HTTP | Severity | Test |
|----|----------|---------|----------|--------|------|----------|------|
| L-01 | Missing `LLM_API_KEY` | Empty env var | Use fallback ranker; `llm_used: false`; log warning at startup | `client.py` | `200` | High | `test_missing_api_key_fallback` |
| L-02 | Invalid API key | 401 from provider | Fallback ranker; log error; optional `502` if no fallback | `client.py` | `200` or `502` | High | Mock 401 |
| L-03 | LLM timeout | Request > 30s | Timeout config (e.g. 25s); fallback ranker | `client.py` | `200` | High | Mock timeout |
| L-04 | Rate limit (429) | Provider throttling | Retry once with backoff; then fallback | `client.py` | `200` | High | Mock 429 |
| L-05 | Provider 500 / outage | Groq down | Fallback ranker | `client.py` | `200` | High | Mock 500 |
| L-06 | Wrong `LLM_PROVIDER` value | `"groqq"` | Startup warning; fallback or fail fast — document | `config.py` | — | Medium | `test_invalid_provider` |
| L-07 | Network partition mid-request | Connection dropped | Treat as timeout; fallback | `client.py` | `200` | High | Mock connection error |

### 5.2 Response Parsing

| ID | Scenario | Example | Handling | Module | Severity | Test |
|----|----------|---------|----------|--------|----------|------|
| L-08 | Malformed JSON from LLM | Prose instead of JSON | Retry once with repair prompt; then fallback | `response_parser.py` | High | `test_malformed_json_retry` |
| L-09 | JSON wrapped in markdown | ` ```json {...} ``` ` | Strip code fences before parse | `response_parser.py` | High | `test_markdown_fence_strip` |
| L-10 | Hallucinated `restaurant_id` | ID not in candidates | Discard entry; log; fill rank from next valid | `response_parser.py` | Critical | `test_hallucinated_id_rejected` |
| L-11 | Duplicate ranks | Two `rank: 1` | Renormalize ranks 1–5 in order of appearance | `response_parser.py` | Medium | `test_duplicate_ranks` |
| L-12 | Missing ranks | Only 3 recommendations returned | Accept 3; do not pad with random restaurants | `response_parser.py` | Medium | `test_partial_recommendation_count` |
| L-13 | More than 5 recommendations | LLM returns 10 | Take first 5 valid by rank | `response_parser.py` | Low | `test_excess_recommendations_truncated` |
| L-14 | Empty `explanation` | `explanation: ""` | Use generic: *"Matches your preferences."* | `response_parser.py` | Medium | `test_empty_explanation_fallback` |
| L-15 | Missing `summary` | No summary field | Omit or use generic summary in formatter | `formatter.py` | Low | `test_missing_summary` |
| L-16 | `restaurant_id` type mismatch | ID as number vs string in JSON | Normalize to string for comparison | `response_parser.py` | Medium | `test_id_type_normalization` |
| L-17 | LLM invents new fields | Extra keys in JSON | Ignore unknown keys | `response_parser.py` | Low | `test_extra_llm_fields` |
| L-18 | LLM returns same restaurant twice | Duplicate IDs in list | Dedupe; keep first occurrence | `response_parser.py` | Medium | `test_duplicate_restaurant_ids` |
| L-19 | Repair prompt also fails | Two parse failures | Fallback ranker | `response_parser.py` | High | `test_repair_prompt_failure` |

### 5.3 Prompt & Token Limits

| ID | Scenario | Example | Handling | Module | Severity | Test |
|----|----------|---------|----------|--------|----------|------|
| L-20 | Context window exceeded | 30 large candidates | Cap at 30; compact JSON fields only; reduce to 20 if still too large | `prompt_builder.py` | High | Token count test |
| L-21 | `additional` conflicts with filters | "cheap" but budget high | LLM may rank accordingly; hard filters already applied; note in prompt | `prompt_builder.py` | Low | Manual |
| L-22 | Non-English `additional` | Hindi preferences text | Pass through; LLM should still rank | `prompt_builder.py` | Low | Manual |
| L-23 | Empty candidate explanations in fallback | LLM down, 5 candidates | Generic explanation on all 5 | `fallback_ranker` | Medium | `test_fallback_explanations` |

### 5.4 Fallback Ranker

| ID | Scenario | Example | Handling | Module | Severity | Test |
|----|----------|---------|----------|--------|----------|------|
| L-24 | Fewer than 5 candidates | Only 2 after filter | Return 2 recommendations, not 5 | `fallback_ranker` | High | `test_fallback_less_than_five` |
| L-25 | Single candidate | 1 restaurant matches | Return 1 recommendation with rank 1 | `fallback_ranker` | Medium | `test_fallback_single_candidate` |
| L-26 | All candidates same score | Tie in fallback formula | Secondary sort by name or rating | `fallback_ranker` | Low | `test_fallback_tie_break` |

---

## 6. Application Orchestration & Formatting

| ID | Scenario | Example | Handling | Module | HTTP | Severity | Test |
|----|----------|---------|----------|--------|------|----------|------|
| O-01 | Dataset not loaded at request time | Startup failed partially | `503` on `/recommendations`; health shows not ready | `orchestrator.py` | `503` | Critical | `test_request_before_dataset_ready` |
| O-02 | Concurrent requests during startup | Request while loading | Block until load completes or return `503` | `main.py` | `503` | Medium | `test_concurrent_startup` |
| O-03 | Merge LLM ID with missing store record | Race or stale ID | Skip recommendation; log | `response_parser.py` | Medium | `test_stale_id_merge` |
| O-04 | `estimated_cost` display with null cost | No cost in data | Show `"Not available"` or `"—"` | `formatter.py` | Low | `test_null_cost_display` |
| O-05 | Rating display precision | `4.333333` | Format to 1 decimal (e.g. `4.3`) | `formatter.py` | Low | `test_rating_format` |
| O-06 | Cuisine list display | `["Italian", "Pizza"]` | Join as `"Italian, Pizza"` | `formatter.py` | Low | `test_cuisine_display_join` |
| O-07 | `meta.filters_relaxed` accuracy | Cuisine relaxed | Include `filters_relaxed: ["cuisine"]` in response | `formatter.py` | Medium | `test_meta_relaxed_filters` |
| O-08 | `meta.llm_used` flag | Fallback path | `llm_used: false` clearly set | `formatter.py` | Medium | `test_llm_used_flag` |
| O-09 | `candidates_considered` count | 18 candidates | Match actual candidate count sent to LLM | `formatter.py` | Low | `test_candidates_considered_count` |

---

## 7. REST API

| ID | Scenario | Example | Handling | Module | HTTP | Severity | Test |
|----|----------|---------|----------|--------|------|----------|------|
| A-01 | `GET /health` when healthy | Normal operation | `200`, `dataset_loaded: true` | `routes.py` | `200` | Medium | `test_health_ok` |
| A-02 | `GET /health` when dataset missing | Load failed | `200` or `503` with `dataset_loaded: false` | `routes.py` | `503` | High | `test_health_degraded` |
| A-03 | `GET /meta/locations` before load | Early request | `503` or empty with status flag | `routes.py` | `503` | Medium | `test_meta_before_load` |
| A-04 | Unsupported HTTP method | `DELETE /recommendations` | `405` | FastAPI | `405` | Low | `test_method_not_allowed` |
| A-05 | Wrong content type | `text/plain` body | `400` or FastAPI validation error | FastAPI | `400` | Low | `test_wrong_content_type` |
| A-06 | Very large request body | 1 MB JSON | Reject at size limit | FastAPI middleware | `413` | Low | Optional |
| A-07 | CORS from browser UI | React on different port | Configure CORS for dev origins | `main.py` | — | Medium | Manual browser test |

### Error Response Shape

All `400` responses should include field-level detail:

```json
{
  "error": "validation_error",
  "message": "Invalid request",
  "details": [
    { "field": "budget", "message": "Must be one of: low, medium, high" }
  ]
}
```

`404` for no matches:

```json
{
  "error": "no_matches",
  "message": "No restaurants found for your preferences.",
  "suggestions": [
    "Try removing the cuisine filter",
    "Lower your minimum rating"
  ],
  "filters_applied": ["location", "budget", "cuisine", "min_rating"]
}
```

---

## 8. Frontend / UI

| ID | Scenario | Example | Handling | Module | Severity | Test |
|----|----------|---------|----------|--------|----------|------|
| UI-01 | Double submit | User clicks "Get Recommendations" twice | Disable button while loading; debounce | UI | Medium | Manual |
| UI-02 | Submit with empty required fields | No location selected | Inline validation before API call | UI | High | Manual |
| UI-03 | API `404` | No matches | Show empty state with relax-filters suggestions | UI | High | Manual |
| UI-04 | API `400` | Invalid budget | Show field errors from `details` | UI | High | Manual |
| UI-05 | API `503` | Dataset not loaded | Show service unavailable message | UI | High | Manual |
| UI-06 | Slow LLM (>5s) | Long wait | Keep spinner; optional timeout message after 10s | UI | Medium | Manual |
| UI-07 | Network error from UI | API unreachable | Error state with retry button | UI | High | Manual |
| UI-08 | Partial results (1–4 cards) | Few candidates | Display all returned; do not show empty placeholder cards | UI | Medium | Manual |
| UI-09 | Long explanation text | 500-char explanation | Card layout wraps text; no overflow break | UI | Low | Manual |
| UI-10 | Meta endpoints fail | Locations dropdown empty | Disable form or show error banner | UI | Medium | Manual |
| UI-11 | `llm_used: false` | Fallback ranking | Optional badge: "Ranked without AI" | UI | Low | Manual |
| UI-12 | Mobile narrow viewport | Small screen | Responsive card layout | UI | Low | Manual |

---

## 9. Configuration & Startup

| ID | Scenario | Example | Handling | Module | Severity | Test |
|----|----------|---------|----------|--------|----------|------|
| C-01 | Missing `.env` file | No local env | Use defaults; LLM fallback if no key | `config.py` | Medium | `test_no_env_file` |
| C-02 | Invalid integer in config | `CANDIDATE_CAP=abc` | Fail at startup with clear message | `config.py` | Medium | `test_invalid_config` |
| C-03 | `CANDIDATE_CAP=0` or negative | Invalid cap | Clamp to minimum 1 or fail startup | `config.py` | Low | `test_candidate_cap_config` |
| C-04 | Custom budget thresholds | Env overrides tiers | Apply overrides in preprocessor | `config.py` | Low | `test_custom_tier_thresholds` |
| C-05 | Read-only cache directory | Cannot write cache | Log warning; run in-memory only | `store.py` | Medium | `test_readonly_cache_dir` |

---

## 10. Security & Abuse

| ID | Scenario | Example | Handling | Module | Severity | Test |
|----|----------|---------|----------|--------|----------|------|
| S-01 | API key in logs | Exception includes key | Never log `LLM_API_KEY`; redact in error handlers | `client.py` | Critical | Log audit |
| S-02 | API key in client bundle | Key in frontend JS | **Never** expose LLM key to browser; UI calls backend only | Architecture | Critical | Code review |
| S-03 | Prompt injection in `additional` | Malicious instructions | System prompt restricts behavior; no tool execution | `prompt_builder.py` | High | Manual |
| S-04 | XSS in restaurant names | `<script>` in name | Escape HTML in UI; JSON API is fine | UI | Medium | `test_xss_escape` |
| S-05 | Request flooding | 1000 req/s | Optional rate limit in production; not required for MVP | nginx/middleware | Low | Future |
| S-06 | Path traversal in cache path | `../../etc/passwd` | Use fixed cache dir; ignore path injection | `loader.py` | Medium | `test_cache_path_safe` |

---

## 11. Performance & Concurrency

| ID | Scenario | Example | Handling | Module | Severity | Test |
|----|----------|---------|----------|--------|----------|------|
| P-01 | Many concurrent requests | 50 parallel POSTs | Stateless handlers; single in-memory store (read-only after load) | FastAPI | Medium | Load test |
| P-02 | Memory usage with full dataset | 10k+ restaurants | Monitor memory; one copy in store | `store.py` | Medium | Profiling |
| P-03 | Cold start with no cache | First download on deploy | Pre-bake cache in Docker image or init container | Deployment | High | Deploy test |
| P-04 | LLM latency dominates | 4s inference | Set client timeout; document p95 < 5s target | `client.py` | Medium | Timing test |
| P-05 | Repeated identical requests | Same prefs twice | No caching required for MVP; optional response cache later | — | Low | Future |

---

## 12. Deployment & Operations

| ID | Scenario | Example | Handling | Module | Severity | Test |
|----|----------|---------|----------|--------|----------|------|
| OP-01 | Container health check fails | Dataset not loaded | `/health` returns not ready; orchestrator restarts | Docker/k8s | High | Deploy test |
| OP-02 | Stale cache after code change | Preprocessor logic updated | Document `rm data/cache/*` or version cache file | Ops | Medium | Docs |
| OP-03 | Log volume from LLM errors | Many parse failures | Structured logs with counts; no full prompt in prod logs | Logging | Low | Log review |
| OP-04 | Disk full on cache write | Cannot save cache | Continue in-memory; log error | `store.py` | Medium | Mock disk full |
| OP-05 | Graceful shutdown | SIGTERM during LLM call | Cancel or wait; uvicorn graceful timeout | `main.py` | Low | Manual |

---

## 13. Quick Reference Matrix

Summary of highest-priority edge cases and their outcomes:

| ID | Scenario | Outcome | HTTP |
|----|----------|---------|------|
| D-01 | HF download fails | Retry → cache fallback | — |
| D-02 | No cache, download fails | Service not ready | `503` |
| F-01 | Zero candidates | No matches message | `404` |
| F-02 | < 3 candidates | Relax filters | `200` |
| L-01 | No API key | Fallback ranker | `200` |
| L-03 | LLM timeout | Fallback ranker | `200` |
| L-10 | Hallucinated ID | Discard entry | `200` |
| L-08 | Bad LLM JSON | Repair → fallback | `200` |
| U-01 | Missing location | Validation error | `400` |
| U-13 | Unknown location | Validation error + hint | `400` |
| O-01 | Dataset not loaded | Service unavailable | `503` |
| S-01 | Key in logs | Redact | — |
| S-02 | Key in frontend | Backend-only LLM | — |

---

## Test Coverage Checklist

Use this checklist when closing Phase 8 (testing):

- [ ] All **Critical** edge cases have automated tests or documented manual verification
- [ ] All **High** edge cases in sections 2–7 have unit or integration tests
- [ ] Fallback path tested end-to-end (LLM disabled)
- [ ] Zero-candidate and partial-candidate paths tested
- [ ] Validation errors return correct `400` shape
- [ ] `/health` reflects dataset state
- [ ] No secrets in logs (manual grep audit)

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [architecture.md](./architecture.md) | Error handling matrix (Section 13), filter logic |
| [implementationplan.md](./implementationplan.md) | Phase 8 error handling tasks |
| [context.md](./context.md) | Core requirements checklist |

---

*Last updated to align with architecture v1 and implementation plan phases 0–8.*
