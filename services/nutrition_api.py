import os
import re
import requests
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()


class NutritionAPI:
    """
    fast usda nutrition mapper (optimized + deterministic)

    this class provides a lightweight interface to the usda fooddata central api.
    it cleans ingredient text, searches the api, selects the best matching food,
    and extracts normalized macronutrient values per 100g.

    the design prioritizes:
    - deterministic results (no randomness)
    - caching for performance
    - robust text normalization
    - safe fallback behavior when api fails
    """

    BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

    def __init__(self):
        """
        initialize the nutrition api client.

        loads the usda api key from environment variables.
        raises an error if the key is missing because the api cannot function without it.
        """
        self.api_key = os.getenv("USDA_API_KEY")
        if not self.api_key:
            raise ValueError("Missing USDA_API_KEY")

    # Text normalization
    def clean(self, text: str) -> str:
        """
        normalize ingredient text for consistent api querying.

        this removes quantities, units, and descriptive modifiers so that
        search queries are more likely to match usda database entries.

        args:
            text (str): raw ingredient text

        returns:
            str: cleaned, normalized query string
        """
        text = text.lower()
        text = re.sub(r"\d+", "", text)
        text = re.sub(
            r"\b(tbsp|tsp|g|kg|ml|oz|cup|cups|chopped|sliced|large|small|fresh)\b",
            "",
            text
        )
        text = re.sub(r"[^a-z ]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    # Nutrients extraction
    def extract(self, food: dict) -> dict:
        """
        extract macronutrient values from a usda food entry.

        converts raw api nutrient data into a simplified structure:
        calories, protein, carbs, and fat (all per 100g basis).

        args:
            food (dict): raw food object from usda api

        returns:
            dict: normalized nutrient dictionary
        """
        out = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}

        for n in food.get("foodNutrients", []):
            name = n.get("nutrientName", "").lower()
            val = n.get("value", 0)

            if "energy" in name or "calorie" in name:
                out["calories"] = val
            elif "protein" in name:
                out["protein"] = val
            elif "carbohydrate" in name:
                out["carbs"] = val
            elif "fat" in name and "fiber" not in name:
                out["fat"] = val

        return out

    # Ranking logic
    def pick(self, foods, query: str):
        """
        select the best matching food entry from usda search results.

        scoring is based on token overlap, specificity, and cooking relevance.
        raw matches are preferred while processed or low-relevance items are penalized.

        args:
            foods (list): list of candidate food entries from api
            query (str): cleaned ingredient query

        returns:
            dict or none: best matching food entry if confidence is sufficient
        """
        if not foods:
            return None

        query_tokens = set(self.clean(query).split())

        def score(f):
            desc = f.get("description", "").lower()
            desc_tokens = set(self.clean(desc).split())

            # reject completely unrelated items
            if len(query_tokens & desc_tokens) == 0:
                return -9999

            s = 0
            # reward token overlap
            s += len(query_tokens & desc_tokens) * 30
            # reward full subset matches
            if query_tokens.issubset(desc_tokens):
                s += 50
            # prefer raw foods
            if "raw" in desc:
                s += 20
            # penalize processed foods
            if "fried" in desc or "processed" in desc:
                s -= 50
            # penalize overly long descriptions slightly
            s -= len(desc_tokens) * 0.2
            return s

        best = max(foods, key=score)

        # reject bad matches
        if score(best) < 0:
            return None

        return best

    # Cached api lookup
    @lru_cache(maxsize=512)
    def _cached_lookup(self, cleaned_query: str, api_key: str):
        """
        cached wrapper for usda api requests.

        avoids repeated network calls for identical queries.

        args:
            cleaned_query (str): normalized ingredient query
            api_key (str): usda api key (included for cache uniqueness)

        returns:
            dict or none: extracted nutrient data per 100g
        """
        try:
            r = requests.get(
                self.BASE_URL,
                params={
                    "query": cleaned_query,
                    "pageSize": 8,
                    "api_key": api_key
                },
                timeout=10
            )
            # parse response safely
            try:
                data = r.json()
            except Exception:
                return None

            foods = data.get("foods", [])

            # pick best matching food
            food = self.pick(foods, cleaned_query)

            if not food:
                return None
            
            # extract normalized nutrients
            return self.extract(food)

        except Exception as e:
            print("USDA API error:", e)
            return None

    # Public interface
    def get_nutrition_per_100g(self, ingredient: str):
        """
        get nutrition values per 100g for a given ingredient.

        this is the main public method used by downstream agents.
        it handles cleaning, caching, api lookup, and fallback behavior.

        args:
            ingredient (str): raw ingredient name from recipe

        returns:
            dict or none: nutrition values per 100g if available
        """
        if not ingredient:
            return None

        cleaned = self.clean(ingredient)
        
        # delegate to cached lookup for performance
        return self._cached_lookup(cleaned, self.api_key)