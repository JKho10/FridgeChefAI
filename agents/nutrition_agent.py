import re
from services.nutrition_api import NutritionAPI


class NutritionAgent:

    def __init__(self):
        self.api = NutritionAPI()

        self.FALLBACK_NUTRITION = {
            "chicken": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6},
            "beef": {"calories": 250, "protein": 26, "carbs": 0, "fat": 17},
            "pork": {"calories": 242, "protein": 27, "carbs": 0, "fat": 14},
            "fish": {"calories": 200, "protein": 22, "carbs": 0, "fat": 12},
            "egg": {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11},
            "rice": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3},
            "pasta": {"calories": 131, "protein": 5, "carbs": 25, "fat": 1.1},
            "potato": {"calories": 77, "protein": 2, "carbs": 17, "fat": 0.1},
            "oil": {"calories": 884, "protein": 0, "carbs": 0, "fat": 100},
            "butter": {"calories": 717, "protein": 0.9, "carbs": 0.1, "fat": 81},
            "milk": {"calories": 60, "protein": 3.2, "carbs": 5, "fat": 3.3},
            "flour": {"calories": 364, "protein": 10, "carbs": 76, "fat": 1},
            "coconut milk": {"calories": 230, "protein": 2, "carbs": 6, "fat": 24},
        }

    # ---------------- TEXT CLEANING ----------------

    def clean_name(self, text):
        if isinstance(text, dict):
            text = text.get("name") or text.get("ingredient") or ""

        text = str(text).lower()
        text = re.sub(r"\d+", "", text)
        text = re.sub(r"[^a-z ]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    # ---------------- QTY PARSING ----------------

    def extract_qty(self, text):
        if not text:
            return None

        text = str(text).lower().replace("-", " ")
        text = text.replace("¼", "0.25").replace("¾", "0.75")

        def frac_to_float(m):
            whole = float(m.group(1))
            num, denom = map(float, m.group(2).split("/"))
            return str(whole + (num / denom))

        text = re.sub(r"(\d+)\s+(\d/\d+)", frac_to_float, text)

        patterns = [
            (r"(\d+\.?\d*)\s*kg", 1000),
            (r"(\d+\.?\d*)\s*g", 1),
            (r"(\d+\.?\d*)\s*ml", 1),
            (r"(\d+\.?\d*)\s*cups?", 200),
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

    # ---------------- WEIGHT ESTIMATION ----------------

    def estimate_weight(self, name):
        name = name.lower()

        if "whole chicken" in name:
            return 1200
        if "chicken" in name:
            return 165
        if "rice" in name:
            return 180
        if "pasta" in name:
            return 140

        base = {
            "carrot": 80,
            "onion": 110,
            "garlic": 5,
            "tomato": 120,
            "potato": 150,
            "egg": 50,
            "oil": 15,
            "butter": 14,
            "milk": 240,
            "flour": 100,
            "coconut milk": 200,
        }

        for k, v in base.items():
            if k in name:
                return v

        return 120

    # ---------------- COOKING ----------------

    def cooking_modifier(self, name):
        name = name.lower()

        if "fried" in name:
            return 1.15
        if "stew" in name:
            return 1.10
        if "curry" in name:
            return 1.10
        if "grilled" in name:
            return 0.95
        if "boiled" in name:
            return 0.90

        return 1.0

    # ---------------- FAT ABSORPTION ----------------

    def fat_absorption(self, name, grams, calories):
        if any(x in name.lower() for x in ["fried", "stew", "curry"]):
            calories += grams * 0.08
        return calories

    # ---------------- TARGET ----------------

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
            "very active": 1.9,
        }

        tdee = bmr * multipliers.get(activity_level.lower(), 1.55)

        if "lose" in goal.lower():
            return tdee * 0.8
        if "gain" in goal.lower():
            return tdee * 1.15

        return tdee

    def estimate_servings(self, calories):
        if calories < 500:
            return 1
        if calories < 900:
            return 2
        if calories < 1400:
            return 3
        return 4

    # ---------------- NUTRITION LOOKUP ----------------

    def get_nutrition(self, name):
        clean = self.clean_name(name)

        api_result = self.api.get_nutrition_per_100g(clean)
        if api_result:
            return api_result

        for key, value in self.FALLBACK_NUTRITION.items():
            if key in clean:
                return value

        return {"calories": 60, "protein": 2, "carbs": 5, "fat": 2}

    # ---------------- MAIN ANALYSIS ----------------

    def analyze(self, recipes, goal, weight, height, age, sex, activity_level, diet_pref="None"):

        target = self.calculate_target(goal, weight, height, age, sex, activity_level)

        results = []

        for recipe in recipes:

            total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}

            ingredients = recipe.get("ingredients", [])

            for ingredient in ingredients:

                name = ingredient.get("ingredient") if isinstance(ingredient, dict) else str(ingredient)
                measure = ingredient.get("measure", "") if isinstance(ingredient, dict) else ""

                grams = self.extract_qty(f"{measure} {name}")

                if grams is None:
                    grams = self.estimate_weight(name)

                name_lower = name.lower()

                # FIX: rice/pasta normalization
                if ("rice" in name_lower or "pasta" in name_lower) and grams > 200:
                    grams *= 0.33

                nutrition = self.get_nutrition(name)

                factor = grams / 100.0

                carbs_value = nutrition["carbs"] * factor

                # FIX: per-ingredient carb safety clamp
                if "rice" in name_lower or "pasta" in name_lower:
                    carbs_value = min(carbs_value, 250)

                total["calories"] += nutrition["calories"] * factor
                total["protein"] += nutrition["protein"] * factor
                total["carbs"] += carbs_value
                total["fat"] += nutrition["fat"] * factor

            total["calories"] *= self.cooking_modifier(recipe.get("name", ""))

            # FIX: single clean servings logic
            servings = recipe.get("servings")

            if not servings:
                servings = self.estimate_servings(total["calories"])
            
            servings = max(1, int(servings))

            # FIX: final carb sanity cap (single consistent rule)
            carbs_per_serving = total["carbs"] / servings
            if carbs_per_serving > 120:
                total["carbs"] = 120 * servings

            results.append({
                "name": recipe.get("name", "").strip(),
                "total_calories": round(total["calories"]),
                "calories": round(total["calories"] / servings),
                "protein": round(total["protein"] / servings),
                "carbs": round(total["carbs"] / servings),
                "fat": round(total["fat"] / servings),
                "servings": servings
            })

        top = results[0] if results else {}

        return {
            "target_calories": round(target),
            "estimated_calories": top.get("calories", 0),
            "estimated_protein": top.get("protein", 0),
            "estimated_carbs": top.get("carbs", 0),
            "estimated_fat": top.get("fat", 0),
            "recipes": results,
            "goal": goal,
            "dietary_preference": diet_pref
        }