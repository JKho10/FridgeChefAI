from agents.coordinator_agent import CoordinatorAgent

def test_full_agent_pipeline():
    """
    Tests the full coordinator agent pipeline end-to-end.

    This integration test ensures that the coordinator agent can:
    - Parse user input
    - Generate recipes
    - Compute nutrition
    - Build a trace log

    It validates that the final output structure contains the expected keys
    and that the pipeline completes without crashing.
    """

    agent = CoordinatorAgent()

    # Run full meal planning pipeline with sample user data
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

    # Validate required output structure exists
    assert "recipes" in result
    assert "nutrition" in result
    assert "trace" in result