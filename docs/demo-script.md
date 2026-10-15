# 90-second demo script

**0–10 sec — Problem**  GiftSense is a small agentic personalisation pipeline. It turns synthetic customer events into a catalogue-grounded gift suggestion and a draft message.

**10–25 sec — Scenario**  Load “Eid gift intent.” Point out the UAE market, AED budget, and browse/cart events. These are synthetic test events.

**25–45 sec — Run**  Click Run GiftSense. Explain the graph: signal interpretation, filtered catalogue retrieval, recommendation and critic checks, then message composition.

**45–60 sec — Reliability**  Show the product metadata and guardrail checks. Change the budget to AED 25 and rerun to demonstrate a safe no-match instead of inventing a cheap product.

**60–75 sec — Human approval**  Show that the output remains a draft until the checkbox is selected. Clarify that approval is simulated and no customer is contacted.

**75–90 sec — Engineering**  Show the execution trace, SQLite aggregate metrics, MCP server, tests, and README architecture. State the next step is a 30–50 scenario evaluation and vector-retrieval comparison.
