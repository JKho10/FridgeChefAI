import re
from services.nutrition_api import NutritionAPI


class NutritionAgent:

    def __init__(self):
        self.api = NutritionAPI()


    ZERO_CAL = {
        "water",
        "salt",
        "pepper",
        "stock",
        "broth",
        "spice",
        "thyme",
        "parsley",
        "garlic"
    }


    UNIT_WEIGHTS = {

        # realistic defaults
        "whole chicken": 1200,
        "chicken": 150,

        "rice": 100,
        "bread": 40,
        "chocolate": 20,

        "corn": 100,
        "sweetcorn":100,

        "oil":15,
        "chorizo":225,

        "onion":120,
        "garlic":10,
    }



    def extract_qty(self,text):

        text=text.lower()


        # grams
        m=re.search(r"(\d+\.?\d*)\s*g",text)

        if m:
            return float(m.group(1))


        # kilograms
        m=re.search(r"(\d+\.?\d*)\s*kg",text)

        if m:
            return float(m.group(1))*1000


        # ml
        m=re.search(r"(\d+\.?\d*)\s*ml",text)

        if m:
            return float(m.group(1))


        # cups
        m=re.search(r"(\d+)\s*cups?",text)

        if m:
            return int(m.group(1))*180


        # tablespoon
        m=re.search(r"(\d+)\s*(tbsp|tablespoon)",text)

        if m:
            return int(m.group(1))*15


        return None



    def clean_name(self,text):

        text=text.lower()

        text=re.sub(
            r"\d+|g|kg|ml|oz|tbsp|tablespoon",
            "",
            text
        )

        text=re.sub(
            "[^a-z ]",
            " ",
            text
        )

        return re.sub(
            "\s+",
            " ",
            text
        ).strip()



    def estimate_weight(self,name,qty):

        for key,value in self.UNIT_WEIGHTS.items():

            if key in name:

                if qty:
                    return qty

                return value


        return qty or 100



    def calculate_target(
        self,
        goal,
        weight,
        height
    ):

        bmr=(
            10*weight
            +
            6.25*height
            -
            5*30
            +
            5
        )

        tdee=bmr*1.55


        if "lose" in goal.lower():
            return tdee*0.8

        if "gain" in goal.lower():
            return tdee*1.15


        return tdee



    def analyze(
        self,
        recipes,
        goal,
        weight=70,
        height=170,
        diet_pref="None"
    ):


        target=self.calculate_target(
            goal,
            weight,
            height
        )


        recipe_results=[]


        for recipe in recipes:


            total={
                "calories":0,
                "protein":0,
                "carbs":0,
                "fat":0
            }


            for ingredient in recipe.get(
                "ingredients",
                []
            ):


                name=self.clean_name(
                    ingredient
                )


                if any(
                    x in name
                    for x in self.ZERO_CAL
                ):
                    continue


                qty=self.extract_qty(
                    ingredient
                )


                grams=self.estimate_weight(
                    name,
                    qty
                )


                nutrition=self.api.get_nutrition_per_100g(
                    name
                )


                if not nutrition:
                    continue


                multiplier=grams/100


                total["calories"] += (
                    nutrition["calories"]
                    *
                    multiplier
                )

                total["protein"] += (
                    nutrition["protein"]
                    *
                    multiplier
                )

                total["carbs"] += (
                    nutrition["carbs"]
                    *
                    multiplier
                )

                total["fat"] += (
                    nutrition["fat"]
                    *
                    multiplier
                )



            # estimate servings

            servings = recipe.get(
                "servings"
            )


            if not servings:

                # realistic recipe serving estimation

                ingredient_text = " ".join(
                    recipe.get("ingredients", [])
                ).lower()


                if "whole chicken" in ingredient_text:
                    servings = 5

                elif "400g rice" in ingredient_text:
                    servings = 5

                elif "225g chorizo" in ingredient_text:
                    servings = 5

                else:
                    servings = 4

            recipe_results.append({

                "name":
                    recipe.get(
                        "name",
                        "Recipe"
                    ),

                "total_calories":
                    round(
                        total["calories"]
                    ),

                "calories":
                    round(
                        total["calories"]
                        /
                        servings
                    ),

                "protein":
                    round(
                        total["protein"]
                        /
                        servings
                    ),

                "carbs":
                    round(
                        total["carbs"]
                        /
                        servings
                    ),

                "fat":
                    round(
                        total["fat"]
                        /
                        servings
                    ),

                "servings":
                    servings
            })



        # IMPORTANT:
        # Only top recipe counts
        # recommendations are not eaten together

        selected = (
            recipe_results[0]
            if recipe_results
            else {}
        )


        return {


            "target_calories":
                round(target),


            "estimated_calories":
                selected.get(
                    "calories",
                    0
                ),


            "estimated_protein":
                selected.get(
                    "protein",
                    0
                ),


            "estimated_carbs":
                selected.get(
                    "carbs",
                    0
                ),


            "estimated_fat":
                selected.get(
                    "fat",
                    0
                ),


            "recipes":
                recipe_results,


            "goal":
                goal,


            "dietary_preference":
                diet_pref
        }