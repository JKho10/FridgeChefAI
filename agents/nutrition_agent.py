"""
NutritionAgent (FIXED + STABLE + FAST)

FIXES:
✔ correct servings calculation
✔ removes broken indentation bug
✔ avoids recalculating per ingredient incorrectly
✔ stable USDA scaling
✔ consistent recipe output
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
    def clean_name(self, text):
        text = text.lower()
        text = re.sub(r"\d+", "", text)
        text = re.sub(r"[^a-z ]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    # -------------------------
    def estimate_weight(self, name, qty):
        for key, value in self.UNIT_WEIGHTS.items():
            if key in name:
                return qty if qty else value
        return qty or 100

    # -------------------------
    def calculate_target(self,goal,weight,height,age,sex,activity_level
    ):
        """
        Estimates daily calorie target using
        Mifflin-St Jeor equation.

        Inputs:
        - weight: kg
        - height: cm
        - age: years
        - sex: male/female
        - activity_level: sedentary/light/moderate/active
        """

        if sex.lower() == "male":
            bmr = (
                10 * weight
                + 6.25 * height
                - 5 * age
                + 5
            )

        else:
            bmr = (
                10 * weight
                + 6.25 * height
                - 5 * age
                - 161
            )

        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very active": 1.9
        }

        multiplier = activity_multipliers.get(
            activity_level.lower(),
            1.55
        )

        tdee = bmr * multiplier

        if "lose" in goal.lower():
            return tdee * 0.8

        if "gain" in goal.lower():
            return tdee * 1.15

        return tdee

    # -------------------------
    def analyze(self, recipes, goal, weight, height, age, sex, activity_level, diet_pref="None"):

        target = self.calculate_target(goal, weight, height, age, sex, activity_level)

        results = []

        for recipe in recipes:

            total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
            total_weight = 0

            cleaned_cache = {}

            for ingredient in recipe.get("ingredients", []):

                if ingredient in cleaned_cache:
                    name, qty, grams, nutrition = cleaned_cache[ingredient]
                else:
                    name = self.clean_name(ingredient)

                    if any(x in name for x in self.ZERO_CAL):
                        continue

                    qty = self.extract_qty(ingredient)
                    grams = self.estimate_weight(name, qty)

                    nutrition = self.api.get_nutrition_per_100g(name)

                    cleaned_cache[ingredient] = (name, qty, grams, nutrition)

                if not nutrition:
                    continue

                multiplier = grams / 100

                total["calories"] += nutrition["calories"] * multiplier
                total["protein"] += nutrition["protein"] * multiplier
                total["carbs"] += nutrition["carbs"] * multiplier
                total["fat"] += nutrition["fat"] * multiplier

                total_weight += grams

            # FIXED SERVINGS LOGIC
            servings = max(1, round(total_weight / 500))

            results.append({
                "name": recipe.get("name", "Recipe"),
                "total_calories": round(total["calories"]),
                "calories": round(total["calories"] / servings),
                "protein": round(total["protein"] / servings),
                "carbs": round(total["carbs"] / servings),
                "fat": round(total["fat"] / servings),
                "servings": servings
            })

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