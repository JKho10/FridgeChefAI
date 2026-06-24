class SafetyAgent:

    """
    Input safety checker.

    Runs before other agents in the pipeline.

    Responsibilities:
    - Checks user input for unsafe or harmful content
    - Blocks execution for high-risk inputs
    - Flags potentially concerning inputs
    """

    def check(self, text):

        """
        Performs a rule-based keyword check on user input.

        Returns:
        - SAFE: input can proceed through pipeline
        - WARNING: potentially concerning content
        - UNSAFE: execution should be blocked
        """

        text = text.lower()

        risk_keywords = {
            "high": ["starve", "self harm", "kill myself"],
            "medium": ["danger", "hurt"],
        }

        for word in risk_keywords["high"]:
            if word in text:
                return "UNSAFE: High risk content detected"

        for word in risk_keywords["medium"]:
            if word in text:
                return "WARNING: Potentially unsafe input"

        return "SAFE: Input validated"
    
    