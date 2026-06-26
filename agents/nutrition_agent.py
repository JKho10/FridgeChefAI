import re
from services.nutrition_api import NutritionAPI


class NutritionAgent:

    def __init__(self):
        self.api = NutritionAPI()

    ZERO_CAL = {
        "water", "salt", "pepper", "stock", "broth",
        "spice", "parsley", "thyme", "bay leaf"
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
            (r"(\d+\.?\d*)\s*(lb|lbs|pound|pounds)", 453.592),
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

        mapping = {
            "carrot": 80,
            "onion": 110,
            "garlic": 5,
            "tomato": 120,
            "potato": 150,
            "chicken": 165,
            "beef": 170,
            "rice": 185,
            "egg": 50,
            "oil": 15,
            "flour": 100
        }

        for k, v in mapping.items():
            if k in name:
                return v

        return 100

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

                if not nutrition:
                    continue

                multiplier = grams / 100

                total["calories"] += nutrition["calories"] * multiplier
                total["protein"] += nutrition["protein"] * multiplier
                total["carbs"] += nutrition["carbs"] * multiplier
                total["fat"] += nutrition["fat"] * multiplier

            # -------------------------
            # FIXED SERVINGS LOGIC (STABLE)
            # -------------------------
            # based on food weight, not calories
            ingredient_count = max(len(ingredients), 1)
            servings = min(6, max(2, ingredient_count // 5))

            results.append({
                "name": recipe.get("name", "").strip(),

                # total dish (NEVER scaled twice)
                "total_calories": round(total["calories"]),

                # per serving (safe division only here)
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