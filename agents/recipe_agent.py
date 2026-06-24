from mcp_server.server import MealMCPServer
import re

class RecipeAgent:
    """
    Recipe retrieval, ranking, and explanation agent.

    This agent is responsible for:
    - Fetching recipes via MCP tool layer
    - Extracting structured ingredients from API responses
    - Comparing user ingredients with recipe ingredients
    - Computing match scores (coverage)
    - Identifying:
        ✔ matched ingredients (user has them)
        ✖ missing ingredients (user input not in recipe)
        ➕ additional ingredients (recipe requires but user does not have)

    Key design goal:
    - Avoid substring matching errors (e.g. "chicken" ≠ "chicken stock")
    - Use token-based matching for accuracy
    """

    def __init__(self):
        """
        Initializes RecipeAgent with MCP server connection.
        """
        self.mcp = MealMCPServer()

    def normalize(self, text: str) -> str:
        """
        Normalizes text for consistent comparison.

        Steps:
        - Converts to lowercase
        - Strips whitespace

        Args:
            text (str): input string

        Returns:
            str: normalized string
        """
        return text.lower().strip()

    def clean_tokens(self, text: str):
        """
        Converts a string into a set of word tokens.

        Example:
            "chicken stock" -> {"chicken", "stock"}

        Args:
            text (str)

        Returns:
            set[str]
        """
        return set(re.findall(r"[a-z]+", text.lower()))

    def is_match(self, a: str, b: str) -> bool:
        """
        Determines if two ingredient strings match.

        FIXES:
        - Prevents false positives like:
            "chicken" matching "chicken stock"

        Logic:
        - Token intersection must exist

        Args:
            a (str): ingredient A
            b (str): ingredient B

        Returns:
            bool: True if match exists
        """
        return len(self.clean_tokens(a) & self.clean_tokens(b)) > 0

    def generate(self, ingredients, strategy):
        """
        Generates ranked recipe recommendations.

        Pipeline:
        1. Normalize user ingredients
        2. Retrieve candidate meals via MCP search
        3. Fetch full recipe details
        4. Rank recipes by ingredient overlap
        5. Return top 3 results

        Args:
            ingredients (list[str])
            strategy (str): user goal / dietary strategy

        Returns:
            tuple:
                - list[dict]: ranked recipes
                - str: explanation message
        """

        ingredients = [
            x.lower().strip()
            for x in ingredients
            if x.strip()
        ]

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

        return recipes, "Recipes ranked using multi-agent ingredient intelligence."

    def rank_recipes(self, meals, ingredients):
        """
        Ranks recipes based on ingredient overlap.

        Steps:
        1. Fetch full recipe details via MCP
        2. Extract structured ingredient list
        3. Compare against user input
        4. Compute:
            - matched ingredients
            - missing ingredients (user input not in recipe)
            - additional ingredients (recipe requires but user lacks)
        5. Compute coverage score
        6. Sort by score

        Args:
            meals (list)
            ingredients (list[str])

        Returns:
            list[dict]: ranked recipes
        """

        results = []

        user_ingredients = [
            self.normalize(i) for i in ingredients
        ]

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

            matched = list(set(matched))
            missing = list(set(missing))

            additional = []

            for ri in recipe_ingredients:
                if not any(self.is_match(ri, ui) for ui in user_ingredients):
                    additional.append(ri)

            additional = list(dict.fromkeys(additional))

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

    def extract(self, meal):
        """
        Extracts structured ingredients from MealDB response.

        MealDB format:
        - strIngredient1 ... strIngredient20
        - strMeasure1 ... strMeasure20

        Returns:
            list[dict]:
                {
                    "ingredient": str,
                    "measure": str
                }
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

    def explain(self, strategy, recipe):
        """
        Generates human-readable explanation for recipe ranking.

        Args:
            strategy (str)
            recipe (dict)

        Returns:
            str: explanation text
        """

        return (
            f"⭐ Recommended for {strategy}\n\n"
            f"Match: {recipe['coverage']}%\n"
            f"Uses: {', '.join(recipe['matched']) if recipe['matched'] else 'None'}\n"
            f"Missing: {', '.join(recipe['missing']) if recipe['missing'] else 'None'}"
        )