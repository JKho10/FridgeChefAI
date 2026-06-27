import re

class ShoppingAgent:
    """
    ShoppingAgent builds a consolidated grocery list from multiple recipes.

    This agent is responsible for:
        - Extracting ingredient data from recipe objects
        - Normalizing ingredient strings to avoid duplicates
        - Deduplicating across multiple recipes
        - Producing a clean, human-readable shopping list

    Design goals:
        - Deterministic output (no randomness)
        - Lightweight normalization (no external dependencies)
        - Cross-recipe deduplication
    """
    def normalize(self, text: str) -> str:
        """
        Normalize ingredient text into a consistent comparable format.

        Steps:
            - Lowercase conversion
            - Remove numbers
            - Remove special characters
            - Collapse extra whitespace

        This ensures:
            "2 cups Rice", "rice 200g", and "Rice" map to the same key.

        Args:
            text (str): Raw ingredient string

        Returns:
            str: Normalized token used for deduplication
        """
        text = str(text).lower().strip()
        text = re.sub(r"\d+", "", text)
        text = re.sub(r"[^a-z ]", " ", text)
        text = " ".join(text.split())
        return text

    def create_list(self, recipes):
        """
        Generate a deduplicated grocery list from a set of recipes.

        Process:
            1. Extract ingredients from each recipe
            2. Convert structured/unstructured formats into strings
            3. Normalize each ingredient for comparison
            4. Deduplicate using a set
            5. Return sorted final list

        Args:
            recipes (list[dict]):
                List of recipe objects, each containing an "ingredients" field

        Returns:
            list[str]:
                Sorted, deduplicated shopping list (human-readable format)
        """
        items = []
        seen = set()

        for r in recipes:
            raw = r.get("ingredients", [])

            for item in raw:

                if isinstance(item, dict):
                    name = item.get("ingredient") or item.get("name") or ""
                    measure = item.get("measure", "")
                    cleaned = f"{measure} {name}".strip()
                else:
                    cleaned = str(item)

                key = self.normalize(cleaned)

                if not key:
                    continue

                if key not in seen:
                    seen.add(key)
                    items.append(cleaned.strip())

        return sorted(items)