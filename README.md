# FridgeChef AI — Multi-Agent Meal Planning System

## Overview

FridgeChef AI is a rule-based multi-agent meal planning application that generates recipe suggestions, nutrition estimates, and grocery lists based on user-provided ingredients and dietary goals.

The system is designed as a modular pipeline where each component is responsible for a specific step in the meal planning process, enabling separation of concerns and easier maintenance.

---

## Problem Statement

Meal planning is often difficult when users:

- Have limited or random ingredients available
- Want meals aligned with fitness goals (e.g. weight loss or muscle gain)
- Need structured grocery lists
- Lack clear nutritional breakdowns of meals

Most existing recipe tools are static and do not combine ingredient availability with goal-based planning in a structured workflow.

---

## Solution Overview

FridgeChef AI addresses this by breaking the problem into multiple specialized components:

- Recipe retrieval and ranking
- Nutrition estimation
- Grocery list generation
- Safety validation
- Central orchestration layer

Each component is implemented as a dedicated agent in a structured pipeline.

---

## System Architecture

```

User Input (Streamlit UI)
↓
SafetyAgent (input validation)
↓
CoordinatorAgent (workflow orchestration)
↓
MealMCPServer (tool abstraction layer)
↓
RecipeAgent (recipe retrieval + ranking via MealDB API)
↓
NutritionAgent (macro estimation using USDA API + fallback rules)
↓
ShoppingAgent (ingredient consolidation)
↓
Final Output (recipes, nutrition, grocery list)

````

---

## Agent Design

### CoordinatorAgent
- Orchestrates the full workflow
- Validates required user inputs
- Runs safety checks before processing
- Coordinates execution across all agents
- Maintains execution trace for debugging and transparency

### RecipeAgent
- Retrieves recipes using the MealDB API via MCP server
- Ranks recipes based on ingredient overlap and coverage scoring
- Filters recipes based on dietary preference (e.g. vegetarian mode)
- Returns ranked recipe candidates with match explanations

### NutritionAgent
- Estimates calories and macronutrients per recipe
- Uses USDA FoodData Central API when available
- Falls back to deterministic nutrition database when API is unavailable
- Computes user calorie targets using a basic TDEE model
- Applies simple cooking and portion adjustments

### ShoppingAgent
- Extracts ingredients from selected recipes
- Normalizes ingredient formatting
- Removes duplicates to generate a clean grocery list

### SafetyAgent
- Performs keyword-based safety checks on user input
- Blocks unsafe or self-harm-related content before processing
- Prevents unsafe inputs from reaching downstream agents

---

## MCP Tool Layer

The `MealMCPServer` provides a controlled abstraction layer over external APIs.

It exposes:

- `search_meals` — search recipes by ingredient
- `get_meal` — retrieve full recipe details by ID

This ensures agents do not directly interact with external APIs, improving modularity and testability.

---

## Key System Features

### 1. Multi-Agent Pipeline Architecture
The system decomposes meal planning into specialized components rather than relying on a single monolithic model.

---

### 2. Tool Abstraction Layer (MCP-style Design)
All external API interactions are handled through a centralized server layer, separating logic from data retrieval.

---

### 3. Heuristic-Based Recipe Ranking
Recipes are ranked using ingredient overlap and coverage scoring to prioritize relevance to user inputs.

---

### 4. Nutrition Estimation Pipeline
Nutrition values are computed using:

- USDA FoodData Central API (when available)
- Deterministic fallback nutrition database
- Basic portion scaling and cooking adjustments

---

### 5. Safety Filtering Layer
User inputs are validated before processing using a rule-based system that blocks unsafe or harmful content.

---

### 6. Execution Trace Logging
The CoordinatorAgent records each step of the pipeline execution to improve transparency and debugging.

---

## Technical Stack

- Python
- Streamlit (UI)
- Requests (API calls)
- Pytest (testing framework)
- MealDB API
- USDA FoodData Central API

---

## Workflow

1. User enters ingredients and dietary goal
2. SafetyAgent validates input
3. CoordinatorAgent parses input and selects strategy
4. RecipeAgent retrieves and ranks recipes via MCP server
5. NutritionAgent estimates nutritional values
6. ShoppingAgent generates grocery list
7. Streamlit UI displays results and trace logs

---

## Testing Strategy

The project includes unit and integration tests covering:

- MCP tool routing
- Recipe generation and ranking
- Nutrition estimation logic
- Safety filtering behavior
- Full pipeline execution

Run tests:

```bash
pytest
````

---

## Installation & Execution

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Limitations

This project is an educational prototype with the following constraints:

* Nutrition estimates are simplified and not medical-grade
* Recipe ranking is based on heuristic scoring rather than machine learning
* No persistent memory or personalization layer
* No advanced autonomous reasoning or LLM-based agents
* External API coverage depends on MealDB and USDA datasets

---

## Future Improvements

* Integrate LLM-based recipe generation and rewriting
* Improve nutrition accuracy with more precise portion estimation
* Add user profiles for personalization
* Extend MCP layer with additional external tools
* Add feedback-based refinement logic (iterative improvement loop)
* Deploy as a production API using FastAPI + Docker

---

## Summary

FridgeChef AI demonstrates a modular rule-based multi-agent system for structured meal planning.

It emphasizes:

* separation of concerns
* tool abstraction (MCP layer)
* heuristic ranking logic
* maintainable and testable system design
* transparent execution tracing

```

---