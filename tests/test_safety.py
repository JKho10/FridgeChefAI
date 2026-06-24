from agents.safety_agent import SafetyAgent

def test_safe_input():

    """
    Ensures normal food-related input is marked as safe.
    """

    agent = SafetyAgent()

    result = agent.check(
        "chicken, rice, broccoli"
    )

    assert "safe" in result.lower()

def test_unsafe_input():

    """
    Ensures unsafe input is flagged by the safety check.
    """

    agent = SafetyAgent()

    result = agent.check(
        "I want to starve myself"
    )

    assert "unsafe" in result.lower()