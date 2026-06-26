import re
from services.nutrition_api import NutritionAPI


class NutritionAgent:
    """
    nutrition agent
    responsible for estimating recipe nutrition values using:
    1. external nutrition api (preferred)
    2. deterministic fallback database
    3. safe default values

    also handles:
    - ingredient parsing
    - unit conversion
    - weight estimation
    - cooking effect adjustments
    - serving normalization
    """

    def __init__(self):
        self.api = NutritionAPI()

        # deterministic fallback database (NO randomness ever)
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

    # Text processing
    def clean_name(self, text):
        """
        normalize ingredient text into clean lowercase keyword form
        removes numbers, symbols, and extra whitespace
        """
        if isinstance(text, dict):
            text = text.get("name") or text.get("ingredient") or ""

        text = str(text).lower()
        text = re.sub(r"\d+", "", text)
        text = re.sub(r"[^a-z ]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def extract_qty(self, text):
        """
        extract ingredient quantity and convert to grams/ml equivalent
        returns float or None if no match found
        """
        if not text:
            return None

        text = str(text).lower()

        text = text.replace("-", " ")
        text = text.replace("¼", "0.25")
        text = text.replace("¾", "0.75")

        def frac_to_float(m):
            whole = float(m.group(1))
            num, denom = map(float, m.group(2).split("/"))
            return str(whole + (num / denom))

        text = re.sub(r"(\d+)\s+(\d/\d+)", frac_to_float, text)
        
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

    # Weight estimation
    def estimate_weight(self, name):
        """
        estimate ingredient weight when no explicit measurement is provided
        """
        name = name.lower()

        # cooked/raw assumptions (important for accuracy)
        cooked_defaults = {
            "rice": 180,      # cooked portion baseline
            "pasta": 140,
            "chicken": 165,   # raw edible portion estimate
            "beef": 170,
        }

        for k, v in cooked_defaults.items():
            if k in name:
                return v

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


    # Cooking effects
    def cooking_modifier(self, recipe_name):
        """
        adjust calories based on cooking method
        """
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

    def fat_absorption(self, name, grams, calories):
        """
        add absorbed cooking fat for certain cooking styles
        """
        if any(x in name.lower() for x in ["fried", "stew", "curry"]):
            calories += grams * 0.12
        return calories

    # Target calculation
    def calculate_target(self, goal, weight, height, age, sex, activity_level):
        """
        calculate daily calorie target using tdee model
        """
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
        """
        estimate number of servings based on total calories
        """
        if calories < 400:
            return 1
        elif calories < 800:
            return 2
        elif calories < 1400:
            return 3
        return 4

    # Nutrition lookup
    def get_nutrition(self, name):
        """
        resolve nutrition data using:
        1. api
        2. fallback dictionary
        3. safe default
        """
        clean = self.clean_name(name)

        api_result = self.api.get_nutrition_per_100g(clean)
        if api_result:
            return api_result

        for key, value in self.FALLBACK_NUTRITION.items():
            if key in clean:
                return value

        return {"calories": 60, "protein": 2, "carbs": 5, "fat": 2}

    # main analysis
    def analyze(
        self,
        recipes,
        goal,
        weight,
        height,
        age,
        sex,
        activity_level,
        diet_pref="None"
    ):
        """
        compute nutrition for a list of recipes

        returns:
        - per recipe macros
        - estimated servings
        - top recipe summary
        - user calorie target
        """
        target = self.calculate_target(goal, weight, height, age, sex, activity_level)

        results = []

        for recipe in recipes:

            total = {
                "calories": 0,
                "protein": 0,
                "carbs": 0,
                "fat": 0
            }

            ingredients = recipe.get("ingredients", [])

            for ingredient in ingredients:

                name = ingredient.get("ingredient") if isinstance(ingredient, dict) else str(ingredient)
                measure = ingredient.get("measure", "") if isinstance(ingredient, dict) else ""

                if not name:
                    continue

                grams = self.extract_qty(f"{measure} {name}") or self.estimate_weight(name)

                nutrition = self.get_nutrition(name)

                factor = grams / 100

                cal = nutrition["calories"] * factor
                pro = nutrition["protein"] * factor
                carb = nutrition["carbs"] * factor
                fat = nutrition["fat"] * factor

                cal = self.fat_absorption(name, grams, cal)

                total["calories"] += cal
                total["protein"] += pro
                total["carbs"] += carb
                total["fat"] += fat

            total["calories"] *= self.cooking_modifier(recipe.get("name", ""))

            servings = self.estimate_servings(total["calories"])

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
            "dietary_preference": diet_pref or "none"
        }