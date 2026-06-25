import re
from services.nutrition_api import NutritionAPI


class NutritionAgent:

    def __init__(self):
        self.api = NutritionAPI()

    # --------------------------------------------------
    # QUANTITY EXTRACTION (FIXED)
    # --------------------------------------------------
    def extract_qty(self, text):
        text = text.lower()

        # eggs (FIXED CRITICAL BUG)
        if "egg" in text:
            match = re.search(r"(\d+)", text)
            count = int(match.group(1)) if match else 1
            return count * 50  # ~50g per egg

        # cups (FIXED MULTIPLIER)
        match = re.search(r"(\d+)\s*cup", text)
        if match:
            return int(match.group(1)) * 180
        if "cup" in text:
            return 180

        # tablespoons
        match = re.search(r"(\d+)\s*(tbsp|tablespoon)", text)
        if match:
            return int(match.group(1)) * 15
        if "tbsp" in text or "tablespoon" in text:
            return 15

        # teaspoons
        match = re.search(r"(\d+)\s*(tsp|teaspoon)", text)
        if match:
            return int(match.group(1)) * 5
        if "tsp" in text or "teaspoon" in text:
            return 5

        # grams / kg / oz
        match = re.search(r"(\d+\.?\d*)\s*(g|kg|oz)", text)
        if match:
            value = float(match.group(1))
            unit = match.group(2)

            if unit == "kg":
                return value * 1000
            if unit == "oz":
                return value * 28.35
            return value

        # fallback
        return 100

    # --------------------------------------------------
    # CLEAN INGREDIENT NAME
    # --------------------------------------------------
    def clean_name(self, text):
        text = text.lower()

        remove_words = [
            "g", "kg", "oz", "ml",
            "cup", "cups",
            "tbsp", "tsp",
            "tablespoon", "teaspoon",
            "large", "small", "medium",
            "whole", "fresh",
            "chopped", "diced",
            "sliced"
        ]

        for w in remove_words:
            text = text.replace(w, "")

        text = re.sub(r"\d+", "", text)
        text = re.sub(r"[^a-z ]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    # --------------------------------------------------
    # MAIN ANALYSIS (FIXED OUTPUT SCHEMA)
    # --------------------------------------------------
    def analyze(self, recipes, goal, weight=70, height=170, diet_pref="None"):

        # ------------------------------
        # CALORIE TARGET
        # ------------------------------
        bmr = 10 * weight + 6.25 * height - 5 * 30 + 5
        tdee = bmr * 1.55

        goal = goal.lower()
        if "lose" in goal:
            target = tdee * 0.8
        elif "gain" in goal:
            target = tdee * 1.15
        else:
            target = tdee

        recipe_results = []

        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0

        # ------------------------------
        # PER RECIPE
        # ------------------------------
        for recipe in recipes:

            calories = 0
            protein = 0
            carbs = 0
            fat = 0

            ingredients = recipe.get("ingredients", [])

            for item in ingredients:
                qty = self.extract_qty(item)
                clean = self.clean_name(item)

                if not clean:
                    continue

                nutrition = self.api.get_nutrition_per_100g(clean)
                if not nutrition:
                    continue

                scale = qty / 100

                calories += nutrition["calories"] * scale
                protein += nutrition["protein"] * scale
                carbs += nutrition["carbs"] * scale
                fat += nutrition["fat"] * scale

            servings = 4

            c = round(calories / servings)
            p = round(protein / servings)
            cb = round(carbs / servings)
            f = round(fat / servings)

            recipe_results.append({
                "name": recipe.get("name", "Recipe"),
                "calories": c,
                "protein": p,
                "carbs": cb,
                "fat": f
            })

            # accumulate totals for UI FIX
            total_calories += c
            total_protein += p
            total_carbs += cb
            total_fat += f

        # ------------------------------
        # FINAL RETURN (FIXED FOR UI)
        # ------------------------------
        return {
            "target_calories": round(target),

            # UI FIX (THIS SOLVES YOUR 0 kcal BUG)
            "estimated_calories": round(total_calories),
            "estimated_protein": round(total_protein),
            "estimated_carbs": round(total_carbs),
            "estimated_fat": round(total_fat),

            "recipes": recipe_results,
            "dietary_preference": diet_pref,
            "goal": goal
        }