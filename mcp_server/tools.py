import requests
from functools import lru_cache

BASE = "https://www.themealdb.com/api/json/v1/1"

@lru_cache(maxsize=128)
def search_meals_by_ingredient(ingredient: str):
    """
    Search meals from TheMealDB API by ingredient.

    This function queries the MealDB filter endpoint to retrieve
    meals that contain a specific ingredient.

    It uses LRU caching to avoid repeated network calls for
    identical ingredient queries.

    Args:
        ingredient (str):
            Ingredient name used to filter meals
            (e.g., "chicken", "rice", "tomato").

    Returns:
        dict:
            Raw JSON response from TheMealDB API.
            Example structure:
                {
                    "meals": [
                        {
                            "idMeal": "...",
                            "strMeal": "...",
                            "strMealThumb": "..."
                        }
                    ]
                }

    Raises:
        requests.HTTPError:
            If the API request fails (non-2xx response).
        requests.RequestException:
            For network-related errors.
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
    Retrieve full meal details from TheMealDB API by meal ID.

    This function fetches complete recipe information including:
        - Ingredients (up to 20 fields)
        - Measurements
        - Cooking instructions
        - Metadata (area, category, tags)

    Results are cached using LRU to minimize redundant API calls.

    Args:
        meal_id (str):
            Unique identifier for a meal (idMeal from search endpoint).

    Returns:
        dict:
            Raw JSON response from TheMealDB API.
            Example:
                {
                    "meals": [
                        {
                            "strMeal": "...",
                            "strInstructions": "...",
                            "strIngredient1": "...",
                            ...
                        }
                    ]
                }

    Raises:
        requests.HTTPError:
            If the API request fails (non-2xx response).
        requests.RequestException:
            For network-related or timeout errors.
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