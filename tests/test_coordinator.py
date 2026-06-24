from agents.coordinator_agent import CoordinatorAgent

def test_full_agent_pipeline():

    """
    Ensures the CoordinatorAgent can execute
    the full meal planning workflow and return
    expected output fields.
    """

    agent = CoordinatorAgent()

    result = agent.run(
        "chicken,rice",
        "Weight Gain",
        70,
        170,
        "High Protein"
    )

    assert "recipes" in result
    assert "nutrition" in result
    assert "trace" in result