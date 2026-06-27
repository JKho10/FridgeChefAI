import os
import re
import requests
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()


class NutritionAPI:
    """
    NutritionAPI is a lightweight deterministic wrapper around the USDA FoodData Central API.

    This class is responsible for:
        - Cleaning and normalizing ingredient text
        - Querying the USDA food database
        - Selecting the most relevant food match
        - Extracting macronutrients in a standardized format (per 100g)
        - Providing cached lookups for performance optimization

    Design principles:
        - Deterministic output (no randomness in selection)
        - High cache efficiency (LRU caching)
        - Robust fallback behavior when API fails
        - Lightweight text normalization for better matching accuracy
    """

    BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

    def __init__(self):
        """
        Initialize NutritionAPI client.

        Loads USDA API key from environment variables.

        Raises:
            ValueError:
                If USDA_API_KEY is not found in environment variables.
        """
        self.api_key = os.getenv("USDA_API_KEY")
        if not self.api_key:
            raise ValueError("Missing USDA_API_KEY")

    # Text normalization
    def clean(self, text: str) -> str:
        """
        Normalize ingredient text for consistent USDA search queries.

        Steps:
            - Lowercase conversion
            - Remove numeric values
            - Remove common cooking descriptors and units
            - Remove special characters
            - Normalize whitespace

        This improves API matching accuracy by reducing noise in queries.

        Args:
            text (str): Raw ingredient string

        Returns:
            str: Cleaned and normalized query string
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
        Extract macronutrients from a USDA food entry.

        Converts raw USDA nutrient format into a simplified structure:

            {
                "calories": ...,
                "protein": ...,
                "carbs": ...,
                "fat": ...
            }

        All values are normalized per 100g.

        Args:
            food (dict): USDA food entry object

        Returns:
            dict: Standardized nutrient dictionary
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

    # Food matching
    def pick(self, foods, query: str):
        """
        Select the best matching USDA food entry for a query.

        This function ranks candidates using a heuristic scoring system:

        Scoring signals:
            - Token overlap with query (primary signal)
            - Full subset matches
            - Preference for raw foods
            - Penalization of processed foods
            - Slight penalty for overly long descriptions

        Args:
            foods (list[dict]): Candidate USDA food entries
            query (str): Cleaned ingredient query

        Returns:
            dict | None:
                Best matching food entry, or None if no valid match is found
        """
        if not foods:
            return None

        query_tokens = set(self.clean(query).split())

        def score(f):
            desc = f.get("description", "").lower()
            desc_tokens = set(self.clean(desc).split())

            # reject unrelated items early
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

    # Cached lookup
    @lru_cache(maxsize=512)
    def _cached_lookup(self, cleaned_query: str, api_key: str):
        """
        Cached USDA API lookup for a normalized ingredient query.

        This method:
            1. Queries USDA API
            2. Parses response safely
            3. Selects best matching food
            4. Extracts macronutrients

        Args:
            cleaned_query (str): Preprocessed ingredient query
            api_key (str): USDA API key (included for cache isolation)

        Returns:
            dict | None: Nutrients per 100g or None if unavailable
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
        Public API method to retrieve nutrition data per 100g.

        This method:
            - Cleans input ingredient
            - Uses cached lookup layer
            - Returns standardized macronutrient data

        Args:
            ingredient (str): Raw ingredient name

        Returns:
            dict | None:
                Nutrition data per 100g if found, otherwise None
        """
        if not ingredient:
            return None

        cleaned = self.clean(ingredient)
        
        # delegate to cached lookup for performance
        return self._cached_lookup(cleaned, self.api_key)