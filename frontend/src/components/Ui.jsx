import { useEffect, useRef, useState } from "react";

/* ── Color maps ──────────────────────────────────────────── */
const FACTOR_COLORS = {
  savings_ratio:     ["#028090", "#02C39A"],
  spending_control:  ["#00A896", "#02C39A"],
  debt_load:         ["#0B7A8C", "#028090"],
  payment_stability: ["#028090", "#00A896"],
  liquidity_buffer:  ["#3AAFA9", "#02C39A"],
};

const BAND_COLORS = {
  Excellent:    "#02C39A",
  Good:         "#00A896",
  Fair:         "#E9B44C",
  "Needs work": "#E08A3C",
  "At risk":    "#E07A5F",
};

export function bandColor(b) {
  return BAND_COLORS[b] || "#5A6B72";
}

/* ── Animated number counter ─────────────────────────────── */
function useAnimatedNumber(target, duration = 800) {
  const [display, setDisplay] = useState(0);
  const rafRef = useRef(null);

  useEffect(() => {
    const start = display;
    const diff = target - start;
    if (diff === 0) return;
    const startTime = performance.now();

    function tick(now) {
      const elapsed = now - startTime;
      const t = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const ease = 1 - Math.pow(1 - t, 3);
      setDisplay(Math.round(start + diff * ease));
      if (t < 1) rafRef.current = requestAnimationFrame(tick);
    }
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target]);

  return display;
}

/* ── SVG Gauge ───────────────────────────────────────────── */
export function Gauge({ score, band, size = 154 }) {
  const r = size / 2 - 14;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score)) / 100;
  const col = bandColor(band);
  const animScore = useAnimatedNumber(score);

  return (
    <div className="gauge" style={{ position: "relative", width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        {/* track */}
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke="rgba(255,255,255,.1)" strokeWidth="14" />
        {/* glow layer */}
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={col} strokeWidth="14" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - pct)}
          style={{
            transition: "stroke-dashoffset 1s cubic-bezier(.4,0,.2,1)",
            filter: `drop-shadow(0 0 8px ${col}66)`,
          }}
          opacity="0.35" />
        {/* main arc */}
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={col} strokeWidth="14" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - pct)}
          style={{ transition: "stroke-dashoffset 1s cubic-bezier(.4,0,.2,1)" }} />
      </svg>
      <div style={{
        position: "absolute", inset: 0, display: "flex",
        flexDirection: "column", alignItems: "center", justifyContent: "center",
      }}>
        <div style={{
          fontSize: size * 0.3, fontWeight: 900, lineHeight: 1, color: "#fff",
          letterSpacing: "-2px",
        }}>
          {animScore}
        </div>
        <div style={{ fontSize: 12, color: "rgba(255,255,255,.45)", fontWeight: 500 }}>/ 100</div>
      </div>
    </div>
  );
}

/* ── Factor list ─────────────────────────────────────────── */
export function FactorList({ factors }) {
  return (
    <div>
      {factors.map((f) => {
        const [c1, c2] = FACTOR_COLORS[f.key] || ["#028090", "#02C39A"];
        return (
          <div className="factor-row" key={f.key}>
            <div className="factor-name">{f.label}</div>
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{
                  width: `${f.sub_score}%`,
                  background: `linear-gradient(90deg, ${c1}, ${c2})`,
                }}
              />
            </div>
            <div className="factor-val">{Math.round(f.sub_score)}</div>
            <div className="factor-reason">{f.reason}</div>
          </div>
        );
      })}
    </div>
  );
}

/* ── Recommendations ─────────────────────────────────────── */
export function Recommendations({ recs }) {
  const gradients = [
    "linear-gradient(135deg, #028090, #02C39A)",
    "linear-gradient(135deg, #00A896, #3AAFA9)",
    "linear-gradient(135deg, #0B7A8C, #028090)",
    "linear-gradient(135deg, #02C39A, #00A896)",
  ];
  if (!recs || recs.length === 0)
    return <p className="muted" style={{ padding: "20px 0" }}>✅ No actions needed — this profile is already healthy.</p>;
  return (
    <div>
      {recs.map((r, i) => (
        <div className="rec" key={r.id}>
          <div className="rec-num" style={{ background: gradients[i % gradients.length] }}>
            {i + 1}
          </div>
          <div className="rec-body">
            <div className="rec-title">{r.title}</div>
            <div className="rec-why">{r.why}</div>
          </div>
          <div className="gain">+{r.projected_gain} pts</div>
        </div>
      ))}
    </div>
  );
}

/* ── Loading skeleton ────────────────────────────────────── */
export function LoadingSkeleton() {
  return (
    <div style={{ padding: "40px 0" }}>
      <div className="loading-skeleton skeleton-line w-40" style={{ height: 12, marginBottom: 10 }} />
      <div className="loading-skeleton skeleton-line w-60" style={{ height: 28, marginBottom: 28 }} />
      <div className="loading-skeleton" style={{ height: 180, borderRadius: 22, marginBottom: 22 }} />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <div className="loading-skeleton" style={{ height: 260, borderRadius: 16 }} />
        <div className="loading-skeleton" style={{ height: 260, borderRadius: 16 }} />
      </div>
    </div>
  );
}
