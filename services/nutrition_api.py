import os
import re
import requests
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()


class NutritionAPI:
    """
    FAST USDA Nutrition Mapper (optimized + fixed)
    """

    BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

    def __init__(self):
        self.api_key = os.getenv("USDA_API_KEY")
        if not self.api_key:
            raise ValueError("Missing USDA_API_KEY")

    # -----------------------------
    # CLEANING
    # -----------------------------
    def clean(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"\d+", "", text)
        text = re.sub(
            r"\b(tbsp|tsp|g|kg|ml|oz|cup|cups|chopped|sliced|large|small|fresh)\b",
            "",
            text
        )
        text = re.sub(r"[^a-z ]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    # -----------------------------
    # EXTRACT NUTRIENTS
    # -----------------------------
    def extract(self, food: dict) -> dict:
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

    # -----------------------------
    # PICK BEST MATCH
    # -----------------------------
    def pick(self, foods, query: str):
        if not foods:
            return None

        query_tokens = set(self.clean(query).split())

        def score(f):
            desc = f.get("description", "").lower()
            desc_tokens = set(self.clean(desc).split())

            if len(query_tokens & desc_tokens) == 0:
                return -9999

            s = 0
            s += len(query_tokens & desc_tokens) * 30

            if query_tokens.issubset(desc_tokens):
                s += 50

            if "raw" in desc:
                s += 20
            if "fried" in desc or "processed" in desc:
                s -= 50

            s -= len(desc_tokens) * 0.2
            return s

        best = max(foods, key=score)

        # reject bad matches
        if score(best) < 0:
            return None

        return best

    # -----------------------------
    # CACHE FUNCTION (FIXED)
    # -----------------------------
    @lru_cache(maxsize=512)
    def _cached_lookup(self, cleaned_query: str, api_key: str):
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

            try:
                data = r.json()
            except Exception:
                return None

            foods = data.get("foods", [])
            food = self.pick(foods, cleaned_query)

            if not food:
                return None

            return self.extract(food)

        except Exception as e:
            print("USDA API error:", e)
            return None

    # -----------------------------
    # PUBLIC METHOD
    # -----------------------------
    def get_nutrition_per_100g(self, ingredient: str):
        if not ingredient:
            return None

        cleaned = self.clean(ingredient)
        return self._cached_lookup(cleaned, self.api_key)