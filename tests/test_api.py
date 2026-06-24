from mcp_server.server import MealMCPServer

def test_mcp_search():

    """
    Ensures the MCP server correctly routes
    a search request to the underlying tool.
    """

    server = MealMCPServer()

    result = server.call_tool(
        "search_meals",
        ingredient="chicken"
    )

    assert result is not None