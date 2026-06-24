"""
nutrition_api.py

USDA Nutrition API service layer.

This module handles all external API communication with the
USDA FoodData Central API.

Responsibilities:
- Query USDA API using ingredient names
- Extract macronutrients (calories, protein, carbs, fat)
- Normalize API response into a consistent structure
- Hide API keys using environment variables

IMPORTANT:
- Requires USDA_API_KEY in .env file
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


class NutritionAPI:
    """
    Service class for interacting with USDA FoodData Central API.
    """

    BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

    def __init__(self):
        self.api_key = os.getenv("USDA_API_KEY")

    def get_nutrition(self, ingredient: str):
        """
        Fetch nutrition data for a single ingredient.

        Args:
            ingredient (str): food name (e.g. "chicken", "rice")

        Returns:
            dict or None:
                {
                    "ingredient": str,
                    "calories": float,
                    "protein": float,
                    "carbs": float,
                    "fat": float
                }
        """

        if not ingredient:
            return None

        params = {
            "query": ingredient,
            "pageSize": 1,
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()

            foods = data.get("foods", [])
            if not foods:
                return None

            food = foods[0]

            nutrients = {
                n["nutrientName"]: n["value"]
                for n in food.get("foodNutrients", [])
            }

            return {
                "ingredient": ingredient,
                "calories": nutrients.get("Energy", 0),
                "protein": nutrients.get("Protein", 0),
                "carbs": nutrients.get("Carbohydrate, by difference", 0),
                "fat": nutrients.get("Total lipid (fat)", 0)
            }

        except Exception as e:
            print(f"[USDA API ERROR] {e}")
            return None