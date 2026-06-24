from mcp_server.server import MealMCPServer

class RecipeAgent:

    """
    Recipe retrieval and ranking agent.

    Responsibilities:
    - Retrieves recipe data through MCP tool layer
    - Fetches full recipe details for candidates
    - Scores recipes based on ingredient overlap
    - Returns ranked list of recommendations with explanations

    The agent does not directly access external APIs.
    All external calls are routed through the MCP server.
    """

    def __init__(self):
        self.mcp = MealMCPServer()

    def generate(self, ingredients, strategy):

        """
        Generates ranked recipe recommendations.

        Steps:
        1. Normalize input ingredients
        2. Retrieve candidate meals via MCP search tool
        3. Fetch full recipe details via MCP tool
        4. Rank recipes using ingredient coverage scoring
        5. Return top results with explanations
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
                "rank": index + 1,
                "why": self.explain(strategy, recipe)
            })

        return recipes, "Recipes ranked using multi-agent ingredient intelligence."

    def rank_recipes(self, meals, ingredients):

        """
        Ranks recipes based on ingredient overlap.

        Process:
        1. Fetch full recipe details via MCP tool
        2. Extract ingredient list
        3. Compare against user ingredients
        4. Compute coverage score
        5. Apply bonus for higher overlap
        6. Sort recipes by final score
        """

        results = []

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

            recipe_items = [
                x.lower()
                for x in self.extract(recipe)
            ]

            matched = []
            missing = []

            for user_item in ingredients:

                found = any(user_item in r for r in recipe_items)

                if found:
                    matched.append(user_item)
                else:
                    missing.append(user_item)

            if len(ingredients) == 0:
                coverage = 0
            else:
                coverage = round(len(matched) / len(ingredients) * 100)

            score = coverage

            if len(matched) >= 2:
                score += 20

            results.append({
                "score": score,
                "name": recipe["strMeal"],
                "image": recipe["strMealThumb"],
                "ingredients": recipe_items,
                "instructions": recipe["strInstructions"],
                "coverage": coverage,
                "matched": matched,
                "missing": missing
            })

        return sorted(results, key=lambda x: x["score"], reverse=True)

    def extract(self, meal):
        
        """
        Extracts ingredient list from MealDB API response.

        The API stores ingredients in fields:
        strIngredient1 ... strIngredient20

        This function:
        - collects non-empty values
        - normalizes formatting
        - returns a clean list of ingredients
        """

        items = []

        for i in range(1, 21):
            item = meal.get(f"strIngredient{i}")
            if item and item.strip():
                items.append(item.strip())

        return items

    def explain(self, strategy, recipe):

        """
        Generates a simple explanation of why a recipe was selected.

        Returns:
        - strategy used
        - ingredient match percentage
        - matched ingredients
        - missing ingredients
        """

        return (
            f"⭐ Recommended for {strategy}\n\n"
            f"Match: {recipe['coverage']}%\n"
            f"Uses: {', '.join(recipe['matched'])}\n"
            f"Missing: {', '.join(recipe['missing']) if recipe['missing'] else 'None'}"
        )