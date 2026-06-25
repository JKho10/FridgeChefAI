from mcp_server.server import MealMCPServer
import re


class RecipeAgent:

    def __init__(self):
        self.mcp = MealMCPServer()

    # -----------------------------
    # NORMALIZATION
    # -----------------------------
    def normalize(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z ]", "", text)
        return text.strip()

    def is_match(self, user_item: str, recipe_item: str) -> bool:
        user_tokens = set(self.normalize(user_item).split())
        recipe_tokens = set(self.normalize(recipe_item).split())
        return user_tokens == recipe_tokens

    # -----------------------------
    # GENERATION
    # -----------------------------
    def generate(self, ingredients, strategy, diet_pref=None):

        diet_pref = (diet_pref or "none").strip().lower()
        strategy = (strategy or "").strip()

        if not ingredients:
            return [], "No ingredients provided."

        ingredients = [
            self.normalize(x)
            for x in ingredients
            if x.strip()
        ]

        # -----------------------------
        # FIXED fish handling
        # -----------------------------
        fish_aliases = {"fish", "salmon", "tuna", "cod", "tilapia"}
        if any(i in fish_aliases for i in ingredients):
            return [], "Please specify fish type (salmon, tuna, cod, tilapia)."

        # -----------------------------
        # BUILD MEAL POOL
        # -----------------------------
        meal_pool = {}

        for ingredient in ingredients:
            try:
                data = self.mcp.call_tool("search_meals", ingredient=ingredient)
            except Exception as e:
                return [], f"MCP search failed: {str(e)}"

            if data and data.get("meals"):
                for meal in data["meals"]:
                    meal_pool[meal["idMeal"]] = meal

        if not meal_pool:
            return [], "No recipes found."

        ranked = self.rank_recipes(meal_pool.values(), ingredients)

        # -----------------------------
        # DIET FILTERING
        # -----------------------------
        filtered = []

        for recipe in ranked:

            ingredients_text = " ".join(recipe.get("ingredients", [])).lower()

            # vegetarian
            if diet_pref == "vegetarian":
                if any(x in ingredients_text for x in ["chicken", "beef", "pork", "fish"]):
                    continue

            # low carb (hard filter too)
            if diet_pref == "low carb":
                if any(x in ingredients_text for x in ["pasta", "rice", "bread", "noodles", "potato", "flour", "tortilla"]):
                    continue
            
            # high protein (soft preference, not constraint)
            protein_keywords = ["chicken", "beef", "fish", "egg", "turkey", "lamb", "pork"]
            if diet_pref == "high protein":
                if not any(x in ingredients_text for x in protein_keywords):
                    continue

            filtered.append(recipe)

        if not filtered:
            filtered = ranked[:3]

        # -----------------------------
        # OUTPUT TOP 3
        # -----------------------------
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
            for i, r in enumerate(filtered[:3])
        ], "Recipes ranked using ingredient intelligence."

    # -----------------------------
    # RANKING
    # -----------------------------
    def rank_recipes(self, meals, ingredients):

        results = []
        user_ingredients = sorted(set(self.normalize(i) for i in ingredients))

        for meal in meals:

            try:
                details = self.mcp.call_tool("get_meal", meal_id=meal["idMeal"])
            except Exception:
                continue

            if not details or not details.get("meals"):
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
                found = any(
                    self.is_match(ui, ri)
                    for ri in recipe_ingredients
                )

                if found:
                    matched.append(ui)
                else:
                    missing.append(ui)

            matched = sorted(set(matched))
            missing = sorted(set(missing))

            additional = [
                ri for ri in recipe_ingredients
                if not any(self.is_match(ri, ui) for ui in user_ingredients)
            ]

            additional = sorted(set(additional))

            coverage = round(
                len(matched) / len(user_ingredients) * 100
            ) if user_ingredients else 0

            score = coverage + (len(matched) * 5)

            results.append({
                "score": score,
                "name": recipe["strMeal"],
                "image": recipe["strMealThumb"],
                "ingredients": [
                    f"{i['measure']} {i['ingredient']}".strip()
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
                    "ingredient": ingredient.strip(),
                    "measure": (measure or "").strip()
                })

        return items

    # -----------------------------
    # EXPLAIN
    # -----------------------------
    def explain(self, strategy, recipe, diet_pref=None):

        diet_line = (
            f"Diet preference: {diet_pref}\n"
            if diet_pref and diet_pref != "none"
            else ""
        )

        return (
            f"⭐ Recommended for {strategy}\n"
            f"{diet_line}"
            f"Match: {recipe['coverage']}%\n"
            f"Uses: {', '.join(recipe['matched']) if recipe['matched'] else 'None'}\n"
            f"Missing: {', '.join(recipe['missing']) if recipe['missing'] else 'None'}"
        )