from skills.meal_skill import meal_planning_skill
from agents.recipe_agent import RecipeAgent
from agents.nutrition_agent import NutritionAgent
from agents.shopping_agent import ShoppingAgent
from agents.safety_agent import SafetyAgent


class CoordinatorAgent:

    """
    CoordinatorAgent is the central orchestrator of the meal planning system.

    It acts as the "brain controller" that coordinates multiple specialized agents:

    - SafetyAgent → ensures input is safe
    - RecipeAgent → generates candidate recipes
    - NutritionAgent → computes nutritional breakdown
    - ShoppingAgent → builds grocery list
    - meal_planning_skill → defines strategy logic

    Pipeline flow:
        user input → safety check → parsing → strategy →
        recipe generation → nutrition analysis → shopping list → final output

    This design follows a modular multi-agent architecture.
    """

    def __init__(self):
        """
        Initialize all sub-agents used in the meal planning pipeline.
        Each agent is responsible for a single domain of logic.
        """
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
        Main execution pipeline for generating a full meal plan.

        Args:
            user_input (str):
                Raw ingredient input from user (comma-separated string)

            goal (str):
                Dietary goal (e.g. "Lose Weight", "Gain Muscle")

            weight (float):
                User body weight in kg

            height (float):
                User height in cm

            age (int):
                User age

            sex (str):
                "Male" or "Female" (used for BMR calculation)

            activity_level (str):
                Physical activity level (sedentary → very active)

            diet_pref (str, optional):
                Dietary preference (e.g. vegetarian, high protein)

        Returns:
            dict:
                {
                    "recipes": List of top recipes,
                    "nutrition": Nutrition breakdown of best recipe,
                    "shopping_list": Deduplicated grocery items,
                    "strategy": Planning strategy used,
                    "safety": Safety evaluation result,
                    "trace": Debug trace of pipeline steps,
                    "reason": Explanation or failure reason
                }
        """

        trace = []

        # Normalize diet preference for consistency
        diet_pref = (diet_pref or "none").strip().lower()


        # Validation step ensuring required user metadata exists
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

        # Safety check prevent unsafe or inappropriate inputs
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

        # Input parsing convert raw string into structured ingredient list 
        ingredients = self._parse(user_input)
        trace.append({"step": "parse", "ingredients": ingredients})

        # Strategy generation determine meal planning approach based on goal and ingredients
        strategy = meal_planning_skill(ingredients, goal)
        trace.append({"step": "strategy", "strategy": strategy})

        # Recipe generation generate candidate recipes based on ingredients + strategy
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

        # Select top recipes but limit to top 3 candidates to reduce noise
        best_recipes = recipes[:3]

        # Normalize servings safely
        for r in best_recipes:
            try:
                s = int(r.get("servings", 2))
            except:
                s = 2
            r["servings"] = max(1, min(s, 4))

        # Nutrition analysis to compute macros for selected recipes
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
        shopping = self._dedupe_list(
            self.shopping_agent.create_list(best_recipes)
        )

        trace.append({
            "step": "shopping",
            "items": len(shopping)
        })

        # Final output return structured meal plan result
        return {
            "recipes": best_recipes,
            "nutrition": nutrition,
            "shopping_list": shopping,
            "strategy": strategy,
            "safety": safety,
            "trace": trace,
            "reason": reason
        }

    # Helpers
    def _parse(self, text):
        """
        Parse comma-separated ingredient string into clean list.

        Example:
            "chicken, rice, tomato"
            → ["chicken", "rice", "tomato"]
        """
        if not text:
            return []

        return [
            x.strip().lower()
            for x in text.split(",")
            if x.strip()
        ]

    def _dedupe_list(self, items):
        """
        Remove duplicate grocery items while preserving order.

        Args:
            items (list): raw grocery items

        Returns:
            list: cleaned unique grocery list
        """
        seen = set()
        result = []

        for i in items:
            key = str(i).strip().lower()
            if key not in seen:
                seen.add(key)
                result.append(i)

        return result