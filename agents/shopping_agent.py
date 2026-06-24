class ShoppingAgent:

    """
    Generates a consolidated grocery list from selected recipes.
    """

    def create_list(self, recipes):

        """
        Combines ingredients from all recipes and removes duplicates.

        Returns:
        A sorted list of unique grocery items.
        """

        items = []

        for r in recipes:
            items.extend(r.get("ingredients", []))

        return sorted(list(set(items)))