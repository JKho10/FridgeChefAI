from agents.coordinator_agent import CoordinatorAgent


def test_full_agent_pipeline():
    """
    End-to-end integration test for CoordinatorAgent meal planning pipeline.

    This test validates that the full system pipeline executes successfully
    with all agents properly connected and returning a valid structured output.

    Pipeline coverage:
        - Input validation and required field handling
        - SafetyAgent screening
        - RecipeAgent generation and ranking
        - NutritionAgent analysis and estimation
        - ShoppingAgent list generation
        - Execution trace logging across all stages

    Test scope:
        - Ensures system integration works end-to-end
        - Verifies pipeline completes without runtime exceptions
        - Confirms expected response schema exists

    Test does NOT validate:
        - Nutritional accuracy
        - Recipe ranking quality
        - External API correctness
    """

    agent = CoordinatorAgent()

    result = agent.run(
        "chicken,rice",
        "Weight Gain",
        70,
        170,
        25,
        "Male",
        "Moderate",
        "High Protein"
    )

    # ---------------- STRUCTURE VALIDATION ----------------
    assert isinstance(result, dict), "Result should be a dictionary"

    assert "recipes" in result
    assert "nutrition" in result
    assert "trace" in result

    # ---------------- BASIC INTEGRITY CHECKS ----------------
    assert isinstance(result["recipes"], list)
    assert isinstance(result["nutrition"], dict)
    assert isinstance(result["trace"], list)

    # Ensure pipeline actually executed steps
    assert len(result["trace"]) > 0, "Trace should contain execution steps"