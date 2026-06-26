from mcp_server.server import MealMCPServer

def test_mcp_search():
    """
    Tests that the mcp server correctly routes a search request.

    This unit test validates that the tool routing layer can successfully
    forward a "search_meals" request to the underlying meal search function
    and return a non-null response.

    It does not validate api correctness, only routing behavior.
    """

    server = MealMCPServer()

    # Call the mcp routing layer with a valid tool request
    result = server.call_tool(
        "search_meals",
        ingredient="chicken"
    )

    # Ensure the response is not empty or null
    assert result is not None