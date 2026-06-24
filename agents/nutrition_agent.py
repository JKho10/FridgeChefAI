"""
nutrition_agent.py

Nutrition intelligence agent for FridgeChef AI.

This agent:
- Estimates BMR and TDEE
- Computes calorie targets based on user goals
- Calls USDA API per ingredient for real nutrition data
- Aggregates macros safely (no duplicate inflation)
- Produces final nutrition summary for UI

DESIGN PRINCIPLES:
-------------------
✔ No fake food database
✔ No substring matching errors
✔ Real-world nutrient data via USDA API
✔ Clean separation of concerns (service vs agent)
✔ Safe aggregation (no double counting)
"""

from services.nutrition_api import NutritionAPI


class NutritionAgent:
    """
    Nutrition reasoning and aggregation agent.
    """

    def __init__(self):
        self.api = NutritionAPI()

    def analyze(self, recipes, goal, weight=70, height=170, diet_pref="None"):
        """
        Compute full nutrition profile from recipes + user goals.

        Steps:
        1. Estimate BMR (Mifflin-St Jeor formula)
        2. Estimate TDEE
        3. Adjust calories based on goal
        4. Fetch real nutrition per ingredient (USDA API)
        5. Aggregate calories + protein safely
        """

        # -------------------------
        # 1. BMR + TDEE
        # -------------------------
        bmr = 10 * weight + 6.25 * height - 5 * 30 + 5
        tdee = bmr * 1.55

        goal = goal.lower()

        if "lose" in goal:
            target_calories = tdee * 0.8
        elif "gain" in goal:
            target_calories = tdee * 1.15
        else:
            target_calories = tdee

        # -------------------------
        # 2. Protein target
        # -------------------------
        protein_target = weight * 1.6
        protein_note = "Balanced macros"

        if "high protein" in diet_pref.lower():
            protein_target *= 1.2
            protein_note = "High protein adjustment applied"

        if "low carb" in diet_pref.lower():
            protein_note = "Reduced carb emphasis"

        # -------------------------
        # 3. USDA-based aggregation
        # -------------------------
        estimated_calories = 0
        estimated_protein = 0
        seen = set()  # prevent double counting

        for recipe in recipes:
            for item in recipe.get("ingredients", []):

                ingredient_text = item.lower().strip()

                # prevent duplicates across recipes
                if ingredient_text in seen:
                    continue
                seen.add(ingredient_text)

                data = self.api.get_nutrition(ingredient_text)

                if not data:
                    continue

                estimated_calories += data["calories"]
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