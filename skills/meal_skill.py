def meal_planning_skill(ingredients, goal):
    """
    selects a meal planning strategy based on the user's goal.

    this function determines how recipes should be prioritized by the system
    depending on whether the user wants to lose weight, gain weight, or maintain
    a balanced diet.

    args:
        ingredients (list): list of user-provided ingredients (not used directly in logic)
        goal (str): user's dietary goal (e.g., lose weight, gain weight, maintenance)

    returns:
        str: strategy label used by downstream recipe ranking system

    possible returns:
        - high_protein_priority: prioritize protein-dense meals for muscle gain
        - low_calorie_priority: prioritize lower-calorie meals for weight loss
        - balanced_meals: default neutral strategy for maintenance
    """
    goal = goal.lower()

    if "gain" in goal:
        return "HIGH_PROTEIN_PRIORITY"

    if "lose" in goal:
        return "LOW_CALORIE_PRIORITY"

    return "BALANCED_MEALS"