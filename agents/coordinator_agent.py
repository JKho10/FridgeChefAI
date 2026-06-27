from skills.meal_skill import meal_planning_skill
from agents.recipe_agent import RecipeAgent
from agents.nutrition_agent import NutritionAgent
from agents.shopping_agent import ShoppingAgent
from agents.safety_agent import SafetyAgent


class CoordinatorAgent:
    """
    CoordinatorAgent orchestrates the full meal-planning pipeline.

    This agent acts as the central controller that coordinates multiple
    specialized sub-agents:

    - SafetyAgent: validates user input for unsafe or disallowed content
    - RecipeAgent: generates meal recipes based on ingredients and strategy
    - NutritionAgent: analyzes nutritional values of selected recipes
    - ShoppingAgent: builds a consolidated shopping list
    - meal_planning_skill: determines meal planning strategy

    Workflow:
        1. Validate required user health/context fields
        2. Run safety checks on user input
        3. Parse raw input into structured ingredients
        4. Generate a meal planning strategy
        5. Generate candidate recipes
        6. Select top recipes (max 3)
        7. Perform nutrition analysis
        8. Build shopping list
        9. Return structured response with traceability

    Attributes:
        recipe_agent (RecipeAgent): Generates recipe suggestions.
        nutrition_agent (NutritionAgent): Computes nutrition estimates.
        shopping_agent (ShoppingAgent): Builds ingredient shopping lists.
        safety_agent (SafetyAgent): Validates safety of user input.
    """

    def __init__(self):
        """Initialize all sub-agents used in the coordination pipeline."""
        self.recipe_agent = RecipeAgent()
        self.nutrition_agent = NutritionAgent()
        self.shopping_agent = ShoppingAgent()
        self.safety_agent = SafetyAgent()

    def run(
        self,
        user_input,
        goal,
        weight,
        height,
        age,
        sex,
        activity_level,
        diet_pref="None"
    ):
        """
        Execute the full meal planning pipeline.

        Args:
            user_input (str):
                Raw user input describing desired meals or ingredients
                (e.g., "chicken, rice, broccoli").

            goal (str):
                Nutrition or fitness goal (e.g., "bulk", "cut", "maintain").

            weight (float | int):
                User body weight in kilograms.

            height (float | int):
                User height in centimeters.

            age (int):
                User age in years. Required.

            sex (str):
                Biological sex ("male", "female", etc.). Required.

            activity_level (str):
                Physical activity level (e.g., "low", "moderate", "high").
                Required.

            diet_pref (str, optional):
                Dietary preference (e.g., "vegan", "keto", "none").
                Defaults to "None".

        Returns:
            dict: A structured response containing:
                - recipes (list): Top 3 generated recipes
                - nutrition (dict): Estimated nutrition breakdown
                - shopping_list (list): Consolidated ingredient list
                - strategy (dict): Meal planning strategy used
                - safety (str): Safety evaluation result
                - trace (list): Step-by-step execution log
                - reason (str): Final status or failure explanation

        Flow Control:
            - If required fields are missing → early exit with reason
            - If safety check flags unsafe content → execution is blocked
            - If no recipes are generated → early exit with reason
        """

        trace = []

        diet_pref = (diet_pref or "none").strip().lower()

        # Validate required fields
        missing_fields = []
        if not age:
            missing_fields.append("age")
        if not sex:
            missing_fields.append("sex")
        if not activity_level:
            missing_fields.append("activity_level")

        if missing_fields:
            return {
                "recipes": [],
                "nutrition": {},
                "shopping_list": [],
                "trace": trace,
                "reason": f"Missing required fields: {', '.join(missing_fields)}"
            }

        # Safety check
        safety = self.safety_agent.check(user_input)
        trace.append({"step": "safety", "result": safety})

        if safety and "unsafe" in safety.lower():
            return {
                "recipes": [],
                "nutrition": {},
                "shopping_list": [],
                "trace": trace,
                "reason": "Blocked by safety system"
            }

        # Parse input
        ingredients = self._parse(user_input)
        trace.append({"step": "parse", "ingredients": ingredients})

        # Strategy generation
        strategy = meal_planning_skill(ingredients, goal)
        trace.append({"step": "strategy", "strategy": strategy})

        # Recipe generation
        recipes, reason = self.recipe_agent.generate(
            ingredients,
            strategy,
            diet_pref
        )

        trace.append({
            "step": "recipe_generation",
            "recipe_count": len(recipes),
            "reason": reason
        })

        if not recipes:
            return {
                "recipes": [],
                "nutrition": {},
                "shopping_list": [],
                "trace": trace,
                "reason": reason
            }

        # Keep only top 3 recipes
        best_recipes = recipes[:3]

        # Nutrition analysis
        nutrition = self.nutrition_agent.analyze(
            best_recipes,
            goal,
            weight,
            height,
            age,
            sex,
            activity_level,
            diet_pref
        )

        trace.append({
            "step": "nutrition",
            "result": {
                "estimated_calories": nutrition.get("estimated_calories"),
                "estimated_protein": nutrition.get("estimated_protein")
            }
        })

        # Shopping list generation
        shopping = self.shopping_agent.create_list(best_recipes)

        trace.append({
            "step": "shopping",
            "items": len(shopping)
        })

        return {
            "recipes": best_recipes,
            "nutrition": nutrition,
            "shopping_list": shopping,
            "strategy": strategy,
            "safety": safety,
            "trace": trace,
            "reason": reason
        }

    # Helper method
    def _parse(self, text):
        """
        Parse raw comma-separated user input into a normalized ingredient list.

        Args:
            text (str): Raw user input string.

        Returns:
            list[str]: Cleaned list of lowercase ingredient strings.
        """
        if not text:
            return []

        return [
            x.strip().lower()
            for x in text.split(",")
            if x.strip()
        ]