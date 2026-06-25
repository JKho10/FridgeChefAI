import os
import re
import requests
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()


class NutritionAPI:
    """
    FAST USDA Nutrition Mapper (optimized)

    FIXES:
    - adds caching (major speed boost)
    - avoids repeated API calls for same ingredient
    - reduces Streamlit lag drastically
    """

    BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

    def __init__(self):
        self.api_key = os.getenv("USDA_API_KEY")
        if not self.api_key:
            raise ValueError("Missing USDA_API_KEY")

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

    def extract(self, food: dict) -> dict:
        out = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}

        for n in food.get("foodNutrients", []):
            name = n.get("nutrientName", "").lower()
            val = n.get("value", 0)

            if "energy" in name:
                out["calories"] = val
            elif "protein" in name:
                out["protein"] = val
            elif "carbohydrate" in name:
                out["carbs"] = val
            elif "fat" in name and "fiber" not in name:
                out["fat"] = val

        return out

    def pick(self, foods, query: str):
        if not foods:
            return None

        query_tokens = set(query.lower().split())

        def score(f):
            d = f.get("description", "").lower()
            t = set(d.split())

            s = 0
            s += len(query_tokens & t) * 30
            if query_tokens.issubset(t):
                s += 50
            if "raw" in d:
                s += 20
            if "fried" in d or "processed" in d:
                s -= 50
            s -= len(t) * 0.2
            return s

        return max(foods, key=score)

    # ---------------------------------------------------------
    # 🔥 CACHE LAYER (MAIN FIX)
    # ---------------------------------------------------------

    @lru_cache(maxsize=512)
    def get_cached_nutrition(self, cleaned_query: str):
        try:
            r = requests.get(
                self.BASE_URL,
                params={
                    "query": cleaned_query,
                    "pageSize": 8,
                    "api_key": self.api_key
                },
                timeout=10
            )

            foods = r.json().get("foods", [])
            food = self.pick(foods, cleaned_query)

            if not food:
                return None

            return self.extract(food)

        except:
            return None

    def get_nutrition_per_100g(self, ingredient: str):
        if not ingredient:
            return None

        cleaned = self.clean(ingredient)
        return self.get_cached_nutrition(cleaned)