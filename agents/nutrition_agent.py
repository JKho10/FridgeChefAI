import re
from services.nutrition_api import NutritionAPI


class NutritionAgent:

    def __init__(self):
        self.api = NutritionAPI()

    # -------------------------
    # FOOD CLASSIFICATION (for realism)
    # -------------------------
    FOOD_CLASS = {
        "oil": "fat_dense",
        "butter": "fat_dense",
        "rice": "starch",
        "pasta": "starch",
        "potato": "starch",
        "flour": "starch_dense",
        "chicken": "protein",
        "beef": "protein",
        "pork": "protein",
        "fish": "protein",
        "egg": "protein",
        "milk": "liquid_fat",
        "coconut milk": "liquid_fat",
        "onion": "veg_low",
        "tomato": "veg_low",
        "carrot": "veg_medium"
    }

    # -------------------------
    def extract_qty(self, text):
        if not text:
            return None

        text = str(text).lower()

        patterns = [
            (r"(\d+\.?\d*)\s*kg", 1000),
            (r"(\d+\.?\d*)\s*g", 1),
            (r"(\d+\.?\d*)\s*ml", 1),
            (r"(\d+\.?\d*)\s*cups?", 240),
            (r"(\d+\.?\d*)\s*(tbsp|tablespoons?)", 15),
            (r"(\d+\.?\d*)\s*(tsp|teaspoons?)", 5),
            (r"(\d+\.?\d*)\s*(lb|lbs|pounds?)", 453.592),
            (r"(\d+\.?\d*)\s*(cloves?)", 5),
        ]

        for pattern, multiplier in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1)) * multiplier

        return None

    # -------------------------
    def clean_name(self, text):
        if isinstance(text, dict):
            text = text.get("name") or text.get("ingredient") or ""

        text = str(text).lower()
        text = re.sub(r"\d+", "", text)
        text = re.sub(r"[^a-z ]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    # -------------------------
    def estimate_weight(self, name):
        name = name.lower()

        base = {
            "carrot": 80,
            "onion": 110,
            "garlic": 5,
            "tomato": 120,
            "potato": 150,
            "chicken": 165,
            "beef": 170,
            "rice": 180,
            "pasta": 140,
            "egg": 50,
            "oil": 15,
            "butter": 14,
            "milk": 240,
            "flour": 100,
            "coconut milk": 200
        }

        for k, v in base.items():
            if k in name:
                return v

        return 120

    # -------------------------
    # REALISTIC COOKING MODIFIER
    # -------------------------
    def cooking_modifier(self, recipe_name):
        name = recipe_name.lower()

        if "fried" in name:
            return 1.25
        if "stew" in name:
            return 1.15
        if "curry" in name:
            return 1.20
        if "grilled" in name:
            return 0.95
        if "boiled" in name:
            return 0.90
        if "salad" in name:
            return 0.85

        return 1.0

    # -------------------------
    # OIL / FAT ABSORPTION MODEL
    # -------------------------
    def fat_absorption(self, name, grams, calories):
        if any(x in name.lower() for x in ["fried", "stew", "curry"]):
            calories += grams * 0.12  # absorbed oil estimate
        return calories

    # -------------------------
    def calculate_target(self, goal, weight, height, age, sex, activity_level):

        if sex.lower() == "male":
            bmr = (10 * weight + 6.25 * height - 5 * age + 5)
        else:
            bmr = (10 * weight + 6.25 * height - 5 * age - 161)

        multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very active": 1.9
        }

        tdee = bmr * multipliers.get(activity_level.lower(), 1.55)

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

            ingredients = recipe.get("ingredients", [])

            for ingredient in ingredients:

                if isinstance(ingredient, dict):
                    name = ingredient.get("ingredient") or ingredient.get("name") or ""
                    measure = ingredient.get("measure", "")
                else:
                    name = str(ingredient)
                    measure = ""

                if not name.strip():
                    continue

                grams = self.extract_qty(f"{measure} {name}")
                if grams is None:
                    grams = self.estimate_weight(name)

                nutrition = self.api.get_nutrition_per_100g(self.clean_name(name))

                # 🔥 FIX: NEVER skip missing nutrition
                if not nutrition:
                    nutrition = {
                        "calories": 50,
                        "protein": 1,
                        "carbs": 2,
                        "fat": 1
                    }

                multiplier = grams / 100

                cal = nutrition["calories"] * multiplier
                pro = nutrition["protein"] * multiplier
                carb = nutrition["carbs"] * multiplier
                fat = nutrition["fat"] * multiplier

                # 🔥 realism layers
                cal = self.fat_absorption(name, grams, cal)

                total["calories"] += cal
                total["protein"] += pro
                total["carbs"] += carb
                total["fat"] += fat

            # -------------------------
            # REALISTIC SERVINGS MODEL
            # -------------------------
            base_calories = max(total["calories"], 1)

            if base_calories < 400:
                servings = 1
            elif base_calories < 800:
                servings = 2
            elif base_calories < 1400:
                servings = 3
            else:
                servings = 4

            # apply cooking modifier
            mod = self.cooking_modifier(recipe.get("name", ""))

            total["calories"] *= mod
            total["protein"] *= mod
            total["carbs"] *= mod
            total["fat"] *= mod

            results.append({
                "name": recipe.get("name", "").strip(),

                # TOTAL DISH
                "total_calories": round(total["calories"]),

                # PER SERVING
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
            "dietary_preference": diet_pref or "none"
        }