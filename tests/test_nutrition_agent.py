from agents.nutrition_agent import NutritionAgent

def test_nutrition_calculation():
    """
    Unit test for NutritionAgent nutrition estimation pipeline.

    This test validates that the NutritionAgent.analyze() method correctly
    processes a synthetic recipe input and produces meaningful nutrition output.

    It ensures:
        - Estimated calories are computed and greater than zero
        - Estimated protein values are computed and greater than zero
        - Target daily calorie calculation is functional and valid

    Scope:
        - Tests end-to-end nutrition calculation logic
        - Does NOT validate USDA API accuracy
        - Does NOT validate ingredient parsing correctness in edge cases
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
    Unit test for gender-based calorie target calculation logic.

    This test ensures that the BMR-based calorie estimation correctly
    differentiates between male and female metabolic calculations.

    It validates:
        - Both male and female calorie targets are computed
        - Female calorie target is lower than male for identical inputs

    Scope:
        - Tests BMR formula correctness
        - Does NOT validate activity level multipliers independently
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