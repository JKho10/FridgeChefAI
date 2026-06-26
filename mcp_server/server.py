from mcp_server.tools import (
    search_meals_by_ingredient,
    get_meal_details
)

class MealMCPServer:

    """
    Simple tool routing layer for meal-related api calls.

    This class acts as a thin abstraction over external meal tools,
    providing a unified interface for recipe search and retrieval.

    It decouples the agent layer from direct tool implementations,
    making it easier to extend or replace backend data sources.
    """
    
    def call_tool(
        self,
        tool_name,
        **kwargs
    ):
        """
        Routes tool requests to the appropriate meal function.

        This method provides a single entry point for all meal-related
        tool operations. It validates the requested tool name and forwards
        arguments to the corresponding implementation.

        supported tools:
        - search_meals: searches recipes using a single ingredient
        - get_meal: retrieves full meal details by meal id

        args:
            tool_name (str): name of the tool to execute
            **kwargs: tool-specific parameters

        returns:
            dict or list: response from the underlying tool function

        raises:
            ValueError: if an unsupported tool name is provided
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