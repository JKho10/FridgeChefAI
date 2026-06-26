from agents.recipe_agent import RecipeAgent

def test_recipe_generation():
    """
    Tests that recipe generation returns a valid ranked list of recipes.

    This unit test ensures that:
    - the recipe agent returns a list structure
    - at least one recipe is generated for valid ingredients
    - each recipe contains required fields such as name and instructions

    It validates basic functional correctness of the recipe generation pipeline
    without depending on external api accuracy.
    """

    agent = RecipeAgent()

    # Sample ingredient input
    recipes, reason = agent.generate(
        [
            "chicken",
            "rice"
        ],
        "HIGH_PROTEIN_PRIORITY"
    )

    # Validate output structure
    assert isinstance(recipes, list)
    assert len(recipes) > 0
    assert "name" in recipes[0]
    assert "instructions" in recipes[0]


def test_missing_fish_type():
    """
    Tests that ambiguous fish input is handled with a clear error message.

    This unit test ensures the system correctly detects incomplete fish queries
    and returns a clarification response instead of generating invalid recipes.
    """

    agent = RecipeAgent()

    # Ambiguous input intentionally missing fish type
    recipes, message = agent.generate(
        ["fish"],
        "BALANCED_MEALS"
    )

    # Validate graceful failure behavior
    assert recipes == []
    assert "specify fish" in message.lower()