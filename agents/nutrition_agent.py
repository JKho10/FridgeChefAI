class NutritionAgent:

    """
    Nutrition estimation agent.

    Responsibilities:
    - Estimates basal metabolic rate (BMR)
    - Estimates total daily energy expenditure (TDEE)
    - Adjusts calorie targets based on user goal
    - Estimates protein requirements
    - Approximates nutrition from selected recipes using a simple food table

    This is a rule-based educational model and not intended for medical use.
    """

    def analyze(self, recipes, goal, weight=70, height=170, diet_pref="None"):

        """
        Computes nutrition estimates based on user profile and recipes.

        Steps:
        1. Estimate BMR using simplified Mifflin-St Jeor formula
        2. Estimate TDEE using fixed activity multiplier
        3. Adjust calorie target based on goal
        4. Estimate protein target from body weight
        5. Approximate calories and protein from recipe ingredients
        6. Return summary metrics
        """

        # Simplified Mifflin-St Jeor inspired estimate.
        # Age and biological sex are fixed assumptions 
        # because this prototype focuses on agent workflow.
        
        bmr = 10 * weight + 6.25 * height - 5 * 30 + 5

        # Default moderate activity assumption
        tdee = bmr * 1.55

        # Goal Adjustment
        goal = goal.lower()

        if "lose" in goal:
            target_calories = tdee * 0.8
        elif "gain" in goal:
            target_calories = tdee * 1.15
        else:
            target_calories = tdee

        """
        Protein estimation:
        Based on body weight with optional adjustment
        for high-protein dietary preference.
        """
        protein_target = weight * 1.6
        
        protein_multiplier_note = "Balanced macros"

        if "high protein" in diet_pref.lower():
            protein_target *= 1.2

        if "low carb" in diet_pref.lower():
            protein_multiplier_note = "Reduced carb emphasis"
        else:
            protein_multiplier_note = "Balanced macros"

        """
        Lightweight food database.

        A production version could replace this
        with a nutrition API or MCP nutrition tool.
        """
        estimated_calories = 0
        estimated_protein = 0

        FOOD_DB = {
            "chicken": {"cal": 165, "protein": 31},
            "rice": {"cal": 205, "protein": 4},
            "egg": {"cal": 70, "protein": 6},
            "beef": {"cal": 250, "protein": 26},
            "salmon": {"cal": 208, "protein": 22},
        }

        for recipe in recipes:
            for item in recipe.get("ingredients", []):
                item = item.lower()

                for food, data in FOOD_DB.items():
                    if food in item:
                        estimated_calories += data["cal"]
                        estimated_protein += data["protein"]

        return {
            "bmr": round(bmr),
            "tdee": round(tdee),
            "target_calories": round(target_calories),

            "estimated_calories": round(estimated_calories),
            "estimated_protein": round(estimated_protein),

            "protein_target": round(protein_target),

            "dietary_preference": diet_pref,
            "goal": goal,
            
            "insight": protein_multiplier_note
        }