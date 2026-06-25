"""
NutritionAPI (USDA mapper)

GOAL:
- Prefer raw foods
- Avoid processed junk bias
"""

import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()


class NutritionAPI:

    BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

    def __init__(self):
        self.api_key = os.getenv("USDA_API_KEY")
        if not self.api_key:
            raise ValueError("Missing USDA_API_KEY")

    def clean(self, text):
        text = text.lower()
        text = re.sub(r"\d+", "", text)
        text = re.sub(r"\b(cooked|fried|prepared|chopped|raw)\b", "", text)
        text = re.sub(r"[^a-z ]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def extract(self, food):
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

    def pick(self, foods, query):
        if not foods:
            return None

        query_tokens = set(query.split())

        def score(f):
            d = f.get("description", "").lower()
            t = set(d.split())

            s = len(query_tokens & t) * 30
            if "raw" in d:
                s += 20
            if "fried" in d:
                s -= 50
            return s

        return max(foods, key=score)

    def get_nutrition_per_100g(self, ingredient):
        if not ingredient:
            return None

        cleaned = self.clean(ingredient)

        try:
            r = requests.get(
                self.BASE_URL,
                params={
                    "query": cleaned,
                    "pageSize": 5,
                    "api_key": self.api_key
                },
                timeout=10
            )

            foods = r.json().get("foods", [])
            food = self.pick(foods, cleaned)

            if not food:
                return None

            return self.extract(food)

        except:
            return None