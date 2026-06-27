from mcp_server.server import MealMCPServer
import re

class RecipeAgent:
    """
    RecipeAgent is responsible for generating and ranking recipes
    based on user-provided ingredients, dietary preferences, and strategy signals.

    It integrates with an external Meal MCP server to:
        - Search for candidate meals
        - Fetch full recipe details
        - Extract structured ingredient lists

    Core responsibilities:
        1. Normalize and interpret user ingredients
        2. Query external meal database (MCP server)
        3. Aggregate and deduplicate recipe candidates
        4. Rank recipes based on ingredient coverage and strategy
        5. Filter recipes based on dietary restrictions (e.g., vegetarian)
        6. Generate human-readable explanations for recommendations

    Ranking is primarily based on:
        - Ingredient match coverage
        - Number of matched ingredients
        - Strategy-based adjustments (e.g., high protein, low calorie)
    """
    def __init__(self):
        """Initialize connection to external Meal MCP server."""
        self.mcp = MealMCPServer()

    def estimate_servings(self, recipe):
        """
        Estimate number of servings based on recipe complexity.

        Heuristic:
            - Fewer ingredients → smaller meal
            - More ingredients → larger meal

        Args:
            recipe (dict): Recipe object with ingredient list

        Returns:
            int: Estimated number of servings
        """
        ingredient_count = len(recipe.get("ingredients", []))

        if ingredient_count < 6:
            return 2
        if ingredient_count < 12:
            return 3
        return 4

    # Normalization
    def normalize(self, text) -> str:
        """
        Normalize text into lowercase alphabetical tokens.

        Used for:
            - Ingredient matching
            - Deduplication
            - Comparison between user input and recipe data

        Args:
            text (str | dict): Raw ingredient or recipe text

        Returns:
            str: Clean normalized string
        """
        if isinstance(text, dict):
            text = text.get("name") or text.get("ingredient") or str(text)

        text = str(text).lower()
        text = re.sub(r"[^a-z ]", "", text)
        return text.strip()

    def is_match(self, user_item: str, recipe_item: str) -> bool:
        """
        Check if two ingredient tokens match exactly (set-based comparison).

        Args:
            user_item (str): User-provided ingredient
            recipe_item (str): Recipe ingredient

        Returns:
            bool: True if token sets match exactly
        """
        return set(self.normalize(user_item).split()) == set(self.normalize(recipe_item).split())

    # Diet filtering
    NON_VEGETARIAN_KEYWORDS = {
        "chicken", "beef", "pork", "lamb",
        "fish", "salmon", "tuna", "shrimp", "bacon",
        "anchovy", "gelatin", "stock", "broth", "fish sauce",
        "salmon", "haddock"
    }

    def is_vegetarian(self, extracted_ingredients):
        """
        Determine if a recipe is vegetarian.

        Args:
            extracted_ingredients (list[dict]): Ingredient list from MCP API

        Returns:
            bool: True if no non-vegetarian ingredients detected
        """
        text = " ".join(
            i["ingredient"].lower() for i in extracted_ingredients
        )
        return not any(x in text for x in self.NON_VEGETARIAN_KEYWORDS)

    # Recipe generation
    def generate(self, ingredients, strategy, diet_pref=None):
        """
        Generate ranked recipes from user ingredients.

        Pipeline:
            1. Normalize input ingredients
            2. Query MCP server for candidate meals
            3. Aggregate unique recipes
            4. Rank based on match coverage + strategy bias
            5. Filter by dietary preference
            6. Return top 3 recipes

        Args:
            ingredients (list[str]): User input ingredients
            strategy (str): Meal planning strategy
            diet_pref (str, optional): Dietary preference (e.g., vegetarian)

        Returns:
            tuple:
                - list[dict]: Top ranked recipes
                - str: Status / reason message
        """
        diet_pref = (diet_pref or "none").strip().lower()
        strategy = (strategy or "").strip()

        if not ingredients:
            return [], "No ingredients provided."

        ingredients = [self.normalize(x) for x in ingredients if x.strip()]

        # Require explicit fish type (avoid ambiguity)
        fish_aliases = {"salmon", "tuna", "cod", "tilapia"}
        if "fish" in ingredients and not any(x in ingredients for x in fish_aliases):
            return [], "Please specify fish type."

        meal_pool = {}

        # MCP search
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

        ranked = self.rank_recipes(meal_pool.values(), ingredients, diet_pref, strategy)

        if not ranked:
            return [], "No valid ranked recipes."

        top = ranked[:3]

        return [
            {
                "name": r["name"].strip(),
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
            for i, r in enumerate(top)
        ], "Recipes ranked using ingredient intelligence."

    # Ranking
    def rank_recipes(self, meals, ingredients, diet_pref=None, strategy=None):
        """
        Rank recipes based on ingredient overlap and optional strategy bias.

        Scoring model:
            - Ingredient coverage (primary signal)
            - Matched ingredient count
            - Strategy modifiers:
                - HIGH_PROTEIN_PRIORITY
                - LOW_CALORIE_PRIORITY
                - BALANCED_MEALS

        Returns:
            list[dict]: Ranked recipe candidates
        """
        results = []
        user_ingredients = sorted(set(self.normalize(i) for i in ingredients))

        for meal in meals:

            try:
                details = self.mcp.call_tool("get_meal", meal_id=meal["idMeal"])
            except Exception:
                continue

            if not isinstance(details, dict) or not details.get("meals"):
                continue

            recipe = details["meals"][0]
            extracted = self.extract(recipe)


            # Diet filter
            if (diet_pref or "").lower() == "vegetarian":
                if not self.is_vegetarian(extracted):
                    continue

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

            score = (coverage * 2) + (len(matched) * 3)

            # Strategy bias
            if strategy == "HIGH_PROTEIN_PRIORITY":
                protein_keywords = {"chicken", "beef", "pork", "fish", "egg"}
                protein_hits = sum(1 for i in recipe_ingredients if any(p in i for p in protein_keywords))
                score += protein_hits * 5

            elif strategy == "LOW_CALORIE_PRIORITY":
                score -= len(recipe_ingredients) * 2

            elif strategy == "BALANCED_MEALS":
                score += 2

            results.append({
                "score": score,
                "name": recipe["strMeal"].strip(),
                "image": recipe["strMealThumb"],
                "ingredients": [
                    {
                        "name": i["ingredient"],
                        "ingredient": i["ingredient"],
                        "measure": i["measure"]
                    }
                    for i in extracted
                ],
                "instructions": recipe["strInstructions"],
                "coverage": coverage,
                "matched": matched,
                "missing": missing,
                "additional": additional,
                "country": recipe.get("strArea", "Unknown"),
                "servings": self.estimate_servings(recipe)
            })

        return sorted(results, key=lambda x: x["score"], reverse=True)

    # Ingredients extraction
    def extract(self, meal):
        """
        Extract structured ingredient list from MCP meal response.

        MCP format:
            strIngredient1...strIngredient20
            strMeasure1...strMeasure20

        Returns:
            list[dict]: structured ingredients
        """
        items = []

        for i in range(1, 21):
            ingredient = meal.get(f"strIngredient{i}")
            measure = meal.get(f"strMeasure{i}")

            if ingredient and ingredient.strip():
                items.append({
                    "ingredient": ingredient.strip(),
                    "measure": (measure or "").strip(),
                    "raw": f"{measure} {ingredient}".strip()
                })

        return items

    # Explanation
    def explain(self, strategy, recipe, diet_pref=None):
        """
        Generate human-readable explanation for recipe selection.

        Returns:
            str: explanation text used for UI or debugging
        """
        diet_line = (
            f"Diet preference: {diet_pref}\n"
            if diet_pref and diet_pref != "none"
            else ""
        )

        return (
            f"⭐ Recommended for {strategy}\n"
            f"{diet_line}"
            f"Match: {recipe['coverage']}%\n"
            f"Uses: {', '.join(recipe['matched']) or 'None'}\n"
            f"Missing: {', '.join(recipe['missing']) or 'None'}"
        )