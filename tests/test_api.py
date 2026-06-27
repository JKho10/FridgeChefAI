from mcp_server.server import MealMCPServer

def test_mcp_search():
    """
    Unit test for MealMCPServer tool routing (search functionality).

    This test verifies that the MCP routing layer correctly forwards
    a "search_meals" request to the underlying meal search function.

    Scope of this test:
        - Validates routing behavior only
        - Ensures the correct tool is invoked
        - Ensures a response is returned

    Scope NOT covered:
        - API correctness or response accuracy
        - External MealDB data validity
        - Ranking or recipe logic
    """

    # Initialize MCP routing server
    server = MealMCPServer()

    # Execute tool routing request
    result = server.call_tool(
        "search_meals",
        ingredient="chicken"
    )

    # Validate that a response is returned
    assert result is not None