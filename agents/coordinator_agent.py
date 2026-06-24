from skills.meal_skill import meal_planning_skill
from agents.recipe_agent import RecipeAgent
from agents.nutrition_agent import NutritionAgent
from agents.shopping_agent import ShoppingAgent
from agents.safety_agent import SafetyAgent


class CoordinatorAgent:

    """
    Central orchestration agent for the FridgeChef system.

    Responsibilities:
    - Coordinates execution across specialized agents
    - Applies input safety checks before processing
    - Selects a meal planning strategy based on user goals
    - Runs a simple retry loop if recipe quality is low
    - Aggregates outputs into a final response
    """

    def __init__(self):
        self.recipe_agent = RecipeAgent()
        self.nutrition_agent = NutritionAgent()
        self.shopping_agent = ShoppingAgent()
        self.safety_agent = SafetyAgent()

    def run(
        self,
        user_input,
        goal,
        weight=None,
        height=None,
        diet_pref="None"
    ):
        
        """
        Executes the full meal planning pipeline.

        Pipeline:
        1. Validate input safety
        2. Parse ingredient list
        3. Select meal planning strategy
        4. Generate recipes via RecipeAgent
        5. Retry once if recipe quality is low
        6. Compute nutrition estimates
        7. Generate shopping list

        Returns:
        - recipes
        - nutrition summary
        - shopping list
        - execution trace for debugging
        """

        trace = []

        safety = self.safety_agent.check(user_input)

        trace.append({
            "step": "safety",
            "result": safety
        })

        if "unsafe" in safety.lower():
            return {
                "recipes": [],
                "nutrition": {},
                "shopping_list": [],
                "trace": trace,
                "reason": "Blocked by safety system"
            }

        ingredients = self._parse(user_input)
        trace.append({
            "step": "parse",
            "ingredients": ingredients
        })

        strategy = meal_planning_skill(
            ingredients,
            goal
        )

        trace.append({
            "step": "strategy",
            "strategy": strategy
        })

        """
        Retry loop:
        If recipe coverage is low, the system retries once
        using a fallback strategy. A single retry is used to 
        balance quality improvement with predictable execution time.
        """
        best_recipes = []
        reason = ""

        for attempt in range(2):
            recipes, reason = self.recipe_agent.generate(
                ingredients,
                strategy
            )

            trace.append({
                "step": f"recipe_attempt_{attempt}",
                "recipe_count": len(recipes)
            })

            quality = 0

            if recipes:
                quality = len(
                    recipes[0].get(
                        "matched",
                        []
                    )
                )

            trace.append({
                "step": "reflection",
                "attempt": attempt,
                "quality_score": quality,
                "decision":
                    "accepted"
                    if quality >= 2
                    else "retry with improved strategy"
            })

            if recipes and quality >= 2:
                best_recipes = recipes
                break

            if recipes and not best_recipes:
                best_recipes = recipes

            strategy = "BALANCED_MEALS"

        nutrition = self.nutrition_agent.analyze(
            best_recipes,
            goal,
            weight,
            height,
            diet_pref
        )

        trace.append({
            "step": "nutrition",
            "result": nutrition
        })

        shopping = self.shopping_agent.create_list(
            best_recipes
        )

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

    def _parse(self, text):

        """
        Converts user ingredient input into a normalized list.

        Example:
        "Chicken, Rice"
        becomes:
        ["chicken", "rice"]

        Normalization improves matching accuracy
        during recipe retrieval.
        """
        return [
            x.strip().lower()
            for x in text.split(",")
            if x.strip()
        ]