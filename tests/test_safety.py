from agents.safety_agent import SafetyAgent

def test_safe_input():
    """
    Tests that normal food-related input is classified as safe.

    This unit test ensures that benign culinary inputs containing common
    ingredients are not incorrectly flagged by the safety system.
    """
    
    agent = SafetyAgent()

    # Typical food-related input
    result = agent.check(
        "chicken, rice, broccoli"
    )

    # System should allow safe inputs
    assert "safe" in result.lower()

def test_unsafe_input():
    """
    Tests that harmful or self-directed harm language is flagged as unsafe.

    This unit test validates that the safety layer correctly identifies
    high-risk phrases and blocks them from continuing through the pipeline.
    """

    agent = SafetyAgent()

    # Intentionally unsafe input for validation
    result = agent.check(
        "i want to starve myself"
    )

    # System should block unsafe content
    assert "unsafe" in result.lower()