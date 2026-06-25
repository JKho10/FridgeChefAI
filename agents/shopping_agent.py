import re
class ShoppingAgent:
    """
    Generates a consolidated grocery list from selected recipes.
    """

    def create_list(self, recipes):
        """
        Combines ingredients from all recipes and removes duplicates safely.
        Always normalizes output to strings.
        """

        items = []
        seen = set()

        for r in recipes:
            raw_ingredients = r.get("ingredients", [])

            for item in raw_ingredients:

                # -------------------------
                # FIX 1: handle dict inputs
                # -------------------------
                if isinstance(item, dict):
                    name = item.get("ingredient") or item.get("name") or str(item)
                    measure = item.get("measure", "")
                    cleaned = f"{measure} {name}".strip()

                # -------------------------
                # FIX 2: handle string inputs
                # -------------------------
                else:
                    cleaned = str(item).strip()

                # -------------------------
                # normalize
                # -------------------------
                cleaned = cleaned.lower().strip()

                # normalize numbers + units away for dedupe
                cleaned_key = re.sub(r"[\d\W]+", " ", cleaned)
                cleaned_key = " ".join(cleaned_key.split())

                # -------------------------
                # deduplicate safely
                # -------------------------
                if cleaned not in seen:
                    seen.add(cleaned)
                    items.append(cleaned)

        return sorted(items)