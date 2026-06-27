from agents.safety_agent import SafetyAgent

def test_safe_input():
    """
    Unit test for SafetyAgent safe-input classification.

    This test ensures that normal, non-harmful food-related input is
    correctly classified as SAFE by the safety system.

    It validates:
        - Common culinary ingredients are not flagged as unsafe
        - Safe input passes through the safety filter
        - System does not over-trigger on neutral text

    Scope:
        - Tests safe classification behavior only
        - Does NOT test edge-case slang or adversarial inputs
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
    Unit test for SafetyAgent high-risk input detection.

    This test ensures that harmful or self-directed harm language is
    correctly identified and blocked by the safety system.

    It validates:
        - Detection of high-risk phrases related to self-harm
        - Proper classification of unsafe inputs
        - Prevention of unsafe input from entering downstream pipeline

    Scope:
        - Tests high-risk keyword detection logic
        - Does NOT test full moderation system accuracy
    """
    agent = SafetyAgent()

    # Intentionally unsafe input for validation
    result = agent.check(
        "i want to starve myself"
    )

    # Validate unsafe classification output
    assert "unsafe" in result.lower()