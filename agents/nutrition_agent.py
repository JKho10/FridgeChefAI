"""
NutritionAgent

Responsible for estimating nutrition for generated recipes.

Pipeline:

RecipeAgent
      |
      ↓
NutritionAgent
      |
      ├── Extract ingredient quantities
      ├── Normalize ingredient names
      ├── Query USDA FoodData Central
      ├── Calculate calories/macros
      └── Return recipe nutrition summary


Output:

{
    "target_calories": 2400,

    "recipes":[
        {
            "name":"Chicken Rice Bowl",
            "calories":650,
            "protein":45,
            "carbs":70,
            "fat":18
        }
    ]
}

"""

import re

from services.nutrition_api import NutritionAPI


class NutritionAgent:


    def __init__(self):

        self.api = NutritionAPI()



    # --------------------------------------------------
    # QUANTITY EXTRACTION
    # --------------------------------------------------

    def extract_qty(self, text):

        text = text.lower()


        # whole chicken
        if "whole chicken" in text:
            return 1200


        # cups
        if "cup" in text:
            return 180


        # tablespoons
        if "tbsp" in text or "tablespoon" in text:
            return 15


        # teaspoons
        if "tsp" in text or "teaspoon" in text:
            return 5


        # grams/kg/oz

        match = re.search(
            r"(\d+\.?\d*)\s*(g|kg|oz)",
            text
        )


        if match:

            value=float(match.group(1))
            unit=match.group(2)


            if unit=="kg":
                return value*1000


            if unit=="oz":
                return value*28.35


            return value



        # default serving estimate

        return 100



    # --------------------------------------------------
    # INGREDIENT CLEANING
    # --------------------------------------------------

    def clean_name(self,text):

        text=text.lower()


        remove_words=[
            "g",
            "kg",
            "oz",
            "ml",
            "cup",
            "cups",
            "tbsp",
            "tsp",
            "tablespoon",
            "teaspoon",
            "large",
            "small",
            "whole",
            "chopped",
            "diced",
            "fresh"
        ]


        for w in remove_words:

            text=text.replace(w,"")


        text=re.sub(
            r"\d+",
            "",
            text
        )


        text=re.sub(
            r"[^a-z ]",
            "",
            text
        )


        return text.strip()



    # --------------------------------------------------
    # MAIN ANALYSIS
    # --------------------------------------------------

    def analyze(
        self,
        recipes,
        goal,
        weight=70,
        height=170,
        diet_pref="None"
    ):


        # ------------------------------
        # FITNESS TARGET
        # ------------------------------

        bmr = (
            10*weight
            +
            6.25*height
            -
            5*30
            +
            5
        )


        tdee=bmr*1.55


        goal=goal.lower()


        if "lose" in goal:

            target=tdee*0.8


        elif "gain" in goal:

            target=tdee*1.15


        else:

            target=tdee



        recipe_results=[]



        # ------------------------------
        # EACH RECIPE
        # ------------------------------

        for recipe in recipes:


            calories=0
            protein=0
            carbs=0
            fat=0



            ingredients=recipe.get(
                "ingredients",
                []
            )



            for item in ingredients:


                qty=self.extract_qty(item)


                clean=self.clean_name(item)


                if not clean:
                    continue



                nutrition=self.api.get_nutrition_per_100g(
                    clean
                )


                if not nutrition:
                    continue



                scale=qty/100


                calories += (
                    nutrition["calories"]
                    *
                    scale
                )


                protein += (
                    nutrition["protein"]
                    *
                    scale
                )


                carbs += (
                    nutrition["carbs"]
                    *
                    scale
                )


                fat += (
                    nutrition["fat"]
                    *
                    scale
                )



            # assume recipe feeds 4 people

            servings=4


            recipe_results.append(
                {

                "name":recipe.get(
                    "name",
                    "Recipe"
                ),

                "calories":round(
                    calories/servings
                ),

                "protein":round(
                    protein/servings
                ),

                "carbs":round(
                    carbs/servings
                ),

                "fat":round(
                    fat/servings
                )

                }
            )



        return {

            "target_calories":round(target),

            "recipes":recipe_results,

            "dietary_preference":diet_pref,

            "goal":goal

        }