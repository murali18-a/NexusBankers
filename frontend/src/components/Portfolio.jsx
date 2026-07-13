import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, Tooltip } from "recharts";
import { api } from "../api";
import { bandColor } from "./Ui";

const BANDS = [
  { value: "",            label: "All bands" },
  { value: "Excellent",   label: "Excellent" },
  { value: "Good",        label: "Good" },
  { value: "Fair",        label: "Fair" },
  { value: "Needs work",  label: "Needs work" },
  { value: "At risk",     label: "At risk" },
];

function barColor(bucket) {
  const n = +bucket;
  if (n >= 80) return "#02C39A";
  if (n >= 65) return "#00A896";
  if (n >= 50) return "#E9B44C";
  if (n >= 35) return "#E08A3C";
  return "#E07A5F";
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <div style={{ fontWeight: 700 }}>Score {label}–{+label + 9}</div>
      <div style={{ marginTop: 4, color: "rgba(255,255,255,.7)" }}>
        {payload[0].value.toLocaleString("en-IN")} customers
      </div>
    </div>
  );
};

export default function Portfolio({ onOpen }) {
  const [rows, setRows] = useState([]);
  const [stats, setStats] = useState(null);
  const [band, setBand] = useState("");
  const [total, setTotal] = useState(0);

  useEffect(() => { api.stats().then(setStats); }, []);
  useEffect(() => {
    api.customers(25, band).then((d) => { setRows(d.items); setTotal(d.total); });
  }, [band]);

  const hist = stats?.histogram.map((h) => ({
    range: `${h.bucket}`,
    count: h.count,
  })) || [];

  const statCards = [
    {
      label: "Customers scored",
      value: stats ? stats.total_customers.toLocaleString("en-IN") : "—",
      icon: "👥",
    },
    {
      label: "Average score",
      value: stats ? stats.avg_score : "—",
      icon: "📈",
    },
    {
      label: "At-risk customers",
      value: stats ? stats.bands["At risk"] || 0 : "—",
      icon: "⚠️",
      danger: true,
    },
  ];

  return (
    <div>
      <div className="page-kicker">Relationship manager view</div>
      <div className="page-title">Portfolio Health</div>

      {/* Stat cards */}
      <div className="grid stagger" style={{ gridTemplateColumns: "repeat(3,1fr)", marginBottom: 24 }}>
        {statCards.map((s) => (
          <div className="card" key={s.label} style={{ padding: "24px 22px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <div className="stat-label">{s.label}</div>
                <div className="big-stat" style={s.danger ? {
                  background: "linear-gradient(135deg, #E07A5F 0%, #E08A3C 100%)",
                  WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                } : undefined}>
                  {s.value}
                </div>
              </div>
              <div style={{ fontSize: 28, opacity: .6 }}>{s.icon}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Histogram */}
      <div className="card" style={{ padding: 26, marginBottom: 24 }}>
        <div className="section-h">📊 Score Distribution</div>
        <ResponsiveContainer width="100%" height={230}>
          <BarChart data={hist} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
            <XAxis dataKey="range" tick={{ fontSize: 12, fill: "#5A6B72" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 12, fill: "#5A6B72" }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(2,195,154,.06)", radius: 8 }} />
            <Bar dataKey="count" radius={[8, 8, 0, 0]} maxBarSize={48}>
              {hist.map((h, i) => (
                <Cell key={i} fill={barColor(h.range)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Customer table */}
      <div className="card" style={{ padding: 26 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <div className="section-h" style={{ margin: 0 }}>👤 Customers</div>
          <div className="filter-bar">
            {BANDS.map((b) => (
              <button
                key={b.value}
                className={`filter-pill ${band === b.value ? "active" : ""}`}
                onClick={() => setBand(b.value)}
              >
                {b.label}
              </button>
            ))}
          </div>
        </div>
        <p className="muted" style={{ marginBottom: 14 }}>
          {band ? `${total} in "${band}"` : `${total} total`} · click a row to open the score card
        </p>
        <table>
          <thead>
            <tr><th>ID</th><th>Name</th><th>Segment</th><th>Income</th><th>Score</th><th>Band</th></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr className="click" key={r.id} onClick={() => onOpen(r.id)}>
                <td className="mono" style={{ color: "var(--grey)" }}>#{r.id}</td>
                <td style={{ fontWeight: 600 }}>{r.name}</td>
                <td className="muted">{r.cohort.replace(/_/g, " ")}</td>
                <td className="mono">₹{r.monthly_income.toLocaleString("en-IN")}</td>
                <td className="mono" style={{ fontWeight: 800 }}>{r.score}</td>
                <td>
                  <span className="chip" style={{
                    background: bandColor(r.band) + "18",
                    color: bandColor(r.band),
                  }}>
                    {r.band}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
