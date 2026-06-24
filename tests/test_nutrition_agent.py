from agents.nutrition_agent import NutritionAgent

def test_nutrition_calculation():

    """
    Ensures nutrition estimates are generated
    from recipe input.
    """
    
    agent = NutritionAgent()

    result = agent.analyze(
    [
        {
            "ingredients": ["chicken"]
        }
    ],
        "Weight Gain"
    )

    assert result["estimated_calories"] > 0
    assert result["estimated_protein"] > 0