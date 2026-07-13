"""
Synthetic data generator for FinPulse PoC.

Creates a SQLite database of realistic retail-banking customer profiles with
derived financial metrics, spanning several behavioural cohorts so the score
distribution is meaningful for benchmarking:

  - disciplined_saver
  - stable_earner
  - over_leveraged
  - volatile_spender
  - thin_buffer
  - young_starter

Run:  python -m app.generate_data --n 5000
"""

from __future__ import annotations
import argparse
import os
import random
import sqlite3
from typing import Dict

from .scoring import compute_score
from .recommender import recommend

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "finpulse.db")

FIRST = ["Aarav", "Vivaan", "Diya", "Ananya", "Ishaan", "Kavya", "Rohan",
         "Meera", "Arjun", "Sana", "Karthik", "Nisha", "Dev", "Riya",
         "Aditya", "Tara", "Vikram", "Pooja", "Sanjay", "Lakshmi"]
LAST = ["Sharma", "Iyer", "Reddy", "Nair", "Gupta", "Menon", "Rao",
        "Patel", "Krishnan", "Das", "Verma", "Pillai", "Bose", "Kumar"]

COHORTS = [
    "disciplined_saver", "stable_earner", "over_leveraged",
    "volatile_spender", "thin_buffer", "young_starter",
]


def _round(x, n=3):
    return round(x, n)


def _profile(cohort: str) -> Dict[str, float]:
    """Return a metrics dict for a customer of the given cohort."""
    g = random.gauss
    u = random.uniform
    if cohort == "disciplined_saver":
        m = dict(savings_rate=g(0.28, 0.05), spend_volatility=g(0.15, 0.05),
                 debt_to_income=g(0.12, 0.05), income_regularity=g(0.9, 0.05),
                 on_time_rate=g(0.98, 0.02), emergency_months=g(6.5, 1.5))
    elif cohort == "stable_earner":
        m = dict(savings_rate=g(0.18, 0.05), spend_volatility=g(0.20, 0.06),
                 debt_to_income=g(0.22, 0.06), income_regularity=g(0.92, 0.04),
                 on_time_rate=g(0.95, 0.04), emergency_months=g(4.0, 1.2))
    elif cohort == "over_leveraged":
        m = dict(savings_rate=g(0.06, 0.04), spend_volatility=g(0.30, 0.08),
                 debt_to_income=g(0.48, 0.08), income_regularity=g(0.85, 0.08),
                 on_time_rate=g(0.82, 0.08), emergency_months=g(1.2, 0.8))
    elif cohort == "volatile_spender":
        m = dict(savings_rate=g(0.10, 0.05), spend_volatility=g(0.50, 0.10),
                 debt_to_income=g(0.28, 0.08), income_regularity=g(0.70, 0.10),
                 on_time_rate=g(0.85, 0.08), emergency_months=g(2.0, 1.0))
    elif cohort == "thin_buffer":
        m = dict(savings_rate=g(0.12, 0.05), spend_volatility=g(0.25, 0.07),
                 debt_to_income=g(0.25, 0.07), income_regularity=g(0.88, 0.06),
                 on_time_rate=g(0.92, 0.05), emergency_months=g(0.6, 0.5))
    else:  # young_starter
        m = dict(savings_rate=g(0.14, 0.06), spend_volatility=g(0.35, 0.10),
                 debt_to_income=g(0.18, 0.08), income_regularity=g(0.65, 0.12),
                 on_time_rate=g(0.88, 0.07), emergency_months=g(1.5, 1.0))

    # clamp to sane ranges
    m["savings_rate"] = _round(max(-0.05, min(0.45, m["savings_rate"])))
    m["spend_volatility"] = _round(max(0.05, min(0.80, m["spend_volatility"])))
    m["debt_to_income"] = _round(max(0.0, min(0.65, m["debt_to_income"])))
    m["income_regularity"] = _round(max(0.3, min(1.0, m["income_regularity"])))
    m["on_time_rate"] = _round(max(0.5, min(1.0, m["on_time_rate"])))
    m["emergency_months"] = _round(max(0.0, min(9.0, m["emergency_months"])), 1)
    return m


def build(n: int, seed: int = 42) -> None:
    random.seed(seed)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT, cohort TEXT, monthly_income INTEGER,
            savings_rate REAL, spend_volatility REAL, debt_to_income REAL,
            income_regularity REAL, on_time_rate REAL, emergency_months REAL,
            score INTEGER, band TEXT
        )
    """)
    rows = []
    for i in range(1, n + 1):
        cohort = random.choice(COHORTS)
        m = _profile(cohort)
        income = random.choice([25000, 35000, 45000, 60000, 80000, 120000])
        res = compute_score(m)
        name = f"{random.choice(FIRST)} {random.choice(LAST)}"
        rows.append((
            i, name, cohort, income,
            m["savings_rate"], m["spend_volatility"], m["debt_to_income"],
            m["income_regularity"], m["on_time_rate"], m["emergency_months"],
            res.score, res.band,
        ))
    cur.executemany(
        "INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows
    )
    con.commit()

    # quick distribution report
    cur.execute("SELECT band, COUNT(*) FROM customers GROUP BY band ORDER BY MIN(score)")
    dist = cur.fetchall()
    cur.execute("SELECT AVG(score), MIN(score), MAX(score) FROM customers")
    avg, mn, mx = cur.fetchone()
    con.close()

    print(f"Built {n} customers -> {os.path.abspath(DB_PATH)}")
    print(f"Score: avg={avg:.1f}  min={mn}  max={mx}")
    print("Band distribution:")
    for band, cnt in dist:
        print(f"  {band:12s} {cnt:5d}  ({cnt/n*100:4.1f}%)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    build(args.n, args.seed)
