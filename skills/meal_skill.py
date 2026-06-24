def meal_planning_skill(ingredients, goal):

    """
    Selects a meal planning strategy based on the user's goal.

    Returns one of:
    - HIGH_PROTEIN_PRIORITY
    - LOW_CALORIE_PRIORITY
    - BALANCED_MEALS
    """

    goal = goal.lower()

    if "gain" in goal:
        return "HIGH_PROTEIN_PRIORITY"

    if "lose" in goal:
        return "LOW_CALORIE_PRIORITY"

    return "BALANCED_MEALS"