from mcp_server.tools import (
    search_meals_by_ingredient,
    get_meal_details
)

class MealMCPServer:

    """
    Simple tool routing layer for meal-related API calls.

    This class provides a single interface for accessing
    external meal data functions.
    """
    
    def call_tool(
        self,
        tool_name,
        **kwargs
    ):
        
        """
        Routes requests to the appropriate tool function.

        Supported tools:
        - search_meals: search recipes by ingredient
        - get_meal: retrieve full recipe details by ID

        Raises:
        - ValueError if an unknown tool name is provided
        """

        if tool_name == "search_meals":

            return search_meals_by_ingredient(
                kwargs["ingredient"]
            )

        if tool_name == "get_meal":

            return get_meal_details(
                kwargs["meal_id"]
            )

        raise ValueError(
            f"Unknown MCP tool: {tool_name}"
        )