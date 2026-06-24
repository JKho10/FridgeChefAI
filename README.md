# FridgeChef AI — Multi-Agent Meal Intelligence System

## Overview

FridgeChef AI is a **multi-agent meal planning system** that transforms available fridge ingredients into structured, goal-aware meal recommendations.

Given simple inputs such as ingredients and a fitness goal, the system generates:

* ranked recipe suggestions
* nutrition estimates (calories and protein)
* a consolidated grocery list
* explainable reasoning traces

The system demonstrates how **agent-based decomposition + tool abstraction + iterative evaluation** can improve structured decision-making compared to a single-model approach.

---

## Problem Statement

Meal planning is a frequent real-world challenge where users struggle with:

* deciding what to cook using limited or random ingredients
* aligning meals with fitness or dietary goals
* reducing food waste through better ingredient usage
* creating complete grocery lists without missing items

Most existing recipe tools are:

* static (no goal awareness)
* non-adaptive to user constraints
* limited in reasoning across multiple objectives (taste, nutrition, availability)

FridgeChef AI addresses this by introducing a **multi-agent system that decomposes meal planning into specialized reasoning components**.

---

## Solution Overview

FridgeChef AI uses a **coordinated multi-agent architecture** where each agent is responsible for a specific reasoning task:

* **Coordinator Agent** → Orchestrates workflow, selects strategy, and manages iterative improvement
* **Recipe Agent** → Retrieves and ranks recipes using a tool abstraction layer (MCP-style server)
* **Nutrition Agent** → Estimates calories, protein, and metabolic targets using rule-based modeling
* **Shopping Agent** → Consolidates ingredients into a unified grocery list
* **Safety Agent** → Performs pre-processing safety checks on user input

This decomposition improves:

* modularity
* interpretability
* testability
* extensibility

---

## System Architecture

```
User (Streamlit UI)
        ↓
Safety Agent (Input validation)
        ↓
Coordinator Agent (Orchestration + strategy selection + retry logic)
        ↓
MCP Tool Layer (Meal API abstraction)
        ↓
Recipe Agent (retrieval + ranking)
        ↓
Nutrition Agent (macro estimation)
        ↓
Shopping Agent (grocery synthesis)
        ↓
Final Response + Execution Trace
```

### Key Design Principle

The system enforces a **strict separation between reasoning and external tools**, ensuring:

* agents do not directly call external APIs
* all external interactions are routed through a controlled tool layer (MCP server abstraction)

---

## Key Agent System Concepts

### 1. Multi-Agent Architecture inspired by ADK principles

The system breaks down meal planning into specialized agents rather than relying on a single monolithic model.

Each agent:

* owns a distinct responsibility
* operates independently
* contributes to a shared final output

---

### 2. MCP Tool Abstraction Layer

All external API interactions are handled through `MealMCPServer`.

This design provides:

* controlled access to external data sources
* clear separation between reasoning logic and data retrieval
* improved testability and replaceability of APIs

Agents interact with tools such as:

* `search_meals`
* `get_meal`

without direct API dependency.

---

### 3. Evaluation + Retry Loop (Iterative Refinement)

The Coordinator Agent includes a lightweight evaluation loop:

* generate candidate recipes
* evaluate ingredient coverage quality
* accept or retry based on threshold heuristics

If results are below quality expectations, the system:

* adjusts strategy
* retries recipe generation

This introduces **iterative improvement behavior**, improves result quality via heuristic-based retry.

---

### 4. Safety Layer

The Safety Agent performs early-stage input validation:

* detects unsafe or self-harm-related input using keyword rules
* blocks execution before downstream processing
* ensures safe system boundaries

This prevents unsafe queries from reaching external tools or downstream agents.

---

### 5. Agent Skills (Reusable Reasoning Modules)

The system includes modular “skills” used across agents:

* meal planning strategy selection based on user goals
* recipe ranking using ingredient coverage heuristics
* nutrition estimation using simplified metabolic modeling

These skills allow reuse of reasoning logic across the system.

---

## Technical Stack

* Python
* Streamlit (UI layer)
* Requests (external API calls)
* Pytest (testing framework)
* MealDB API (via MCP abstraction layer)

---

## System Workflow

1. User enters ingredients and dietary goal
2. Safety Agent validates input
3. Coordinator parses ingredients and selects strategy
4. Recipe Agent retrieves candidate meals via MCP server
5. Recipes are ranked using ingredient coverage scoring
6. Evaluation loop refines results if quality is low
7. Nutrition Agent estimates calories and protein targets
8. Shopping Agent consolidates ingredients into a grocery list
9. Streamlit UI renders results + execution trace

---

## Testing Strategy

The system includes unit and integration tests covering:

* MCP tool routing
* recipe generation and ranking
* nutrition estimation outputs
* safety filtering behavior
* full multi-agent pipeline execution

Run tests:

```bash
pytest
```

---

## Installation & Execution

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Safety & Security Design

* Input validation performed before any agent execution
* Unsafe queries are blocked early in the pipeline
* No API keys or credentials are stored in the codebase
* External API access is isolated through a controlled abstraction layer (MCP server)

---

## Deployability

FridgeChef AI is fully deployable as a lightweight **Streamlit web application**.

It requires:

* no database setup
* no authentication system
* no external infrastructure beyond MealDB API access

This makes it easy to reproduce, test, and extend.

---

## Course Concept Mapping (Evaluation Alignment)

| Concept                        | Implementation                                      |
| ------------------------------ | --------------------------------------------------- |
| Multi-Agent System (ADK-style) | CoordinatorAgent orchestrates specialized agents    |
| MCP Server                     | MealMCPServer abstracts external API access         |
| Iterative Reasoning            | Evaluation + retry loop in CoordinatorAgent         |
| Security Features              | SafetyAgent input filtering                         |
| Deployability                  | Streamlit-based application                         |
| Agent Skills                   | Strategy selection + ranking + nutrition heuristics |

---

## Limitations (Important for Evaluation Transparency)

This system is intentionally lightweight and educational in scope:

* Nutrition model uses simplified rule-based estimation (not clinical-grade)
* Recipe ranking uses heuristic coverage scoring (not ML-based ranking)
* No persistent memory or personalization layer
* No LLM-based reasoning or fine-tuning
* External API (MealDB) is limited in recipe diversity and structure

These limitations reflect design choices for clarity, modularity, and educational focus.

---

## Future Improvements

* Integration of LLM-based recipe generation and rewriting
* More advanced nutrition modeling with portion estimation
* Persistent user profiles for personalization
* Deployment as API-based service (FastAPI + Docker)
* Multi-user shared meal planning workflows
* Enhanced agent memory and feedback learning loop

---

## Summary

FridgeChef AI demonstrates a **modular multi-agent architecture for structured decision-making**, combining:

* agent decomposition
* tool abstraction (MCP layer)
* iterative evaluation loops
* safety-aware orchestration

The system is designed to show how agent-based systems can be used to solve practical meal planning tasks in a transparent, extensible, and explainable way.

---

