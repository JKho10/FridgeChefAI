from mcp_server.server import MealMCPServer
import re


class RecipeAgent:
    """
    Recipe retrieval, ranking, and comparison agent.

    This agent is responsible for:

    1. Fetching recipes via MCP tool layer (MealDB wrapper)
    2. Extracting structured ingredients from API responses
    3. Normalizing and comparing user ingredients vs recipe ingredients
    4. Preventing false matches (e.g. "chicken" ≠ "chicken stock")
    5. Computing:
        - matched ingredients (user has them)
        - missing ingredients (user input not found in recipe)
        - additional ingredients (recipe requires but user does not have)
    6. Ranking recipes by ingredient coverage score

    Key design principles:
    - Token-based matching instead of substring matching
    - Avoid false positives from partial words
    - Deterministic scoring for consistent ranking
    """

    def __init__(self):
        """
        Initialize MCP connection.
        """
        self.mcp = MealMCPServer()

    def normalize(self, text: str) -> str:
        """
        Normalizes ingredient text:
        - lowercase
        - removes special characters
        - trims whitespace
        """
        text = text.lower()
        text = re.sub(r"[^a-z ]", "", text)
        return text.strip()

    def is_match(self, user_item: str, recipe_item: str) -> bool:
        """
        Strict ingredient matcher.

        RULES:
        ------
        1. Exact match only OR
        2. Token set must match exactly

        This prevents:
            "chicken" ≠ "chicken stock"
        """

        user_item = self.normalize(user_item)
        recipe_item = self.normalize(recipe_item)

        user_tokens = set(user_item.split())
        recipe_tokens = set(recipe_item.split())

        return user_tokens == recipe_tokens

    def generate(self, ingredients, strategy):
        """
        Generate ranked recipe recommendations.

        PIPELINE:
        ---------
        1. Normalize user input ingredients
        2. Fetch candidate meals via MCP search
        3. Retrieve full recipe details
        4. Rank recipes
        5. Return top 3 results
        """

        ingredients = [
            x.lower().strip()
            for x in ingredients
            if x.strip()
        ]

        if not ingredients:
            return [], "No ingredients provided."

        if "fish" in ingredients:
            return [], "Please specify fish type (salmon, tuna, cod, tilapia)."

        meal_pool = {}

        for ingredient in ingredients:
            try:
                data = self.mcp.call_tool(
                    "search_meals",
                    ingredient=ingredient
                )
            except Exception as e:
                return [], f"MCP search failed: {str(e)}"

            if data and data.get("meals"):
                for meal in data["meals"]:
                    meal_pool[meal["idMeal"]] = meal

        if not meal_pool:
            return [], "No recipes found. Try chicken, rice, eggs, salmon."

        ranked = self.rank_recipes(meal_pool.values(), ingredients)

        recipes = []

        for index, recipe in enumerate(ranked[:3]):
            recipes.append({
                "name": recipe["name"],
                "image": recipe["image"],
                "ingredients": recipe["ingredients"],
                "instructions": recipe["instructions"],
                "coverage": recipe["coverage"],
                "matched": recipe["matched"],
                "missing": recipe["missing"],
                "additional": recipe["additional"],
                "country": recipe.get("country", "Unknown"),
                "rank": index + 1,
                "why": self.explain(strategy, recipe)
            })

        return recipes, "Recipes ranked using ingredient intelligence."

    # ---------------------------------------------------------
    # RANKING ENGINE
    # ---------------------------------------------------------
    def rank_recipes(self, meals, ingredients):
        """
        Rank recipes based on ingredient overlap.

        OUTPUT METRICS:
        ----------------
        matched:
            ingredients user HAS that appear in recipe

        missing:
            user ingredients NOT found in recipe

        additional:
            ingredients required by recipe but not in user input

        coverage:
            % of user ingredients matched
        """

        results = []

        user_ingredients = [self.normalize(i) for i in ingredients]

        for meal in meals:
            try:
                details = self.mcp.call_tool(
                    "get_meal",
                    meal_id=meal["idMeal"]
                )
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

            # --------------------------
            # MATCHED / MISSING
            # --------------------------
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

            # --------------------------
            # ADDITIONAL INGREDIENTS
            # --------------------------
            additional = []

            for ri in recipe_ingredients:
                if not any(self.is_match(ri, ui) for ui in user_ingredients):
                    additional.append(ri)

            additional = sorted(set(additional))

            # --------------------------
            # COVERAGE SCORE
            # --------------------------
            coverage = round(
                len(matched) / len(user_ingredients) * 100
            ) if user_ingredients else 0

            score = coverage + (20 if len(matched) >= 2 else 0)

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

    # ---------------------------------------------------------
    # EXTRACTION FROM MEALDB
    # ---------------------------------------------------------
    def extract(self, meal):
        """
        Extract structured ingredients from MealDB API.

        RETURNS:
        --------
        [
            {
                "ingredient": str,
                "measure": str
            }
        ]
        """

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

    # ---------------------------------------------------------
    # EXPLANATION ENGINE
    # ---------------------------------------------------------
    def explain(self, strategy, recipe):
        """
        Generates human-readable explanation.
        """

        return (
            f"⭐ Recommended for {strategy}\n\n"
            f"Match: {recipe['coverage']}%\n"
            f"Uses: {', '.join(recipe['matched']) if recipe['matched'] else 'None'}\n"
            f"Missing: {', '.join(recipe['missing']) if recipe['missing'] else 'None'}"
        )