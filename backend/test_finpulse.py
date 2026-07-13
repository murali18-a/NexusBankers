"""Sanity tests for the FinPulse scoring + recommender engine."""
from app.scoring import compute_score, WEIGHTS, simulate
from app.recommender import recommend

HEALTHY = dict(savings_rate=0.30, spend_volatility=0.12, debt_to_income=0.10,
               income_regularity=0.95, on_time_rate=0.99, emergency_months=6.5)
STRESSED = dict(savings_rate=0.04, spend_volatility=0.55, debt_to_income=0.50,
                income_regularity=0.70, on_time_rate=0.80, emergency_months=0.5)

def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

def test_healthy_beats_stressed():
    assert compute_score(HEALTHY).score > compute_score(STRESSED).score

def test_score_in_range():
    for m in (HEALTHY, STRESSED):
        assert 0 <= compute_score(m).score <= 100

def test_contributions_reconstruct_score():
    r = compute_score(STRESSED)
    total = sum(f.contribution for f in r.factors)
    assert abs(total - r.score) < 1.0  # rounding only

def test_recommendations_have_positive_uplift():
    recs = recommend(STRESSED, top_n=4)
    assert len(recs) > 0
    assert all(x["projected_gain"] > 0 for x in recs)
    # ranked descending
    gains = [x["projected_gain"] for x in recs]
    assert gains == sorted(gains, reverse=True)

def test_simulate_reducing_debt_helps():
    before = compute_score(STRESSED).score
    after = simulate(STRESSED, {"debt_to_income": 0.20}).score
    assert after > before

if __name__ == "__main__":
    import sys
    fns = [v for k, v in list(globals().items()) if k.startswith("test_")]
    ok = 0
    for fn in fns:
        try:
            fn(); ok += 1; print(f"PASS {fn.__name__}")
        except AssertionError:
            print(f"FAIL {fn.__name__}")
    print(f"{ok}/{len(fns)} passed")
    sys.exit(0 if ok == len(fns) else 1)
