from agents.nutrition_agent import NutritionAgent

def test_nutrition_calculation():
    """
    Tests that nutrition estimates are correctly generated from recipe input.

    This unit test validates that:
    - Calories are calculated and greater than zero
    - Protein values are generated
    - Target calorie calculation is functional

    It uses a minimal synthetic recipe input to ensure the nutrition pipeline
    does not fail and returns meaningful numeric output.
    """

    agent = NutritionAgent()

    # Sample recipe input with simple ingredients
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

    # Validate computed nutrition outputs
    assert result["estimated_calories"] > 0
    assert result["estimated_protein"] > 0
    assert result["target_calories"] > 0


def test_female_calorie_target():
    """
    Ensures that calorie targets are lower for female users
    compared to male users with identical inputs.

    This validates the correctness of the bmr adjustment logic
    inside the target calorie calculation function.
    """

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

    # Female bmr adjustment should result in lower calorie target
    assert female_target < male_target