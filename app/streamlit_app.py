from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from giftsense.graph import run_giftsense
from giftsense.tools import get_campaign_metrics, catalogue


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="GiftSense | Agentic Personalisation Demo",
    page_icon="🎁",
    layout="wide",
)

st.title("GiftSense")
st.caption(
    "Synthetic-data agentic gift-personalisation demo · "
    "Not affiliated with any retailer"
)

st.info(
    "All customers, events, products, and campaign metrics shown here are "
    "synthetic. This demo never sends messages or contacts customers."
)


# --------------------------------------------------
# Load scenarios
# --------------------------------------------------

scenarios = json.loads(
    (ROOT / "data" / "scenarios.json").read_text(encoding="utf-8")
)

MARKETS = ["UAE", "UK", "US"]
OCCASIONS = [
    "eid",
    "ramadan",
    "national_day",
    "birthday",
    "anniversary",
    "thank_you",
    "new_job",
    "new_home",
    "new_baby",
]
LANGUAGES = ["English", "Arabic"]

left, right = st.columns([1, 1.25], gap="large")


# --------------------------------------------------
# Scenario input
# --------------------------------------------------

with left:
    st.subheader("1 · Scenario")

    scenario_name = st.selectbox(
        "Load a test scenario",
        [scenario["name"] for scenario in scenarios],
    )

    scenario = next(
        item for item in scenarios if item["name"] == scenario_name
    )

    market = st.selectbox(
        "Market",
        MARKETS,
        index=MARKETS.index(scenario["market"]),
    )

    occasion = st.selectbox(
        "Occasion",
        OCCASIONS,
        index=OCCASIONS.index(scenario["occasion"]),
    )

    budget = st.slider(
        "Maximum budget (AED)",
        min_value=25,
        max_value=250,
        value=int(scenario["budget_aed"]),
        step=5,
    )

    language = st.radio(
        "Draft language",
        LANGUAGES,
        horizontal=True,
        index=LANGUAGES.index(scenario["language"]),
    )

    events = st.data_editor(
        scenario["events"],
        num_rows="dynamic",
        width="stretch",
        key=f"events-{scenario_name}",
        column_config={
            "type": st.column_config.SelectboxColumn(
                options=[
                    "browse",
                    "cart_add",
                    "photo_upload",
                    "purchase",
                    "occasion_signal",
                ]
            ),
            "product_id": st.column_config.SelectboxColumn(
                options=[
                    product["product_id"] for product in catalogue()
                ]
            ),
        },
    )

    run = st.button(
        "Run GiftSense",
        type="primary",
        width="stretch",
    )


# --------------------------------------------------
# Agent output
# --------------------------------------------------

with right:
    st.subheader("2 · Agent output")

    if run:
        payload = {
            "market": market,
            "occasion": occasion,
            "budget_aed": budget,
            "language": language,
            "events": events,
        }

        st.session_state["result"] = run_giftsense(payload)
        st.session_state["approved"] = False

    result = st.session_state.get("result")

    if result:
        recommendation = result["recommendation"]

        if recommendation.get("product"):
            product = recommendation["product"]

            st.metric("Recommended product", product["name"])

            price_col, intent_col, candidates_col = st.columns(3)

            price_col.metric(
                "Price",
                f"AED {product['price_aed']}",
            )

            intent_col.metric(
                "Intent score",
                f"{result['intent']['intent_score']:.2f}",
            )

            candidates_col.metric(
                "Candidates",
                len(result["candidates"]),
            )

            st.write(recommendation["reason"])

            st.caption("Catalogue-grounded description")
            st.write(product["description"])

        else:
            st.warning(recommendation["reason"])

        st.markdown("**Message draft**")
        st.write(result["draft"])

        st.markdown("**Guardrail checks**")

        for check in result["checks"]:
            st.write("✓ " + check)

        st.warning(
            "Human approval required. Approval below is a local demo state "
            "only; nothing is sent."
        )

        approved = st.checkbox(
            "I approve this draft for the simulated workflow",
            value=st.session_state.get("approved", False),
            key="approval-check",
        )

        st.session_state["approved"] = approved

        if approved:
            st.success(
                "Approved in demo only. No external action was taken."
            )

        with st.expander("Execution trace"):
            for index, item in enumerate(result["trace"], start=1):
                st.write(
                    f"**{index}. {item['step']}** — {item['detail']}"
                )

        with st.expander("Retrieved candidates"):
            candidate_columns = [
                "product_id",
                "name",
                "price_aed",
                "markets",
                "occasions",
                "retrieval_score",
            ]

            candidate_rows = [
                {
                    key: item[key]
                    for key in candidate_columns
                    if key in item
                }
                for item in result["candidates"]
            ]

            st.dataframe(
                candidate_rows,
                width="stretch",
            )

    else:
        st.write(
            "Choose a scenario and click **Run GiftSense** "
            "to inspect the agent pipeline."
        )


# --------------------------------------------------
# Synthetic campaign metrics
# --------------------------------------------------

st.divider()

metrics_col, about_col = st.columns(2)

with metrics_col:
    st.subheader("3 · Synthetic campaign metrics")

    metrics = get_campaign_metrics()
    display_metrics = []

    for row in metrics:
        display_row = dict(row)

        impressions = display_row.get("impressions", 0) or 0
        clicks = display_row.get("clicks", 0) or 0
        conversions = display_row.get("conversions", 0) or 0

        display_row["CTR"] = (
            f"{clicks / impressions:.1%}"
            if impressions
            else "0%"
        )

        display_row["Conversion rate"] = (
            f"{conversions / clicks:.1%}"
            if clicks
            else "0%"
        )

        display_metrics.append(display_row)

    st.dataframe(
        display_metrics,
        hide_index=True,
        width="stretch",
    )


# --------------------------------------------------
# Engineering notes
# --------------------------------------------------

with about_col:
    st.subheader("4 · Engineering notes")

    st.markdown(
        "- **Orchestration:** LangGraph nodes for signal interpretation, "
        "retrieval, recommendation/critique, and message composition.\n"
        "- **Tools:** Local functions also exposed by a separate MCP server.\n"
        "- **Data:** Synthetic JSON catalogue and SQLite aggregate metrics.\n"
        "- **Safety:** Metadata filters, catalogue-grounded claims, and "
        "explicit human approval.\n"
        "- **Limit:** The current starter uses TF-IDF-based retrieval and "
        "template-based drafting, not production-grade semantic RAG or a "
        "live LLM integration."
    )