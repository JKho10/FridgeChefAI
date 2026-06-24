from agents.recipe_agent import RecipeAgent

def test_recipe_generation():

    """
    Ensures recipe generation returns a ranked list
    of recipes for valid ingredients.
    """

    agent = RecipeAgent()

    recipes, reason = agent.generate(
        [
            "chicken",
            "rice"
        ],
        "HIGH_PROTEIN_PRIORITY"
    )

    assert isinstance(
        recipes,
        list
    )

    assert len(recipes) > 0

    assert "name" in recipes[0]

    assert "instructions" in recipes[0]

def test_missing_fish_type():

    """
    Ensures ambiguous ingredient input is handled
    with a clarification message.
    """

    agent = RecipeAgent()

    recipes, message = agent.generate(
        [
            "fish"
        ],
        "BALANCED_MEALS"
    )

    assert recipes == []

    assert "specify fish" in message.lower()