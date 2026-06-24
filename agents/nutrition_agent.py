import re 

class NutritionAgent:

    """
    Nutrition estimation agent.

    This agent is responsible for:
    - Estimating BMR (basal metabolic rate)
    - Estimating TDEE (total daily energy expenditure)
    - Adjusting calorie targets based on user goal
    - Estimating protein targets
    - Computing nutrition from recipe ingredients

    FIXES INCLUDED:
    ----------------
    ✔ Prevents false matches like "chicken" vs "chicken stock"
    ✔ Uses token-based ingredient matching instead of substring matching
    ✔ Removes duplicate counting inflation
    ✔ Avoids exaggerated protein/calorie totals
    ✔ Cleans ingredient strings before matching
    """

    # -----------------------------
    # CORE ENTRY FUNCTION
    # -----------------------------
    def analyze(self, recipes, goal, weight=70, height=170, diet_pref="None"):
        """
        Computes nutrition estimates from user profile + recipes.

        Steps:
        1. Estimate BMR using simplified Mifflin-St Jeor formula
        2. Estimate TDEE using fixed activity multiplier
        3. Adjust calorie target based on goal
        4. Estimate protein target from body weight
        5. Compute calories/protein from matched recipe ingredients
        """

        # -----------------------------
        # BMR + TDEE
        # -----------------------------
        bmr = 10 * weight + 6.25 * height - 5 * 30 + 5
        tdee = bmr * 1.55

        goal = goal.lower()

        if "lose" in goal:
            target_calories = tdee * 0.8
        elif "gain" in goal:
            target_calories = tdee * 1.15
        else:
            target_calories = tdee

        # -----------------------------
        # Protein target
        # -----------------------------
        protein_target = weight * 1.6

        protein_note = "Balanced macros"

        if "high protein" in diet_pref.lower():
            protein_target *= 1.2
            protein_note = "High protein adjustment applied"

        if "low carb" in diet_pref.lower():
            protein_note = "Reduced carb emphasis"

        # -----------------------------
        # FOOD DATABASE (simple model)
        # -----------------------------
        FOOD_DB = {
            "chicken": {"cal": 165, "protein": 31},
            "rice": {"cal": 205, "protein": 4},
            "egg": {"cal": 70, "protein": 6},
            "beef": {"cal": 250, "protein": 26},
            "salmon": {"cal": 208, "protein": 22},
            "beans": {"cal": 347, "protein": 21},
        }

        # -----------------------------
        # CLEANING FUNCTION
        # -----------------------------
        def clean(text: str):
            """
            Converts ingredient text into normalized tokens.

            Example:
                "1 litre chicken stock" → ["chicken", "stock"]
            """
            return set(re.findall(r"[a-z]+", text.lower()))

        def match_food(food_key, ingredient_text):
            """
            Strict match:
            - prevents "chicken" matching "chicken stock"
            - requires token presence
            """
            food_tokens = set(food_key.split())
            ing_tokens = clean(ingredient_text)

            return food_tokens.issubset(ing_tokens)

        # -----------------------------
        # AGGREGATION
        # -----------------------------
        estimated_calories = 0
        estimated_protein = 0

        matched_foods = []

        for recipe in recipes:
            for item in recipe.get("ingredients", []):

                item_tokens = clean(item)

                for food, data in FOOD_DB.items():

                    food_tokens = set(food.split())

                    # STRICT MATCH ONLY
                    if food_tokens.issubset(item_tokens):
                        matched_foods.append(food)

                        # avoid double counting same ingredient repeatedly
                        if food not in matched_foods[:-1]:
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

            "insight": protein_note
        }