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

        trace = []

        diet_pref = (diet_pref or "none").strip().lower()

        # Validation
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

        # Strategy
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

        # Take top 3 ONLY (no mutation, no serving override)
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

        # Shopping list (single source of truth — NO extra dedupe)
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

    # Helpers
    def _parse(self, text):
        if not text:
            return []

        return [
            x.strip().lower()
            for x in text.split(",")
            if x.strip()
        ]