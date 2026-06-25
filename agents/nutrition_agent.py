"""
NutritionAgent 

GOAL:
- Prevent calorie inflation
- Ensure stable USDA scaling
- Use ONLY top recipe for daily plan
- Produce consistent per-serving + total outputs

KEY DESIGN:
- USDA provides per-100g macros
- We convert ingredients → grams → nutrition
- We estimate servings from total weight
"""

import re
from services.nutrition_api import NutritionAPI


class NutritionAgent:

    def __init__(self):
        self.api = NutritionAPI()

    ZERO_CAL = {
        "water", "salt", "pepper", "stock", "broth",
        "spice", "parsley", "thyme"
    }

    # -------------------------
    # GRAM ESTIMATION RULES
    # -------------------------
    UNIT_WEIGHTS = {
        "whole chicken": 1200,
        "chicken": 150,
        "rice": 100,
        "bread": 40,
        "chocolate": 20,
        "corn": 100,
        "sweetcorn": 100,
        "oil": 15,
        "chorizo": 225,
        "onion": 120,
        "garlic": 10,
    }

    # -------------------------
    # CONVERSION
    # -------------------------
    def extract_qty(self, text):
        text = text.lower()

        match = re.search(r"(\d+\.?\d*)\s*g", text)
        if match:
            return float(match.group(1))

        match = re.search(r"(\d+\.?\d*)\s*kg", text)
        if match:
            return float(match.group(1)) * 1000

        match = re.search(r"(\d+)\s*cups?", text)
        if match:
            return int(match.group(1)) * 180

        match = re.search(r"(\d+)\s*(tbsp|tablespoon)", text)
        if match:
            return int(match.group(1)) * 15

        return None

    # -------------------------
    # CLEAN
    # -------------------------
    def clean_name(self, text):
        text = text.lower()
        text = re.sub(r"\d+", "", text)
        text = re.sub(r"[^a-z ]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    # -------------------------
    # WEIGHT ESTIMATION
    # -------------------------
    def estimate_weight(self, name, qty):
        for key, value in self.UNIT_WEIGHTS.items():
            if key in name:
                return qty if qty else value
        return qty or 100

    # -------------------------
    # TARGET CALORIES
    # -------------------------
    def calculate_target(self, goal, weight, height):
        bmr = 10 * weight + 6.25 * height - 5 * 30 + 5
        tdee = bmr * 1.55

        if "lose" in goal.lower():
            return tdee * 0.8
        if "gain" in goal.lower():
            return tdee * 1.15
        return tdee

    # -------------------------
    # MAIN ANALYSIS
    # -------------------------
    def analyze(self, recipes, goal, weight=70, height=170, diet_pref="None"):

        target = self.calculate_target(goal, weight, height)

        results = []

        for recipe in recipes:

            total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
            total_weight = 0

            for ingredient in recipe.get("ingredients", []):

                name = self.clean_name(ingredient)

                if any(z in name for z in self.ZERO_CAL):
                    continue

                qty = self.extract_qty(ingredient)
                grams = self.estimate_weight(name, qty)

                nutrition = self.api.get_nutrition_per_100g(name)
                if not nutrition:
                    continue

                total_weight += grams

                m = grams / 100

                total["calories"] += nutrition["calories"] * m
                total["protein"] += nutrition["protein"] * m
                total["carbs"] += nutrition["carbs"] * m
                total["fat"] += nutrition["fat"] * m

            # -------------------------
            # SERVINGS (FIXED LOGIC)
            # -------------------------
            servings = max(1, round(total_weight / 500))

            per_serving = {
                "name": recipe.get("name", "Recipe"),
                "total_calories": round(total["calories"]),
                "calories": round(total["calories"] / servings),
                "protein": round(total["protein"] / servings),
                "carbs": round(total["carbs"] / servings),
                "fat": round(total["fat"] / servings),
                "servings": servings
            }

            results.append(per_serving)

        # ONLY TOP RECIPE COUNTS
        selected = results[0] if results else {}

        return {
            "target_calories": round(target),

            "estimated_calories": selected.get("calories", 0),
            "estimated_protein": selected.get("protein", 0),
            "estimated_carbs": selected.get("carbs", 0),
            "estimated_fat": selected.get("fat", 0),

            "recipes": results,
            "goal": goal,
            "dietary_preference": diet_pref
        }