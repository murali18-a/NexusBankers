import { useState } from "react";
import Portfolio from "./components/Portfolio";
import ScoreCard from "./components/ScoreCard";
import Simulator from "./components/Simulator";

const NAV = [
  { id: "portfolio", label: "Portfolio", icon: "📊" },
  { id: "card",      label: "Score Card", icon: "🎯" },
  { id: "sim",       label: "What-if Simulator", icon: "⚡" },
];

export default function App() {
  const [view, setView] = useState("portfolio");
  const [customerId, setCustomerId] = useState(12);

  const open = (id) => { setCustomerId(id); setView("card"); };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">💳</div>
          Fin<span>Pulse</span>
        </div>
        <div className="brand-sub">IDBI Innovate 2026</div>

        {NAV.map((n) => (
          <div
            key={n.id}
            className={`nav-item ${view === n.id ? "active" : ""}`}
            onClick={() => setView(n.id)}
          >
            <span className="nav-icon">{n.icon}</span>
            {n.label}
          </div>
        ))}

        <div className="sidebar-foot">
          Explainable Financial Health Score.<br />
          Team NexusBankers.<br />
          Runs on the bank's own data — no black box.
        </div>
      </aside>

      <main className="main" key={view}>
        {view === "portfolio" && <Portfolio onOpen={open} />}
        {view === "card" && <ScoreCard customerId={customerId} />}
        {view === "sim" && <Simulator />}
      </main>
    </div>
  );
}
