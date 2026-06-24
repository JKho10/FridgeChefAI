import requests

BASE = "https://www.themealdb.com/api/json/v1/1"

def search_meals_by_ingredient(
    ingredient: str
):
    """
    Fetches meals that match a given ingredient
    from the MealDB API.
    """

    response = requests.get(
        f"{BASE}/filter.php",
        params={
            "i": ingredient
        },
        timeout=10
    )

    response.raise_for_status()

    return response.json()

def get_meal_details(
    meal_id: str
):
    """
    Fetches detailed information for a meal
    using its MealDB ID.
    """
    response = requests.get(
        f"{BASE}/lookup.php",
        params={
            "i": meal_id
        },
        timeout=10
    )

    response.raise_for_status()

    return response.json()