from agents.recipe_agent import RecipeAgent

def test_recipe_generation():
    """
    End-to-end unit test for recipe generation.

    This test validates the core behavior of the RecipeAgent.generate() method,
    ensuring that valid ingredient inputs produce usable recipe outputs.

    It verifies:
        - The output is a list of recipes
        - At least one recipe is generated for valid inputs
        - Each recipe contains required fields for downstream usage:
            - name (recipe title)
            - instructions (cooking steps)

    Scope:
        - Tests functional correctness of recipe generation logic
        - Does NOT validate external MCP API correctness
        - Does NOT validate ranking accuracy or scoring quality
    """

    agent = RecipeAgent()

    # Provide sample valid ingredients for recipe generation
    recipes, reason = agent.generate(
        [
            "chicken",
            "rice"
        ],
        "HIGH_PROTEIN_PRIORITY"
    )

    # Validate output type and minimal structure integrity
    assert isinstance(recipes, list)
    assert len(recipes) > 0
    assert "name" in recipes[0]
    assert "instructions" in recipes[0]


def test_missing_fish_type():
    """
    Unit test for input validation behavior in RecipeAgent.

    This test ensures that ambiguous fish-related input is handled safely
    by requesting clarification instead of generating unreliable recipes.

    Expected behavior:
        - If "fish" is provided without a specific type (e.g., salmon, tuna),
          the system should not proceed with recipe generation.
        - The function should return an empty recipe list.
        - A clear explanation message should be returned indicating the issue.

    Scope:
        - Tests input validation logic only
        - Does NOT test recipe ranking or MCP API behavior
    """

    agent = RecipeAgent()

    # Ambiguous input without fish type specification
    recipes, message = agent.generate(
        ["fish"],
        "BALANCED_MEALS"
    )

    # Validate safe failure behavior
    assert recipes == []
    assert "specify fish" in message.lower()