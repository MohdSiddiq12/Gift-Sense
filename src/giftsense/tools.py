from __future__ import annotations
import json, sqlite3
from pathlib import Path
from typing import Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[2]
CATALOGUE_PATH = ROOT / "data" / "catalogue.json"
DB_PATH = ROOT / "data" / "giftsense.db"
LOG_PATH = ROOT / "data" / "run_log.jsonl"


def catalogue() -> list[dict[str, Any]]:
    return json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))


def get_customer_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize the supplied synthetic event stream. No real customer data is used."""
    counts: dict[str, int] = {}
    product_ids: list[str] = []
    for event in events:
        kind = str(event.get("type", "unknown"))
        counts[kind] = counts.get(kind, 0) + 1
        if event.get("product_id"):
            product_ids.append(str(event["product_id"]))
    return {"event_count": len(events), "event_types": counts, "product_ids": product_ids,
            "has_cart_intent": counts.get("cart_add", 0) > 0,
            "has_photo_signal": counts.get("photo_upload", 0) > 0}


def search_catalogue(
    market: str,
    occasion: str,
    budget_aed: float,
    query: str = "",
) -> list[dict[str, Any]]:
    """Filter by hard constraints, then rank catalogue items using TF-IDF."""
    eligible = [
        item for item in catalogue()
        if market in item["markets"]
        and occasion in item["occasions"]
        and item["price_aed"] <= budget_aed
    ]

    if not eligible:
        return []

    documents = [
        " ".join([
            item["name"],
            item["category"],
            item["description"],
            " ".join(item["claims"]),
        ])
        for item in eligible
    ]

    if query.strip():
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
        )
        matrix = vectorizer.fit_transform(documents + [query])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    else:
        scores = [0.0] * len(eligible)

    ranked = [
        {**item, "retrieval_score": float(score)}
        for item, score in zip(eligible, scores)
    ]

    return sorted(
        ranked,
        key=lambda item: (-item["retrieval_score"], item["price_aed"]),
    )[:5]


def init_metrics_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        con.execute("CREATE TABLE IF NOT EXISTS campaign_metrics (campaign TEXT PRIMARY KEY, impressions INTEGER, clicks INTEGER, conversions INTEGER)")
        con.execute("INSERT OR IGNORE INTO campaign_metrics VALUES ('eid-gift-guide', 1200, 96, 18)")
        con.execute("INSERT OR IGNORE INTO campaign_metrics VALUES ('national-day-keepsakes', 850, 51, 9)")
        con.execute("INSERT OR IGNORE INTO campaign_metrics VALUES ('anniversary-personalisation', 980, 103, 22)")


def get_campaign_metrics() -> list[dict[str, Any]]:
    init_metrics_db()
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        return [dict(row) for row in con.execute("SELECT campaign, impressions, clicks, conversions FROM campaign_metrics ORDER BY conversions DESC")]


def log_run(payload: dict[str, Any]) -> str:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return "Run logged to local synthetic-demo log."
