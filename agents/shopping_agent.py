import re

class ShoppingAgent:
    """
    Generates a clean, deduplicated grocery list.
    Fully normalized to prevent duplicates.
    """

    def normalize(self, text: str) -> str:
        text = str(text).lower().strip()
        text = re.sub(r"\d+", "", text)
        text = re.sub(r"[^a-z ]", " ", text)
        text = " ".join(text.split())
        return text

    def create_list(self, recipes):
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