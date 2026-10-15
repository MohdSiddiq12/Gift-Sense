"""MCP tool server for GiftSense. Run with: python -m giftsense.mcp_server"""
from mcp.server.fastmcp import FastMCP
from .tools import get_customer_events, search_catalogue, get_campaign_metrics, log_run

mcp = FastMCP("GiftSense synthetic personalization tools")

@mcp.tool()
def customer_events(events: list[dict]) -> dict:
    """Summarize synthetic browse, cart, and photo events."""
    return get_customer_events(events)

@mcp.tool()
def catalogue_search(market: str, occasion: str, budget_aed: float, query: str = "") -> list[dict]:
    """Retrieve catalogue items filtered by market, occasion, and maximum budget."""
    return search_catalogue(market, occasion, budget_aed, query)

@mcp.tool()
def campaign_metrics() -> list[dict]:
    """Read aggregate metrics from the local synthetic SQLite campaign database."""
    return get_campaign_metrics()

@mcp.tool()
def log_demo_run(payload: dict) -> str:
    """Log a synthetic demo run locally; this does not contact customers."""
    return log_run(payload)

if __name__ == "__main__":
    mcp.run(transport="stdio")
