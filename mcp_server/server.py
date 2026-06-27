from mcp_server.tools import (
    search_meals_by_ingredient,
    get_meal_details
)

class MealMCPServer:
    """
    MealMCPServer is a lightweight tool-routing abstraction layer
    for meal and recipe-related external API functions.

    This class serves as a decoupling layer between:
        - Agent logic (RecipeAgent, etc.)
        - External tool implementations (meal APIs)

    Responsibilities:
        - Provide a unified interface for meal-related operations
        - Route tool requests to correct backend functions
        - Hide implementation details of external APIs
        - Make backend tools replaceable without changing agent logic

    Supported tools:
        - search_meals: Search recipes by ingredient
        - get_meal: Retrieve full meal details by meal ID
    """
    def call_tool(self, tool_name, **kwargs):
        """
        Dispatch a meal-related tool request to the appropriate function.

        This method acts as a central router for all MCP (Meal Control Plane)
        operations, ensuring agents do not directly depend on external APIs.

        Args:
            tool_name (str):
                Name of the tool to execute.
                Supported values:
                    - "search_meals"
                    - "get_meal"

            **kwargs:
                Tool-specific arguments:
                    - search_meals:
                        ingredient (str)
                    - get_meal:
                        meal_id (str)

        Returns:
            dict | list:
                Raw response from the underlying MCP tool.

        Raises:
            ValueError:
                If an unsupported tool name is provided.
        """
        # Search by ingredient
        if tool_name == "search_meals":
            return search_meals_by_ingredient(
                kwargs["ingredient"]
            )

        # Get full meal details
        if tool_name == "get_meal":
            return get_meal_details(
                kwargs["meal_id"]
            )

        # Invalid tool
        raise ValueError(
            f"Unknown MCP tool: {tool_name}"
        )