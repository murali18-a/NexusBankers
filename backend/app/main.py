"""
FinPulse FastAPI backend.

Endpoints:
  GET  /                          health check
  GET  /customers                 list customers (paginated, filter by band)
  GET  /customers/{id}            full score card for one customer
  POST /score                     score arbitrary metrics
  POST /recommend                 recommendations for arbitrary metrics
  POST /simulate                  what-if: apply changes and re-score
  GET  /stats                     portfolio benchmarking stats
"""

from __future__ import annotations
import os
import sqlite3
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .scoring import compute_score, simulate, WEIGHTS
from .recommender import recommend

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "finpulse.db")

app = FastAPI(title="FinPulse API", version="1.0.0",
              description="Explainable Financial Health Score — IDBI Innovate 2026")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

METRIC_KEYS = ["savings_rate", "spend_volatility", "debt_to_income",
               "income_regularity", "on_time_rate", "emergency_months"]


class Metrics(BaseModel):
    savings_rate: float = Field(..., ge=-0.1, le=0.6)
    spend_volatility: float = Field(..., ge=0.0, le=1.0)
    debt_to_income: float = Field(..., ge=0.0, le=1.0)
    income_regularity: float = Field(..., ge=0.0, le=1.0)
    on_time_rate: float = Field(..., ge=0.0, le=1.0)
    emergency_months: float = Field(..., ge=0.0, le=12.0)


class SimulateReq(BaseModel):
    metrics: Metrics
    changes: dict


def _con():
    if not os.path.exists(DB_PATH):
        raise HTTPException(503, "Database not built. Run: python -m app.generate_data")
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _row_metrics(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in METRIC_KEYS}


@app.get("/")
def root():
    return {"service": "FinPulse API", "status": "ok", "weights": WEIGHTS}


@app.get("/customers")
def list_customers(
    limit: int = Query(20, le=100),
    offset: int = 0,
    band: Optional[str] = None,
):
    con = _con()
    q = "SELECT id, name, cohort, monthly_income, score, band FROM customers"
    params: List = []
    if band:
        q += " WHERE band = ?"
        params.append(band)
    q += " ORDER BY id LIMIT ? OFFSET ?"
    params += [limit, offset]
    rows = con.execute(q, params).fetchall()
    total = con.execute("SELECT COUNT(*) c FROM customers").fetchone()["c"]
    con.close()
    return {"total": total, "items": [dict(r) for r in rows]}


@app.get("/customers/{cid}")
def get_customer(cid: int):
    con = _con()
    row = con.execute("SELECT * FROM customers WHERE id = ?", (cid,)).fetchone()
    con.close()
    if not row:
        raise HTTPException(404, "Customer not found")
    metrics = _row_metrics(row)
    result = compute_score(metrics)
    recs = recommend(metrics, top_n=4)
    return {
        "id": row["id"],
        "name": row["name"],
        "cohort": row["cohort"],
        "monthly_income": row["monthly_income"],
        "metrics": metrics,
        "score": result.score,
        "band": result.band,
        "factors": [f.__dict__ for f in result.factors],
        "recommendations": recs,
    }


@app.post("/score")
def score(m: Metrics):
    r = compute_score(m.dict())
    return {"score": r.score, "band": r.band, "factors": [f.__dict__ for f in r.factors]}


@app.post("/recommend")
def recommend_ep(m: Metrics):
    return {"recommendations": recommend(m.dict(), top_n=4)}


@app.post("/simulate")
def simulate_ep(req: SimulateReq):
    base = compute_score(req.metrics.dict())
    after = simulate(req.metrics.dict(), req.changes)
    return {
        "base_score": base.score,
        "new_score": after.score,
        "delta": after.score - base.score,
        "band": after.band,
        "factors": [f.__dict__ for f in after.factors],
    }


@app.get("/stats")
def stats():
    con = _con()
    total = con.execute("SELECT COUNT(*) c FROM customers").fetchone()["c"]
    avg = con.execute("SELECT AVG(score) a FROM customers").fetchone()["a"]
    bands = con.execute(
        "SELECT band, COUNT(*) c FROM customers GROUP BY band"
    ).fetchall()
    # histogram in 10-pt buckets
    hist = con.execute("""
        SELECT (score/10)*10 AS bucket, COUNT(*) c
        FROM customers GROUP BY bucket ORDER BY bucket
    """).fetchall()
    con.close()
    return {
        "total_customers": total,
        "avg_score": round(avg, 1),
        "bands": {r["band"]: r["c"] for r in bands},
        "histogram": [{"bucket": r["bucket"], "count": r["c"]} for r in hist],
    }
