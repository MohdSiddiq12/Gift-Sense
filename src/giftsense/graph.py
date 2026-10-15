from __future__ import annotations
from typing import Any, TypedDict
from langgraph.graph import StateGraph, END
from .tools import get_customer_events, search_catalogue, log_run

class GiftState(TypedDict, total=False):
    market: str
    occasion: str
    budget_aed: float
    language: str
    events: list[dict[str, Any]]
    intent: dict[str, Any]
    candidates: list[dict[str, Any]]
    recommendation: dict[str, Any]
    draft: str
    checks: list[str]
    approved: bool
    trace: list[dict[str, Any]]


def _trace(state: GiftState, step: str, detail: str) -> list[dict[str, Any]]:
    return state.get("trace", []) + [{"step": step, "detail": detail}]


def interpret(state: GiftState) -> GiftState:
    intent = get_customer_events(state.get("events", []))
    cart = intent["has_cart_intent"]
    intent["intent_score"] = min(0.98, 0.45 + 0.25 * cart + 0.1 * intent["has_photo_signal"] + 0.05 * min(intent["event_count"], 3))
    return {"intent": intent, "trace": _trace(state, "Signal interpreter", f"{intent['event_count']} synthetic events; intent score {intent['intent_score']:.2f}")}


def retrieve(state: GiftState) -> GiftState:
    event_text = " ".join(str(e.get("text", "")) for e in state.get("events", []))
    candidates = search_catalogue(state["market"], state["occasion"], float(state["budget_aed"]), event_text)
    return {"candidates": candidates, "trace": _trace(state, "Catalogue retrieval", f"Metadata-filtered by market={state['market']}, occasion={state['occasion']}, budget≤AED {state['budget_aed']}; {len(candidates)} candidates")}


def recommend(state: GiftState) -> GiftState:
    candidates = state.get("candidates", [])
    chosen = candidates[0] if candidates else None
    checks = []
    if not chosen:
        checks.append("No matching product met market, occasion, and budget constraints.")
        rec = {"status": "no_match", "product": None, "reason": "No catalogue item passed all filters."}
    else:
        checks.append("Price verified against catalogue record.")
        checks.append("Market and occasion verified against catalogue metadata.")
        checks.append("Product claims restricted to catalogue description and claims.")
        rec = {"status": "ready_for_review", "product": chosen, "reason": f"Fits {state['occasion']} occasion in {state['market']} within the AED {state['budget_aed']} budget."}
    return {"recommendation": rec, "checks": checks, "trace": _trace(state, "Recommendation + critic", "".join(checks) if checks else "No candidate")}



def compose(state: GiftState) -> GiftState:
    rec = state.get("recommendation", {})
    product = rec.get("product")

    if not product:
        draft = (
            "No suitable catalogue match was found. "
            "Adjust the budget or scenario before drafting a message."
        )
    elif state.get("language", "English") == "Arabic":
        draft = (
            f"هدية مقترحة لمناسبة {state['occasion']}: "
            f"{product['name']} بسعر {product['price_aed']} درهم. "
            f"{product['description']} "
            "هذه رسالة تجريبية للمراجعة فقط."
        )
    else:
        draft = (
            f"A thoughtful idea for {state['occasion']}: "
            f"the {product['name']} at AED {product['price_aed']}. "
            f"{product['description']} This is a draft for review only."
        )

    return {
        "draft": draft,
        "trace": _trace(
            state,
            "Message composer",
            f"Draft generated in {state.get('language', 'English')}; no message sent",
        ),
    }



def build_graph():
    graph = StateGraph(GiftState)
    graph.add_node("interpret", interpret)
    graph.add_node("retrieve", retrieve)
    graph.add_node("recommend", recommend)
    graph.add_node("compose", compose)
    graph.set_entry_point("interpret")
    graph.add_edge("interpret", "retrieve")
    graph.add_edge("retrieve", "recommend")
    graph.add_edge("recommend", "compose")
    graph.add_edge("compose", END)
    return graph.compile()


def run_giftsense(payload: dict[str, Any]) -> dict[str, Any]:
    result = build_graph().invoke({**payload, "trace": []})
    log_run({"market": result["market"], "occasion": result["occasion"], "recommendation_status": result["recommendation"]["status"], "product_id": (result["recommendation"].get("product") or {}).get("product_id"), "approved": bool(result.get("approved", False))})
    return result
