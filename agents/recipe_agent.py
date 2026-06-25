from mcp_server.server import MealMCPServer
import re


class RecipeAgent:

    def __init__(self):
        self.mcp = MealMCPServer()

    # -----------------------------
    # NORMALIZATION
    # -----------------------------
    def normalize(self, text) -> str:
        if isinstance(text, dict):
            text = text.get("name") or text.get("ingredient") or str(text)

        text = str(text).lower()
        text = re.sub(r"[^a-z ]", "", text)
        return text.strip()

    def is_match(self, user_item: str, recipe_item: str) -> bool:
        return set(self.normalize(user_item).split()) == set(self.normalize(recipe_item).split())

    # -----------------------------
    # GENERATION
    # -----------------------------
    def generate(self, ingredients, strategy, diet_pref=None):

        diet_pref = (diet_pref or "none").strip().lower()
        strategy = (strategy or "").strip()

        if not ingredients:
            return [], "No ingredients provided."

        ingredients = [self.normalize(x) for x in ingredients if x.strip()]

        fish_aliases = {"salmon", "tuna", "cod", "tilapia"}
        if "fish" in ingredients and not any(x in ingredients for x in fish_aliases):
            return [], "Please specify fish type."

        meal_pool = {}

        for ingredient in ingredients:
            try:
                data = self.mcp.call_tool("search_meals", ingredient=ingredient)
            except Exception:
                continue

            if isinstance(data, dict) and data.get("meals"):
                for meal in data["meals"][:10]:
                    meal_pool[meal["idMeal"]] = meal

        if not meal_pool:
            return [], "No recipes found."

        ranked = self.rank_recipes(meal_pool.values(), ingredients)

        # IMPORTANT FIX: always guarantee list stability
        if not ranked:
            return [], "No valid ranked recipes."

        filtered = ranked[:3] if len(ranked) >= 3 else ranked

        return [
            {
                "name": r["name"],
                "image": r["image"],
                "ingredients": r["ingredients"],
                "instructions": r["instructions"],
                "coverage": r["coverage"],
                "matched": r["matched"],
                "missing": r["missing"],
                "additional": r["additional"],
                "country": r.get("country", "Unknown"),
                "rank": i + 1,
                "why": self.explain(strategy, r, diet_pref)
            }
            for i, r in enumerate(filtered)
        ], "Recipes ranked using ingredient intelligence."

    # -----------------------------
    # RANKING
    # -----------------------------
    def rank_recipes(self, meals, ingredients):

        results = []
        user_ingredients = sorted(set(self.normalize(i) for i in ingredients))

        for meal in meals:

            details = None
            try:
                details = self.mcp.call_tool("get_meal", meal_id=meal["idMeal"])
            except Exception:
                continue

            if not isinstance(details, dict) or not details.get("meals"):
                continue

            recipe = details["meals"][0]
            extracted = self.extract(recipe)

            recipe_ingredients = [
                self.normalize(i["ingredient"])
                for i in extracted
            ]

            matched = []
            missing = []

            for ui in user_ingredients:
                if any(self.is_match(ui, ri) for ri in recipe_ingredients):
                    matched.append(ui)
                else:
                    missing.append(ui)

            matched = sorted(set(matched))
            missing = sorted(set(missing))

            additional = sorted(set(
                ri for ri in recipe_ingredients
                if not any(self.is_match(ri, ui) for ui in user_ingredients)
            ))

            coverage = round(len(matched) / len(user_ingredients) * 100) if user_ingredients else 0
            score = coverage + (len(matched) * 5)

            results.append({
                "score": score,
                "name": recipe["strMeal"].strip().lower(),
                "image": recipe["strMealThumb"],
                "ingredients": [
                    {
                        "name": i["ingredient"].lower(),
                        "ingredient": i["ingredient"].lower(),
                        "measure": i["measure"]
                    }
                    for i in extracted
                ],
                "instructions": recipe["strInstructions"],
                "coverage": coverage,
                "matched": matched,
                "missing": missing,
                "additional": additional,
                "country": recipe.get("strArea", "Unknown")
            })

        return sorted(results, key=lambda x: x["score"], reverse=True)

    # -----------------------------
    # EXTRACT
    # -----------------------------
    def extract(self, meal):

        items = []

        for i in range(1, 21):
            ingredient = meal.get(f"strIngredient{i}")
            measure = meal.get(f"strMeasure{i}")

            if ingredient and ingredient.strip():
                items.append({
                    "ingredient": ingredient.strip().lower(),
                    "measure": (measure or "").strip().lower(),
                    "raw": f"{measure} {ingredient}".strip()
                })

        return items

    # -----------------------------
    # EXPLAIN
    # -----------------------------
    def explain(self, strategy, recipe, diet_pref=None):

        diet_line = f"Diet preference: {diet_pref}\n" if diet_pref and diet_pref != "none" else ""

        return (
            f"⭐ Recommended for {strategy}\n"
            f"{diet_line}"
            f"Match: {recipe['coverage']}%\n"
            f"Uses: {', '.join(recipe['matched']) or 'None'}\n"
            f"Missing: {', '.join(recipe['missing']) or 'None'}"
        )