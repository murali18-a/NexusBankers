# FinPulse — Explainable Financial Health Score

**IDBI Innovate 2026 · Problem Statement 3 · Team NexusBankers**

FinPulse turns the data a bank already holds into a clear, explainable
**Financial Health Score (0–100)** for every retail customer — with a
factor-by-factor breakdown and personalised, prioritised recommendations.
No black box: every point is traceable to a weighted factor.

## What's inside

```
finpulse/
├── backend/          FastAPI + explainable scoring + recommender + synthetic data
│   └── app/
│       ├── scoring.py        # weighted, explainable 0–100 score
│       ├── recommender.py    # ranked actions with simulated score uplift
│       ├── generate_data.py  # synthetic SQLite customer DB (6 cohorts)
│       └── main.py           # REST API
└── frontend/         React + Vite dashboard (score card, RM portfolio, simulator)
```

## Scoring model (explainable by design)

Five weighted factors, weights sum to 1.0:

| Factor | Weight | Signal |
|---|---|---|
| Savings ratio | 0.25 | share of inflow retained as savings |
| Debt load | 0.25 | debt-to-income / EMI burden |
| Spending control | 0.20 | month-to-month spend volatility |
| Payment stability | 0.20 | income regularity + on-time payment rate |
| Liquidity buffer | 0.10 | months of expenses covered by liquid balance |

Final score = Σ (factor sub-score × weight). Because it's additive, the score
is always decomposable — the exact contribution of every factor is returned
with each response, which is what makes the recommendations trustworthy.

## Run it locally

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m app.generate_data --n 5000     # build synthetic DB
uvicorn app.main:app --reload            # http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                              # http://localhost:5173
# point at the API:
# VITE_API_URL=http://localhost:8000 npm run dev
```

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/customers` | list customers (filter by band) |
| GET | `/customers/{id}` | full score card + factors + recommendations |
| POST | `/score` | score arbitrary metrics |
| POST | `/recommend` | ranked actions for arbitrary metrics |
| POST | `/simulate` | what-if: apply changes, re-score |
| GET | `/stats` | portfolio benchmarking distribution |

## Benchmarking (5,000 synthetic customers)

- Score computed in **< 5 ms** per customer (pure Python, no model load).
- Realistic distribution across six behavioural cohorts (savers, over-leveraged,
  volatile spenders, thin-buffer, stable earners, young starters).
- **100% explainable** — every score reproducible from its factor contributions.
- Top-3 recommendations yield an average projected uplift of **+8 to +12 points**.

## Team

NexusBankers — Murali A (lead) · Naveenkumar S · Mohankumar K · Praveen K
