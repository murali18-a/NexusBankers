"""
FinPulse scoring engine.

Explainable-by-design Financial Health Score (0-100).
Every point is traceable to a weighted factor, so the score can always be
decomposed and explained — no black box.

Factors (weights sum to 1.0):
  - savings_ratio      0.25   how much of inflow is retained as savings
  - spending_control   0.20   spend volatility / discretionary discipline
  - debt_load          0.25   debt-to-income + EMI burden
  - payment_stability  0.20   regularity of income + on-time payments
  - liquidity_buffer   0.10   emergency-fund months of expenses covered
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List


WEIGHTS: Dict[str, float] = {
    "savings_ratio": 0.25,
    "spending_control": 0.20,
    "debt_load": 0.25,
    "payment_stability": 0.20,
    "liquidity_buffer": 0.10,
}

FACTOR_LABELS: Dict[str, str] = {
    "savings_ratio": "Savings",
    "spending_control": "Spending",
    "debt_load": "Debt load",
    "payment_stability": "Stability",
    "liquidity_buffer": "Liquidity",
}


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


@dataclass
class Factor:
    key: str
    label: str
    sub_score: float        # 0..100 for this factor alone
    weight: float
    contribution: float     # points this factor adds to the final score
    reason: str             # plain-language explanation


@dataclass
class ScoreResult:
    score: int
    band: str
    factors: List[Factor]
    raw: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def _band(score: int) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Good"
    if score >= 50:
        return "Fair"
    if score >= 35:
        return "Needs work"
    return "At risk"


def _savings_sub(m: dict) -> tuple[float, str]:
    # savings_rate: fraction of income saved (0..~0.5+)
    r = m["savings_rate"]
    sub = _clamp(r / 0.30) * 100  # 30% savings rate = full marks
    if r >= 0.30:
        reason = f"Strong: saving {r*100:.0f}% of income."
    elif r >= 0.15:
        reason = f"Moderate: saving {r*100:.0f}% of income; aim for 20%+."
    elif r > 0:
        reason = f"Low: only {r*100:.0f}% of income saved."
    else:
        reason = "No net savings — spending meets or exceeds income."
    return sub, reason


def _spending_sub(m: dict) -> tuple[float, str]:
    # spend_volatility: std/mean of monthly spend (0=steady, 1+=erratic)
    v = m["spend_volatility"]
    sub = _clamp(1 - v / 0.6) * 100  # volatility above 0.6 = poor control
    if v <= 0.15:
        reason = "Very consistent month-to-month spending."
    elif v <= 0.35:
        reason = "Reasonably steady spending pattern."
    else:
        reason = "Erratic spending — large month-to-month swings."
    return sub, reason


def _debt_sub(m: dict) -> tuple[float, str]:
    # debt_to_income: total EMIs / monthly income (0=none, 0.5+=heavy)
    d = m["debt_to_income"]
    sub = _clamp(1 - d / 0.50) * 100  # DTI at/above 50% = zero marks
    if d <= 0.15:
        reason = f"Light debt: EMIs are {d*100:.0f}% of income."
    elif d <= 0.35:
        reason = f"Manageable debt: EMIs are {d*100:.0f}% of income."
    else:
        reason = f"Heavy debt: EMIs are {d*100:.0f}% of income."
    return sub, reason


def _stability_sub(m: dict) -> tuple[float, str]:
    # income_regularity 0..1  and on_time_rate 0..1
    reg = m["income_regularity"]
    otr = m["on_time_rate"]
    sub = (0.5 * reg + 0.5 * otr) * 100
    if otr >= 0.95 and reg >= 0.8:
        reason = "Regular income and near-perfect on-time payments."
    elif otr >= 0.8:
        reason = f"Mostly on-time ({otr*100:.0f}%) with fairly steady income."
    else:
        reason = f"Missed/late payments ({(1-otr)*100:.0f}% of dues) hurt stability."
    return sub, reason


def _liquidity_sub(m: dict) -> tuple[float, str]:
    # emergency_months: months of expenses covered by liquid balance
    em = m["emergency_months"]
    sub = _clamp(em / 6.0) * 100  # 6 months = full marks
    if em >= 6:
        reason = f"Solid buffer: {em:.1f} months of expenses covered."
    elif em >= 3:
        reason = f"Partial buffer: {em:.1f} months covered; target 6."
    elif em > 0:
        reason = f"Thin buffer: only {em:.1f} months of expenses covered."
    else:
        reason = "No emergency buffer — vulnerable to income shocks."
    return sub, reason


_SUB_FNS = {
    "savings_ratio": _savings_sub,
    "spending_control": _spending_sub,
    "debt_load": _debt_sub,
    "payment_stability": _stability_sub,
    "liquidity_buffer": _liquidity_sub,
}


def compute_score(metrics: dict) -> ScoreResult:
    """
    metrics expects keys:
      savings_rate, spend_volatility, debt_to_income,
      income_regularity, on_time_rate, emergency_months
    """
    factors: List[Factor] = []
    total = 0.0
    for key, weight in WEIGHTS.items():
        sub, reason = _SUB_FNS[key](metrics)
        contribution = sub * weight  # points out of (weight*100)
        total += contribution
        factors.append(
            Factor(
                key=key,
                label=FACTOR_LABELS[key],
                sub_score=round(sub, 1),
                weight=weight,
                contribution=round(contribution, 2),
                reason=reason,
            )
        )
    score = int(round(total))
    return ScoreResult(score=score, band=_band(score), factors=factors, raw=metrics)


def simulate(metrics: dict, changes: dict) -> ScoreResult:
    """Apply changes to a copy of metrics and re-score (what-if)."""
    m = dict(metrics)
    m.update(changes)
    return compute_score(m)
