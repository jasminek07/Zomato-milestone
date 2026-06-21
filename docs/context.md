# Project Context: AI-Powered Restaurant Recommendation System

## Overview

This project is an **AI-powered restaurant recommendation service** inspired by **Zomato**. The system intelligently suggests restaurants based on user preferences by combining **structured restaurant data** with a **Large Language Model (LLM)** to produce personalized, human-like recommendations.

---

## Objective

Design and implement an application that:

1. Takes user preferences (location, budget, cuisine, ratings, and more)
2. Uses a real-world dataset of restaurants
3. Leverages an LLM to generate personalized, human-like recommendations
4. Displays clear and useful results to the user

---

## Data Source

| Item | Details |
|------|---------|
| **Dataset** | Zomato Restaurant Recommendation |
| **Source** | Hugging Face |
| **URL** | https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation |

### Relevant Fields to Extract

- Restaurant name
- Location
- Cuisine
- Cost
- Rating
- (Other fields as available in the dataset)

---

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face
- Extract relevant fields: restaurant name, location, cuisine, cost, rating, etc.

### 2. User Input

Collect the following user preferences:

| Preference | Examples / Notes |
|------------|------------------|
| **Location** | Delhi, Bangalore |
| **Budget** | Low, medium, high |
| **Cuisine** | Italian, Chinese |
| **Minimum rating** | Numeric threshold |
| **Additional preferences** | Family-friendly, quick service, etc. |

### 3. Integration Layer

- Filter and prepare relevant restaurant data based on user input
- Pass structured results into an LLM prompt
- Design a prompt that helps the LLM reason and rank options

### 4. Recommendation Engine

Use the LLM to:

- **Rank** restaurants by relevance to user preferences
- **Explain** why each recommendation fits the user's criteria
- **Optionally summarize** the overall set of choices

### 5. Output Display

Present top recommendations in a user-friendly format. Each recommendation should include:

| Field | Description |
|-------|-------------|
| **Restaurant Name** | Name of the recommended restaurant |
| **Cuisine** | Type of cuisine offered |
| **Rating** | Restaurant rating |
| **Estimated Cost** | Approximate cost for dining |
| **AI-generated explanation** | Why this restaurant was recommended |

---

## Architecture Summary

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Zomato Dataset │────▶│  Data Ingestion  │────▶│  Structured Records │
│  (Hugging Face) │     │  & Preprocessing │     │  (name, location,   │
└─────────────────┘     └──────────────────┘     │   cuisine, cost,    │
                                                  │   rating, etc.)     │
                                                  └──────────┬──────────┘
                                                             │
┌─────────────────┐     ┌──────────────────┐                 │
│   User Input    │────▶│  Filter & Prepare│◀────────────────┘
│  (preferences)  │     │  Relevant Data   │
└─────────────────┘     └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  LLM Prompt      │
                        │  (rank + explain)│
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Recommendation  │
                        │  Engine (LLM)    │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Output Display  │
                        │  (top picks +    │
                        │   explanations)  │
                        └──────────────────┘
```

---

## Key Requirements Checklist

- [ ] Load Zomato dataset from Hugging Face
- [ ] Preprocess and extract relevant restaurant fields
- [ ] Build user input collection (location, budget, cuisine, rating, extras)
- [ ] Implement filtering logic based on user preferences
- [ ] Design LLM prompt for ranking and explanation
- [ ] Integrate LLM for recommendation generation
- [ ] Display results: name, cuisine, rating, cost, AI explanation
- [ ] Ensure all UI icons/symbols (e.g. Material Symbols) render correctly instead of displaying as text placeholders (load external font links properly in the layout's HTML head)

---

## Original Problem Statement

> **Problem Statement: AI-Powered Restaurant Recommendation System (Zomato Use Case)**
>
> You are tasked with building an AI-powered restaurant recommendation service inspired by Zomato. The system should intelligently suggest restaurants based on user preferences by combining structured data with a Large Language Model (LLM).
