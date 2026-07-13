import { useEffect, useState } from "react";
import { api } from "../api";
import { Gauge, FactorList, bandColor } from "./Ui";

const FIELDS = [
  { key: "savings_rate",      label: "Savings rate",            min: 0,   max: 0.45, step: 0.01, fmt: (v) => `${Math.round(v * 100)}%`,    icon: "💰" },
  { key: "spend_volatility",  label: "Spending volatility",     min: 0.05,max: 0.8,  step: 0.01, fmt: (v) => v.toFixed(2),                  icon: "📉" },
  { key: "debt_to_income",    label: "Debt-to-income (EMIs)",   min: 0,   max: 0.65, step: 0.01, fmt: (v) => `${Math.round(v * 100)}%`,    icon: "🏦" },
  { key: "income_regularity", label: "Income regularity",       min: 0.3, max: 1,    step: 0.01, fmt: (v) => `${Math.round(v * 100)}%`,    icon: "📅" },
  { key: "on_time_rate",      label: "On-time payments",        min: 0.5, max: 1,    step: 0.01, fmt: (v) => `${Math.round(v * 100)}%`,    icon: "✅" },
  { key: "emergency_months",  label: "Emergency fund (months)", min: 0,   max: 9,    step: 0.5,  fmt: (v) => `${v.toFixed(1)} mo`,          icon: "🛡️" },
];

const START = {
  savings_rate: 0.08, spend_volatility: 0.35, debt_to_income: 0.4,
  income_regularity: 0.8, on_time_rate: 0.85, emergency_months: 1.5,
};

export default function Simulator() {
  const [m, setM] = useState(START);
  const [base] = useState(START);
  const [result, setResult] = useState(null);
  const [baseScore, setBaseScore] = useState(null);

  useEffect(() => { api.score(base).then((r) => setBaseScore(r.score)); }, []);
  useEffect(() => {
    const t = setTimeout(() => api.score(m).then(setResult), 100);
    return () => clearTimeout(t);
  }, [m]);

  const delta = result && baseScore != null ? result.score - baseScore : 0;

  return (
    <div>
      <div className="page-kicker">What-if simulator</div>
      <div className="page-title">Model a Change, Watch the Score Move</div>

      <div className="grid" style={{ gridTemplateColumns: "1.15fr 1fr" }}>
        {/* Sliders */}
        <div className="card" style={{ padding: 28 }}>
          <div className="section-h">🎛️ Adjust the inputs</div>
          {FIELDS.map((f) => (
            <div className="sim-row" key={f.key}>
              <div className="sim-label">
                <span>{f.icon} {f.label}</span>
                <span>{f.fmt(m[f.key])}</span>
              </div>
              <input type="range" min={f.min} max={f.max} step={f.step} value={m[f.key]}
                onChange={(e) => setM({ ...m, [f.key]: parseFloat(e.target.value) })} />
            </div>
          ))}
          <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
            <button className="btn btn-ghost" onClick={() => setM(START)}>
              ↺ Reset
            </button>
            <button className="btn btn-ghost" onClick={() => setM({
              savings_rate: 0.28, spend_volatility: 0.12, debt_to_income: 0.10,
              income_regularity: 0.95, on_time_rate: 0.99, emergency_months: 6.5,
            })}>
              ⭐ Ideal profile
            </button>
          </div>
        </div>

        {/* Results */}
        <div>
          <div className="score-hero" style={{ marginBottom: 20 }}>
            <Gauge score={result?.score ?? 0} band={result?.band ?? "Fair"} />
            <div style={{ position: "relative", zIndex: 2 }}>
              <div className="band-pill" style={{ background: bandColor(result?.band), color: "#fff" }}>
                {result?.band ?? "…"}
              </div>
              <div style={{ marginTop: 14, fontSize: 15 }}>
                {delta === 0 ? (
                  <span className="delta-badge neutral">
                    Same as starting profile
                  </span>
                ) : delta > 0 ? (
                  <span className="delta-badge positive">
                    ▲ +{delta} points
                  </span>
                ) : (
                  <span className="delta-badge negative">
                    ▼ {delta} points
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="card" style={{ padding: 26 }}>
            <div className="section-h">📋 Live factor breakdown</div>
            {result && <FactorList factors={result.factors} />}
          </div>
        </div>
      </div>
    </div>
  );
}
