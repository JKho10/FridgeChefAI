"""
CoordinatorAgent - Central orchestration layer for FridgeChef AI

This agent is responsible for:
-------------------------------------------------
✔ Validating user input via SafetyAgent
✔ Parsing ingredients into normalized format
✔ Selecting meal strategy via meal_planning_skill
✔ Coordinating recipe generation via RecipeAgent
✔ Running controlled retry logic for recipe quality
✔ Triggering NutritionAgent for macro estimation
✔ Generating shopping list via ShoppingAgent
✔ Producing full execution trace for debugging

DESIGN PRINCIPLES:
-------------------------------------------------
✔ Coordinator does NOT compute nutrition itself
✔ No ingredient logic duplication
✔ No reliance on "matched count" as quality signal
✔ Uses coverage score as primary ranking metric
✔ Stable retry logic without strategy corruption
"""

from skills.meal_skill import meal_planning_skill
from agents.recipe_agent import RecipeAgent
from agents.nutrition_agent import NutritionAgent
from agents.shopping_agent import ShoppingAgent
from agents.safety_agent import SafetyAgent


class CoordinatorAgent:

    def __init__(self):
        self.recipe_agent = RecipeAgent()
        self.nutrition_agent = NutritionAgent()
        self.shopping_agent = ShoppingAgent()
        self.safety_agent = SafetyAgent()

    # ---------------------------------------------------------
    # MAIN PIPELINE
    # ---------------------------------------------------------
    def run(
        self,
        user_input,
        goal,
        weight=None,
        height=None,
        diet_pref="None"
    ):
        """
        Executes full FridgeChef AI pipeline.

        Steps:
        ---------------------------------
        1. Safety validation
        2. Ingredient parsing
        3. Strategy selection
        4. Recipe generation (with retry loop)
        5. Nutrition estimation (USDA-based downstream)
        6. Shopping list generation
        7. Trace aggregation
        """

        trace = []

        # -----------------------------
        # 1. SAFETY CHECK
        # -----------------------------
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

        # -----------------------------
        # 2. PARSE INGREDIENTS
        # -----------------------------
        ingredients = self._parse(user_input)

        trace.append({
            "step": "parse",
            "ingredients": ingredients
        })

        # -----------------------------
        # 3. STRATEGY SELECTION
        # -----------------------------
        strategy = meal_planning_skill(ingredients, goal)

        trace.append({
            "step": "strategy",
            "strategy": strategy
        })

        # -----------------------------
        # 4. RECIPE GENERATION (RETRY LOOP FIXED)
        # -----------------------------
        best_recipes = []
        reason = ""

        for attempt in range(2):

            recipes, reason = self.recipe_agent.generate(
                ingredients,
                strategy
            )

            # SAFE QUALITY SCORE (FIXED)
            quality = 0
            if recipes:
                quality = recipes[0].get("coverage", 0)

            trace.append({
                "step": f"recipe_attempt_{attempt}",
                "recipe_count": len(recipes),
                "quality_score": quality
            })

            trace.append({
                "step": "reflection",
                "attempt": attempt,
                "decision": "accepted" if quality >= 60 else "retry"
            })

            # ACCEPT CONDITION (REALISTIC)
            if recipes and quality >= 60:
                best_recipes = recipes
                break

            # fallback retention
            if recipes and not best_recipes:
                best_recipes = recipes

            # refine strategy without destroying it
            strategy = f"{strategy}_REFINED"

        # -----------------------------
        # 5. NUTRITION ANALYSIS
        # -----------------------------
        nutrition = self.nutrition_agent.analyze(
            best_recipes,
            goal,
            weight,
            height,
            diet_pref
        )

        trace.append({
            "step": "nutrition",
            "result": {
                "estimated_calories": nutrition.get("estimated_calories"),
                "estimated_protein": nutrition.get("estimated_protein")
            }
        })

        # -----------------------------
        # 6. SHOPPING LIST
        # -----------------------------
        shopping = self.shopping_agent.create_list(best_recipes)

        trace.append({
            "step": "shopping",
            "items": len(shopping)
        })

        # -----------------------------
        # 7. FINAL RESPONSE
        # -----------------------------
        return {
            "recipes": best_recipes,
            "nutrition": nutrition,
            "shopping_list": shopping,
            "strategy": strategy,
            "safety": safety,
            "trace": trace,
            "reason": reason
        }

    # ---------------------------------------------------------
    # INGREDIENT PARSER
    # ---------------------------------------------------------
    def _parse(self, text):
        """
        Converts user input string into normalized ingredient list.

        Example:
            "Chicken, Rice, Eggs"
            → ["chicken", "rice", "eggs"]

        NOTE:
        This is intentionally simple.
        Quantity parsing is handled downstream (Recipe/Nutrition agents).
        """

        if not text:
            return []

        return [
            x.strip().lower()
            for x in text.split(",")
            if x.strip()
        ]