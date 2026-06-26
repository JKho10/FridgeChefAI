import re
class ShoppingAgent:
    """
    Generates a consolidated grocery list from selected recipes.

    This agent collects ingredients from multiple recipes,
    normalizes them, and removes duplicates to produce a clean shopping list.
    """

    def create_list(self, recipes):
        """
        Creates a deduplicated grocery list from recipe ingredients.

        This method:
        - extracts ingredients from recipe objects
        - supports both dict and string ingredient formats
        - normalizes text for consistent comparison
        - removes duplicates using a normalized key
        - returns a sorted list of cleaned ingredient strings

        Args:
            recipes (list): list of recipe dictionaries containing ingredients

        Returns:
            list: sorted list of unique ingredient strings
        """

        items = []
        seen = set()

        for r in recipes:
            raw_ingredients = r.get("ingredients", [])

            for item in raw_ingredients:

                if isinstance(item, dict):
                    name = item.get("ingredient") or item.get("name") or str(item)
                    measure = item.get("measure", "")
                    cleaned = f"{measure} {name}".strip()
                else:
                    cleaned = str(item).strip()

                cleaned = cleaned.lower().strip()

                cleaned_key = re.sub(r"[\d\W]+", " ", cleaned)
                cleaned_key = " ".join(cleaned_key.split())

                if cleaned not in seen:
                    seen.add(cleaned)
                    items.append(cleaned)

        return sorted(items)