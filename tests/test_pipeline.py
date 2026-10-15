import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from giftsense.graph import run_giftsense


def test_recommendation_respects_budget_market_and_occasion():
    result = run_giftsense({"market":"UAE", "occasion":"eid", "budget_aed":130, "language":"English", "events":[{"type":"cart_add", "product_id":"GS-004", "text":"added calligraphy mug"}]})
    product = result["recommendation"]["product"]
    assert product["price_aed"] <= 130
    assert "UAE" in product["markets"]
    assert "eid" in product["occasions"]


def test_no_match_when_budget_too_low():
    result = run_giftsense({"market":"US", "occasion":"birthday", "budget_aed":20, "language":"English", "events":[]})
    assert result["recommendation"]["status"] == "no_match"
    assert result["recommendation"]["product"] is None


def test_message_is_draft_not_sent():
    result = run_giftsense({"market":"UK", "occasion":"anniversary", "budget_aed":160, "language":"English", "events":[]})
    assert "draft" in result["draft"].lower() or "review" in result["draft"].lower()

from giftsense.tools import search_catalogue


def test_retrieval_ranks_relevant_product_and_respects_filters():
    results = search_catalogue(
        market="UAE",
        occasion="eid",
        budget_aed=130,
        query="calligraphy mug",
    )

    assert results
    assert results[0]["product_id"] == "GS-004"
    assert all(item["price_aed"] <= 130 for item in results)
    assert all("UAE" in item["markets"] for item in results)
    assert all("eid" in item["occasions"] for item in results)
