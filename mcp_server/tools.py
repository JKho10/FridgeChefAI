import requests
from functools import lru_cache

BASE = "https://www.themealdb.com/api/json/v1/1"

@lru_cache(maxsize=128)
def search_meals_by_ingredient(ingredient: str):
    """
    fetch meals that match a given ingredient from the mealdb api.

    this function uses a cached request layer to reduce repeated api calls
    for the same ingredient.

    args:
        ingredient (str): ingredient name used to filter meals

    returns:
        dict: raw json response from mealdb containing matching meals

    raises:
        requests.HTTPError: if the api request fails
    """
    # Build request to mealdb filter endpoint
    response = requests.get(
        f"{BASE}/filter.php",
        params={"i": ingredient},
        timeout=10
    )

    # Raise error if request fails (non-200 status code)
    response.raise_for_status()

    # Return raw api response
    return response.json()

@lru_cache(maxsize=256)
def get_meal_details(meal_id: str):
    """
    fetch detailed information for a meal using its mealdb id.

    this function retrieves full recipe data including ingredients,
    instructions, and metadata. results are cached to avoid redundant api calls.

    args:
        meal_id (str): unique meal identifier from mealdb

    returns:
        dict: raw json response containing full meal details

    raises:
        requests.HTTPError: if the api request fails
    """
    # Build request to meal lookup endpoint
    response = requests.get(
        f"{BASE}/lookup.php",
        params={"i": meal_id},
        timeout=10
    )
    # Ensure request succeeded
    response.raise_for_status()
    
    # Return full meal details
    return response.json()