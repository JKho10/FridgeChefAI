class SafetyAgent:
    """
    SafetyAgent performs lightweight rule-based input safety screening.

    This agent runs at the very beginning of the pipeline to ensure that
    user-provided input does not contain harmful, self-injurious,
    or otherwise unsafe content.

    Responsibilities:
        - Detect high-risk harmful intent (e.g., self-harm language)
        - Flag medium-risk concerning content
        - Allow safe input to proceed through downstream agents

    Note:
        This is a deterministic keyword-based filter and is NOT a full
        machine learning moderation system. It should be treated as a
        first-layer safety guard only.
    """
    def check(self, text):
        """
        Analyze user input and classify safety level.

        Classification levels:
            - SAFE: No harmful or concerning content detected
            - WARNING: Potentially unsafe or ambiguous content detected
            - UNSAFE: High-risk content detected; pipeline should stop

        Args:
            text (str): Raw user input

        Returns:
            str: Safety classification result with reason prefix
        """
        text = text.lower()

        risk_keywords = {
            "high": ["starve", "self harm", "kill myself"],
            "medium": ["danger", "hurt"],
        }

        # High risk
        for word in risk_keywords["high"]:
            if word in text:
                return "UNSAFE: High risk content detected"

        # Medium risk
        for word in risk_keywords["medium"]:
            if word in text:
                return "WARNING: Potentially unsafe input"

        # Safe
        return "SAFE: Input validated"
    
    