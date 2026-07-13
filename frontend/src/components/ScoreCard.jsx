import { useEffect, useState } from "react";
import { api } from "../api";
import { Gauge, FactorList, Recommendations, LoadingSkeleton, bandColor } from "./Ui";

export default function ScoreCard({ customerId }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    setData(null); setErr(null);
    api.customer(customerId).then(setData).catch(() => setErr("Could not load customer."));
  }, [customerId]);

  if (err) return <div className="loading">{err}</div>;
  if (!data) return <LoadingSkeleton />;

  return (
    <div>
      <div className="page-kicker">Customer score card</div>
      <div className="page-title">{data.name}</div>

      <div className="score-hero" style={{ marginBottom: 24 }}>
        <Gauge score={data.score} band={data.band} />
        <div style={{ position: "relative", zIndex: 2 }}>
          <div className="band-pill" style={{ background: bandColor(data.band), color: "#fff" }}>
            {data.band}
          </div>
          <div style={{ fontSize: 15, color: "rgba(207,231,228,.85)", marginTop: 14, maxWidth: 440, lineHeight: 1.6 }}>
            Financial health for <strong style={{ color: "#fff" }}>{data.name}</strong>,
            a {data.cohort.replace(/_/g, " ")} earning ₹{data.monthly_income.toLocaleString("en-IN")}/month.
            Every point below is traceable to a factor — no black box.
          </div>
          <div className="metric-pills">
            <div className="metric-pill">
              💰 Savings <strong>{Math.round(data.metrics.savings_rate * 100)}%</strong>
            </div>
            <div className="metric-pill">
              📊 DTI <strong>{Math.round(data.metrics.debt_to_income * 100)}%</strong>
            </div>
            <div className="metric-pill">
              🛡️ Buffer <strong>{data.metrics.emergency_months.toFixed(1)} mo</strong>
            </div>
            <div className="metric-pill">
              ✅ On-time <strong>{Math.round(data.metrics.on_time_rate * 100)}%</strong>
            </div>
          </div>
        </div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <div className="card" style={{ padding: 26 }}>
          <div className="section-h">📋 Why this score</div>
          <FactorList factors={data.factors} />
        </div>
        <div className="card" style={{ padding: 26 }}>
          <div className="section-h">🚀 Recommended for you</div>
          <Recommendations recs={data.recommendations} />
        </div>
      </div>
    </div>
  );
}
