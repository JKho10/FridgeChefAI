from services.nutrition_api import USDAClient

def __init__(self):
    self.usda = USDAClient(api_key="YOUR_API_KEY")

    import requests


class USDAClient:
    """
    Wrapper for USDA FoodData Central API.

    Responsibilities:
    - Search food items
    - Retrieve nutrition per 100g
    - Normalize responses
    """

    BASE_URL = "https://api.nal.usda.gov/fdc/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key

    def search_food(self, query: str):
        """
        Searches USDA database for a food item.
        """
        url = f"{self.BASE_URL}/foods/search"

        params = {
            "query": query,
            "pageSize": 1,
            "api_key": self.api_key
        }

        res = requests.get(url, params=params)
        data = res.json()

        foods = data.get("foods", [])
        if not foods:
            return None

        return foods[0]["fdcId"]

    def get_nutrition(self, fdc_id: int):
        """
        Gets full nutrition data for a food item.
        """
        url = f"{self.BASE_URL}/food/{fdc_id}"

        params = {"api_key": self.api_key}

        res = requests.get(url, params=params)
        return res.json()

    def get_macros(self, food_name: str):
        """
        Returns calories + protein per 100g.
        """
        fdc_id = self.search_food(food_name)

        if not fdc_id:
            return None

        data = self.get_nutrition(fdc_id)

        calories = 0
        protein = 0

        for nutrient in data.get("foodNutrients", []):

            name = nutrient.get("nutrient", {}).get("name", "").lower()
            value = nutrient.get("amount", 0)

            if "energy" in name:
                calories = value
            if "protein" in name:
                protein = value

        return {
            "calories": calories,
            "protein": protein
        }