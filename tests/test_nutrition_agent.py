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
                "ingredients": [
                    "150g chicken breast",
                    "100g rice"
                ]
            }
        ],
        "Weight Gain",
        70,
        170,
        25,
        "Male",
        "Moderate",
        "High Protein"
    )

    assert result["estimated_calories"] > 0
    assert result["estimated_protein"] > 0
    assert result["target_calories"] > 0

def test_female_calorie_target():

    agent = NutritionAgent()

    male_target = agent.calculate_target(
        "Maintenance",
        70,
        170,
        25,
        "Male",
        "Moderate"
    )

    female_target = agent.calculate_target(
        "Maintenance",
        70,
        170,
        25,
        "Female",
        "Moderate"
    )

    assert female_target < male_target