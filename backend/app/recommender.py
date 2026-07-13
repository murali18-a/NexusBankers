"""
FinPulse recommendation engine.

For a given customer's metrics, generate candidate actions, simulate each
action's effect on the score, and return the top-N ranked by projected uplift.
Every recommendation carries a concrete, personalised projected point gain.
"""

from __future__ import annotations
from typing import Callable, Dict, List
from .scoring import compute_score


# A candidate action = (id, title, why, mutation function on metrics)
def _apply(metrics: dict, **delta) -> dict:
    m = dict(metrics)
    for k, v in delta.items():
        m[k] = v
    return m


CANDIDATES: List[dict] = [
    {
        "id": "boost_savings",
        "title": "Set up an auto-transfer to a recurring deposit",
        "why": "Automating savings lifts your savings ratio, the single biggest score factor.",
        "applies": lambda m: m["savings_rate"] < 0.25,
        "mutate": lambda m: _apply(m, savings_rate=min(0.30, m["savings_rate"] + 0.08)),
    },
    {
        "id": "cut_high_interest_debt",
        "title": "Clear high-interest card dues first",
        "why": "Reducing EMI burden directly improves your debt-load factor.",
        "applies": lambda m: m["debt_to_income"] > 0.20,
        "mutate": lambda m: _apply(m, debt_to_income=max(0.0, m["debt_to_income"] - 0.12)),
    },
    {
        "id": "emergency_fund",
        "title": "Build a 3-month emergency fund",
        "why": "A liquidity buffer protects your score against income shocks.",
        "applies": lambda m: m["emergency_months"] < 4,
        "mutate": lambda m: _apply(m, emergency_months=min(6.0, m["emergency_months"] + 2.5)),
    },
    {
        "id": "steady_spending",
        "title": "Set a monthly spending cap on discretionary categories",
        "why": "Smoothing month-to-month spend improves your spending-control factor.",
        "applies": lambda m: m["spend_volatility"] > 0.25,
        "mutate": lambda m: _apply(m, spend_volatility=max(0.10, m["spend_volatility"] - 0.15)),
    },
    {
        "id": "autopay_bills",
        "title": "Enable auto-pay for EMIs and bills",
        "why": "On-time payments strengthen your stability factor and avoid late fees.",
        "applies": lambda m: m["on_time_rate"] < 0.95,
        "mutate": lambda m: _apply(m, on_time_rate=min(1.0, m["on_time_rate"] + 0.10)),
    },
    {
        "id": "consolidate_income",
        "title": "Route irregular income through one salary account",
        "why": "More regular income inflow raises your stability factor.",
        "applies": lambda m: m["income_regularity"] < 0.8,
        "mutate": lambda m: _apply(m, income_regularity=min(1.0, m["income_regularity"] + 0.15)),
    },
]


def recommend(metrics: dict, top_n: int = 4) -> List[dict]:
    base = compute_score(metrics).score
    scored: List[dict] = []
    for c in CANDIDATES:
        if not c["applies"](metrics):
            continue
        new_metrics = c["mutate"](metrics)
        projected = compute_score(new_metrics).score
        uplift = projected - base
        if uplift <= 0:
            continue
        scored.append(
            {
                "id": c["id"],
                "title": c["title"],
                "why": c["why"],
                "projected_gain": uplift,
                "projected_score": projected,
            }
        )
    scored.sort(key=lambda x: x["projected_gain"], reverse=True)
    return scored[:top_n]
