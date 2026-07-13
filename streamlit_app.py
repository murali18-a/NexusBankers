import streamlit as st
import sqlite3
import pandas as pd
import os
import sys

# Add project root to python path to import scoring engine
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.app.scoring import compute_score, simulate, WEIGHTS
from backend.app.recommender import recommend

# Resolve database path
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend", "finpulse.db"))

# Ensure database exists; if not, build it with 5000 customers
if not os.path.exists(DB_PATH):
    from backend.app.generate_data import build
    build(5000)

# Set page config
st.set_page_config(
    page_title="FinPulse — Explainable Financial Health Score",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Glow-up to match the React premium UI)
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    /* Global Overrides */
    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    .stApp {
        background-color: #F2F7F9;
    }

    /* Subtle Dot Pattern on main content */
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        background-image: radial-gradient(circle, rgba(2, 128, 144, 0.04) 1px, transparent 1px);
        background-size: 28px 28px;
    }

    /* Hide Streamlit default branding/headers */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B1D2E 0%, #0F2942 60%, #132F4C 100%) !important;
        border-right: 1px solid rgba(2,195,154,.08);
    }
    [data-testid="stSidebar"] * {
        color: #B0CFC9;
    }

    /* Brand Section in Sidebar */
    .brand {
        font-size: 28px;
        font-weight: 900;
        color: #fff;
        letter-spacing: -.6px;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 10px;
    }
    .brand span { color: #02C39A; }
    .brand-icon {
        width: 36px; height: 36px;
        background: linear-gradient(135deg, #02C39A 0%, #028090 100%);
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 18px;
        box-shadow: 0 4px 16px rgba(2,195,154,.3);
        color: white !important;
    }
    .brand-sub {
        font-size: 10px;
        color: #00A896;
        letter-spacing: 2.5px;
        margin: 6px 0 32px 0;
        text-transform: uppercase;
        font-weight: 600;
        padding-left: 46px;
    }

    /* ── Sidebar Navigation Pills ── */
    /* Hide "Navigation" label above radio group — every possible selector */
    div[data-testid="stRadio"] > label,
    div[data-testid="stRadio"] [data-testid="stWidgetLabel"],
    div[data-testid="stRadio"] > div > label:first-child,
    [data-testid="stSidebar"] div[data-testid="stRadio"] > label,
    [data-testid="stSidebar"] .stRadio > label {
        display: none !important;
        height: 0 !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    /* Radio container layout */
    div[data-testid="stRadio"] > div > div {
        display: flex !important;
        flex-direction: column !important;
        gap: 4px !important;
    }
    /* Each option row */
    div[data-testid="stRadio"] div[role="radiogroup"] > label,
    div[data-testid="stRadio"] label[data-baseweb="radio"] {
        padding: 11px 14px !important;
        border-radius: 10px !important;
        cursor: pointer !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #8AAFA9 !important;
        display: flex !important;
        align-items: center !important;
        transition: all 0.2s !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    div[data-testid="stRadio"] label:hover {
        background: rgba(255,255,255,0.06) !important;
        color: #E0F5F0 !important;
    }
    /* ── NUCLEAR: Hide ALL radio circle/dot indicators ── */
    div[data-testid="stRadio"] input[type="radio"],
    div[data-testid="stRadio"] label > div:first-child,
    div[data-testid="stRadio"] label > span:first-child,
    div[data-testid="stRadio"] [class*="radio"] circle,
    div[data-testid="stRadio"] svg,
    div[data-testid="stRadio"] div[data-baseweb="radio"] > div:first-child,
    div[data-testid="stRadio"] label > div[class*="indicator"],
    div[data-testid="stRadio"] label > div[aria-hidden] {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        min-width: 0 !important;
        min-height: 0 !important;
        overflow: hidden !important;
        position: absolute !important;
        opacity: 0 !important;
    }
    /* ── Active / checked state ── */
    div[data-testid="stRadio"] div[data-checked="true"] > label,
    div[data-testid="stRadio"] div[data-checked="true"] label {
        background: linear-gradient(135deg, #028090 0%, rgba(2,195,154,.75) 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border-color: rgba(2,195,154,.25) !important;
        box-shadow: 0 4px 18px rgba(2,128,144,.25) !important;
    }
    div[data-testid="stRadio"] div[data-checked="true"] label p,
    div[data-testid="stRadio"] div[data-checked="true"] label span {
        color: #ffffff !important;
    }
    /* Label paragraph (the text inside) */
    div[data-testid="stRadio"] label p {
        margin: 0 !important;
        font-size: 14px !important;
        font-weight: inherit !important;
        color: inherit !important;
    }


    /* ── Main View Typography ── */
    .page-kicker {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2.5px;
        color: #028090;
        text-transform: uppercase;
        margin-bottom: 2px;
    }
    .page-title {
        font-size: 32px;
        font-weight: 800;
        letter-spacing: -.6px;
        margin: 6px 0 28px 0;
        background: linear-gradient(135deg, #0B1D2E 0%, #028090 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* ── Cards — Premium Glassmorphism ── */
    .card {
        background: rgba(255, 255, 255, 0.72);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.6);
        border-radius: 16px;
        box-shadow: 0 2px 12px rgba(11,29,46,.06), 0 1px 3px rgba(11,29,46,.04);
        padding: 24px;
        margin-bottom: 20px;
        transition: box-shadow .25s ease, transform .25s ease;
    }
    .card:hover {
        box-shadow: 0 4px 20px rgba(11,29,46,.08), 0 1px 4px rgba(11,29,46,.04);
    }
    .section-h {
        font-size: 16px;
        font-weight: 800;
        margin-bottom: 16px;
        color: #0B1D2E;
        letter-spacing: -.2px;
    }

    /* ── Stats Row ── */
    .big-stat {
        font-size: 42px;
        font-weight: 900;
        letter-spacing: -1px;
        background: linear-gradient(135deg, #028090 0%, #02C39A 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-top: 4px;
    }
    .big-stat.danger {
        background: linear-gradient(135deg, #E07A5F 0%, #E08A3C 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .stat-label {
        font-size: 11px;
        color: #5A6B72;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
    }

    /* ── Hero Banner ── */
    .score-hero {
        background: linear-gradient(135deg, #0B1D2E 0%, #0F2942 40%, #028090 100%);
        color: #fff;
        border-radius: 22px;
        padding: 34px 38px;
        display: flex;
        align-items: center;
        gap: 36px;
        box-shadow: 0 12px 48px rgba(11,29,46,.12), 0 0 40px rgba(2,195,154,.15);
        position: relative;
        overflow: hidden;
        margin-bottom: 24px;
    }
    .score-hero::before {
        content: "";
        position: absolute;
        width: 200px; height: 200px;
        border-radius: 50%;
        background: rgba(2,195,154,.12);
        top: -60px; right: -40px;
        filter: blur(40px);
    }
    .gauge-wrapper {
        flex-shrink: 0;
        position: relative;
    }
    .gauge-text {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .gauge-num {
        font-size: 46px;
        font-weight: 900;
        line-height: 1;
        letter-spacing: -2px;
        color: #fff;
    }
    .gauge-of {
        font-size: 11px;
        color: rgba(255,255,255,.45);
        font-weight: 500;
        margin-top: 2px;
    }

    .band-pill {
        display: inline-flex;
        align-items: center;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 13px;
        margin-top: 10px;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,.15);
        color: white;
    }
    
    .metric-pills {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 14px;
    }
    .metric-pill {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 14px;
        border-radius: 10px;
        background: rgba(255,255,255,.15);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,.1);
        font-size: 12px;
        color: rgba(255,255,255,.85);
    }
    .metric-pill strong {
        color: #fff;
        font-weight: 700;
        font-size: 13px;
    }

    /* ── Factor List Breakdown ── */
    .factor-row {
        display: grid;
        grid-template-columns: 110px 1fr 50px;
        gap: 10px 14px;
        align-items: center;
        padding: 14px 0;
        border-bottom: 1px solid rgba(11,29,46,.08);
    }
    .factor-row:last-child {
        border-bottom: none;
    }
    .factor-name {
        font-weight: 600;
        font-size: 13px;
        color: #0B1D2E;
    }
    .bar-track {
        height: 10px;
        background: #E6F4F1;
        border-radius: 6px;
        overflow: hidden;
        position: relative;
    }
    .bar-fill {
        height: 100%;
        border-radius: 6px;
        position: relative;
    }
    .bar-fill::after {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,.3) 50%, transparent 100%);
        border-radius: 6px;
    }
    .factor-val {
        font-weight: 800;
        text-align: right;
        font-size: 14px;
        color: #0B1D2E;
    }
    .factor-reason {
        grid-column: 1 / -1;
        font-size: 12px;
        color: #5A6B72;
        margin-top: -2px;
        line-height: 1.5;
    }

    /* ── Recommendations ── */
    .rec {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 18px 20px;
        border: 1px solid rgba(11,29,46,.08);
        border-radius: 14px;
        margin-bottom: 12px;
        background: rgba(255, 255, 255, 0.72);
        backdrop-filter: blur(8px);
        transition: all .25s ease;
    }
    .rec:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 20px rgba(11,29,46,.08);
        border-color: rgba(2,195,154,.2);
    }
    .rec-num {
        width: 36px; height: 36px;
        border-radius: 50%;
        color: #fff;
        font-weight: 800;
        font-size: 14px;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
        box-shadow: 0 3px 10px rgba(2,128,144,.25);
    }
    .rec-body { flex: 1; }
    .rec-title { font-weight: 700; font-size: 14px; color: #0B1D2E; }
    .rec-why { font-size: 12px; color: #5A6B72; margin-top: 3px; line-height: 1.4; }
    .gain {
        padding: 7px 14px;
        border-radius: 20px;
        background: linear-gradient(135deg, #02C39A 0%, #00A896 100%);
        color: #fff;
        font-weight: 800;
        font-size: 13px;
        white-space: nowrap;
        box-shadow: 0 3px 12px rgba(2,195,154,.25);
    }

    /* ── Delta Badges ── */
    .delta-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 15px;
    }
    .delta-badge.positive {
        background: rgba(2,195,154,.15);
        color: #02C39A;
    }
    .delta-badge.negative {
        background: rgba(224,122,95,.12);
        color: #E07A5F;
    }
    .delta-badge.neutral {
        background: #E6F4F1;
        color: #5A6B72;
    }

    /* ── Table Styling ── */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
    .custom-table th {
        text-align: left;
        font-size: 10px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #5A6B72;
        padding: 12px 16px;
        border-bottom: 2px solid rgba(11,29,46,.08);
        font-weight: 700;
    }
    .custom-table td {
        padding: 14px 16px;
        border-bottom: 1px solid rgba(11,29,46,.08);
        font-size: 14px;
        color: #0B1D2E;
    }
    .custom-table tr {
        transition: all 0.18s ease;
    }
    .custom-table tr:hover {
        background: linear-gradient(90deg, rgba(2,195,154,.06) 0%, rgba(2,128,144,.03) 100%);
    }
    
    .chip {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: .3px;
        display: inline-flex;
        align-items: center;
    }

    /* Custom range slider thumb adjustments for Streamlit */
    div[data-testid="stSlider"] [data-handle] {
        background: linear-gradient(135deg, #02C39A 0%, #028090 100%) !important;
        border: 3px solid #fff !important;
        box-shadow: 0 2px 8px rgba(2,128,144,.3) !important;
    }
</style>
""", unsafe_allow_html=True)

def render_html(html_str):
    # Remove leading spaces on every line to prevent markdown indent code-block parsing
    cleaned = "\n".join(line.strip() for line in html_str.split("\n"))
    st.markdown(cleaned, unsafe_allow_html=True)

# Helper function to assign band colors
def get_band_color(b):
    colors = {
        "Excellent":  "#02C39A",
        "Good":       "#00A896",
        "Fair":       "#E9B44C",
        "Needs work": "#E08A3C",
        "At risk":    "#E07A5F",
    }
    return colors.get(b, "#5A6B72")

def get_factor_gradients(key):
    grads = {
        "savings_ratio":     ["#028090", "#02C39A"],
        "spending_control":  ["#00A896", "#02C39A"],
        "debt_load":         ["#0B7A8C", "#028090"],
        "payment_stability": ["#028090", "#00A896"],
        "liquidity_buffer":  ["#3AAFA9", "#02C39A"],
    }
    return grads.get(key, ["#028090", "#02C39A"])

# Database connection functions
def get_db_connection():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def get_stats():
    con = get_db_connection()
    total = con.execute("SELECT COUNT(*) c FROM customers").fetchone()["c"]
    avg = con.execute("SELECT AVG(score) a FROM customers").fetchone()["a"]
    bands = con.execute("SELECT band, COUNT(*) c FROM customers GROUP BY band").fetchall()
    hist = con.execute("""
        SELECT (score/10)*10 AS bucket, COUNT(*) c
        FROM customers GROUP BY bucket ORDER BY bucket
    """).fetchall()
    con.close()
    
    band_dict = {r["band"]: r["c"] for r in bands}
    hist_data = [{"bucket": int(r["bucket"]), "count": int(r["c"])} for r in hist]
    return {
        "total_customers": total,
        "avg_score": round(avg, 1) if avg else 0,
        "bands": band_dict,
        "histogram": hist_data
    }

def get_customers(limit=25, band=None):
    con = get_db_connection()
    q = "SELECT id, name, cohort, monthly_income, score, band FROM customers"
    params = []
    if band:
        q += " WHERE band = ?"
        params.append(band)
    q += " ORDER BY id LIMIT ?"
    params.append(limit)
    rows = con.execute(q, params).fetchall()
    con.close()
    return [dict(r) for r in rows]

def get_customer_details(cid):
    con = get_db_connection()
    row = con.execute("SELECT * FROM customers WHERE id = ?", (cid,)).fetchone()
    con.close()
    if not row:
        return None
    
    metrics = {
        "savings_rate": row["savings_rate"],
        "spend_volatility": row["spend_volatility"],
        "debt_to_income": row["debt_to_income"],
        "income_regularity": row["income_regularity"],
        "on_time_rate": row["on_time_rate"],
        "emergency_months": row["emergency_months"]
    }
    return {
        "id": row["id"],
        "name": row["name"],
        "cohort": row["cohort"],
        "monthly_income": row["monthly_income"],
        "metrics": metrics,
        "score": row["score"],
        "band": row["band"]
    }

# ── Render Custom SVG Gauge ──
def render_svg_gauge(score, band):
    size = 150
    r = size / 2 - 12
    c = 2 * 3.14159 * r
    pct = max(0, min(100, score)) / 100
    col = get_band_color(band)
    offset = c * (1 - pct)
    
    return f"""
    <div class="gauge-wrapper" style="width: {size}px; height: {size}px;">
        <svg width="{size}" height="{size}" style="transform: rotate(-90deg);">
            <circle cx="{size / 2}" cy="{size / 2}" r="{r}" fill="none"
              stroke="rgba(255,255,255,.12)" stroke-width="12" />
            <circle cx="{size / 2}" cy="{size / 2}" r="{r}" fill="none"
              stroke="{col}" stroke-width="12" stroke-linecap="round"
              stroke-dasharray="{c}" stroke-dashoffset="{offset}"
              style="transition: stroke-dashoffset .8s ease; filter: drop-shadow(0 0 6px {col}44);" />
        </svg>
        <div class="gauge-text">
            <div class="gauge-num">{score}</div>
            <div class="gauge-of">/ 100</div>
        </div>
    </div>
    """

# ── Render Factor Breakdown ──
def render_factor_list(factors):
    html = '<div style="display: flex; flex-direction: column;">'
    for f in factors:
        c1, c2 = get_factor_gradients(f.key)
        html += f"""
        <div class="factor-row">
            <div class="factor-name">{f.label}</div>
            <div class="bar-track">
                <div class="bar-fill" style="width: {f.sub_score}%; background: linear-gradient(90deg, {c1}, {c2});"></div>
            </div>
            <div class="factor-val">{int(f.sub_score)}</div>
            <div class="factor-reason">{f.reason}</div>
        </div>
        """
    html += '</div>'
    return html

# ── Render Recommendations ──
def render_recs(recs):
    if not recs:
        return "<p class='muted'>✅ No actions needed — this profile is already healthy.</p>"
    
    gradients = [
        "linear-gradient(135deg, #028090, #02C39A)",
        "linear-gradient(135deg, #00A896, #3AAFA9)",
        "linear-gradient(135deg, #0B7A8C, #028090)",
        "linear-gradient(135deg, #02C39A, #00A896)",
    ]
    
    html = ""
    for idx, r in enumerate(recs):
        grad = gradients[idx % len(gradients)]
        html += f"""
        <div class="rec">
            <div class="rec-num" style="background: {grad};">{idx + 1}</div>
            <div class="rec-body">
                <div class="rec-title">{r["title"]}</div>
                <div class="rec-why">{r["why"]}</div>
            </div>
            <div class="gain">+{r["projected_gain"]} pts</div>
        </div>
        """
    return html

# ── Navigation in Sidebar ──
with st.sidebar:
    render_html("""
    <div class="brand">
        <div class="brand-icon">💳</div>
        Fin<span>Pulse</span>
    </div>
    <div class="brand-sub">IDBI Innovate 2026</div>
    """)
    
    # Render Navigation (uses custom styled radio labels)
    view = st.radio(
        "Navigation",
        ["📊 Portfolio Health", "🎯 Customer Score Card", "⚡ What-if Simulator"],
        label_visibility="collapsed"
    )

    st.markdown("<br><hr>", unsafe_allow_html=True)
    render_html(
        "<div style='font-size: 11px; color: rgba(160,200,190,.4); line-height: 1.7;'>"
        "Explainable Financial Health Score.<br>"
        "Team NexusBankers.<br>"
        "Runs on the bank's own data — no black box."
        "</div>"
    )

# ════════════════ PORTFOLIO VIEW ════════════════
if view == "📊 Portfolio Health":
    st.markdown('<div class="page-kicker">Relationship manager view</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Portfolio Health</div>', unsafe_allow_html=True)

    stats = get_stats()
    
    # Premium Stat cards
    col1, col2, col3 = st.columns(3)
    with col1:
        render_html(f"""
        <div class="card">
            <div class="stat-label">Customers Scored</div>
            <div class="big-stat">{stats["total_customers"]:,}</div>
        </div>
        """)
    with col2:
        render_html(f"""
        <div class="card">
            <div class="stat-label">Average Score</div>
            <div class="big-stat">{stats["avg_score"]}</div>
        </div>
        """)
    with col3:
        at_risk = stats["bands"].get("At risk", 0)
        render_html(f"""
        <div class="card">
            <div class="stat-label">At-Risk Customers</div>
            <div class="big-stat danger">{at_risk}</div>
        </div>
        """)

    # Score Distribution Chart
    render_html('<div class="section-h" style="margin-top: 12px;">📊 Score Distribution</div>')
    hist_df = pd.DataFrame(stats["histogram"])
    hist_df.rename(columns={"bucket": "Score Range", "count": "Count"}, inplace=True)
    st.bar_chart(hist_df, x="Score Range", y="Count", color="#028090")

    # Customer Table
    render_html('<div class="section-h" style="margin-top: 20px;">👤 Customers</div>')
    
    # Band selection pills
    band_options = ["All bands", "Excellent", "Good", "Fair", "Needs work", "At risk"]
    selected_band = st.selectbox("Filter by band", band_options, label_visibility="collapsed")
    
    query_band = selected_band if selected_band != "All bands" else None
    customers = get_customers(band=query_band)
    
    if customers:
        table_html = """
        <table class="custom-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Segment</th>
                    <th>Income</th>
                    <th>Score</th>
                    <th>Band</th>
                </tr>
            </thead>
            <tbody>
        """
        for r in customers:
            col = get_band_color(r["band"])
            table_html += f"""
                <tr>
                    <td style="font-family: monospace; color: #5A6B72;">#{r["id"]}</td>
                    <td style="font-weight: 600;">{r["name"]}</td>
                    <td style="color: #5A6B72;">{r["cohort"].replace('_', ' ').title()}</td>
                    <td style="font-family: monospace;">₹{r["monthly_income"]:,}</td>
                    <td style="font-family: monospace; font-weight: 800;">{r["score"]}</td>
                    <td>
                        <span class="chip" style="background: {col}18; color: {col};">
                            {r["band"]}
                        </span>
                    </td>
                </tr>
            """
        table_html += "</tbody></table>"
        render_html(table_html)
    else:
        st.info("No customers found in this category.")

# ════════════════ SCORE CARD VIEW ════════════════
elif view == "🎯 Customer Score Card":
    st.markdown('<div class="page-kicker">Customer score card</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Customer Health Details</div>', unsafe_allow_html=True)

    # Selectbox / input search
    customer_id = st.number_input("Enter Customer ID", min_value=1, max_value=5000, value=12, step=1)
    data = get_customer_details(customer_id)

    if data:
        result = compute_score(data["metrics"])
        recs = recommend(data["metrics"], top_n=4)
        
        # Hero Banner with SVG Gauge, Metric Pills
        gauge_html = render_svg_gauge(result.score, result.band)
        band_col = get_band_color(result.band)
        
        render_html(f"""
        <div class="score-hero">
            {gauge_html}
            <div style="position: relative; z-index: 2;">
                <div class="band-pill" style="background: {band_col};">
                    {result.band}
                </div>
                <div style="font-size: 15px; color: rgba(207,231,228,.85); margin-top: 14px; max-width: 460px; line-height: 1.6;">
                    Financial health for <strong style="color: #fff;">{data["name"]}</strong>,
                    a {data["cohort"].replace('_', ' ')} earning ₹{data["monthly_income"]:,}/month.
                    Every point below is traceable to a factor — no black box.
                </div>
                <div class="metric-pills">
                    <div class="metric-pill">
                        💰 Savings <strong>{data["metrics"]["savings_rate"]*100:.0f}%</strong>
                    </div>
                    <div class="metric-pill">
                        📊 DTI <strong>{data["metrics"]["debt_to_income"]*100:.0f}%</strong>
                    </div>
                    <div class="metric-pill">
                        🛡️ Buffer <strong>{data["metrics"]["emergency_months"]:.1f} mo</strong>
                    </div>
                    <div class="metric-pill">
                        ✅ On-time <strong>{data["metrics"]["on_time_rate"]*100:.0f}%</strong>
                    </div>
                </div>
            </div>
        </div>
        """)

        col1, col2 = st.columns(2)
        with col1:
            render_html(f"""
            <div class="card" style="min-height: 420px;">
                <div class="section-h">📋 Why this score</div>
                {render_factor_list(result.factors)}
            </div>
            """)

        with col2:
            render_html(f"""
            <div class="card" style="min-height: 420px;">
                <div class="section-h">🚀 Recommended actions</div>
                {render_recs(recs)}
            </div>
            """)
    else:
        st.error("Customer not found. Please enter a valid ID (1 to 5000).")

# ════════════════ SIMULATOR VIEW ════════════════
else:
    st.markdown('<div class="page-kicker">What-if simulator</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Model a Change, Watch the Score Move</div>', unsafe_allow_html=True)

    START = {
        "savings_rate": 0.08, "spend_volatility": 0.35, "debt_to_income": 0.4,
        "income_regularity": 0.8, "on_time_rate": 0.85, "emergency_months": 1.5,
    }

    # Base score
    base_res = compute_score(START)

    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        render_html('<div class="section-h">🎛️ Adjust the inputs</div>')
        
        sim_metrics = {}
        sim_metrics["savings_rate"] = st.slider("💰 Savings rate", 0.0, 0.45, START["savings_rate"], 0.01)
        sim_metrics["spend_volatility"] = st.slider("Spend volatility", 0.05, 0.8, START["spend_volatility"], 0.01)
        sim_metrics["debt_to_income"] = st.slider("🏦 Debt-to-income (EMIs)", 0.0, 0.65, START["debt_to_income"], 0.01)
        sim_metrics["income_regularity"] = st.slider("📅 Income regularity", 0.3, 1.0, START["income_regularity"], 0.01)
        sim_metrics["on_time_rate"] = st.slider("✅ On-time payments", 0.5, 1.0, START["on_time_rate"], 0.01)
        sim_metrics["emergency_months"] = st.slider("🛡️ Emergency fund (months)", 0.0, 9.0, START["emergency_months"], 0.5)
        
        # Reset / Preset buttons
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Reset to default profile"):
                st.rerun()
        with btn_col2:
            if st.button("⭐ Load Ideal profile"):
                st.session_state["savings_rate"] = 0.28
                st.session_state["spend_volatility"] = 0.12
                st.session_state["debt_to_income"] = 0.10
                st.session_state["income_regularity"] = 0.95
                st.session_state["on_time_rate"] = 0.99
                st.session_state["emergency_months"] = 6.5
                st.rerun()

    with col2:
        # Calculate new score
        new_res = compute_score(sim_metrics)
        delta = new_res.score - base_res.score
        
        # Render custom SVG gauge hero
        gauge_html = render_svg_gauge(new_res.score, new_res.band)
        band_col = get_band_color(new_res.band)
        
        delta_badge_html = ""
        if delta == 0:
            delta_badge_html = "<span class='delta-badge neutral'>Same as starting profile</span>"
        elif delta > 0:
            delta_badge_html = f"<span class='delta-badge positive'>▲ +{delta} points</span>"
        else:
            delta_badge_html = f"<span class='delta-badge negative'>▼ {delta} points</span>"

        render_html(f"""
        <div class="score-hero">
            {gauge_html}
            <div style="position: relative; z-index: 2;">
                <div class="band-pill" style="background: {band_col};">
                    {new_res.band}
                </div>
                <div style="margin-top: 15px;">
                    {delta_badge_html}
                </div>
            </div>
        </div>
        """)
        
        # Live Factor breakdown
        render_html(f"""
        <div class="card">
            <div class="section-h">📋 Live factor breakdown</div>
            {render_factor_list(new_res.factors)}
        </div>
        """)
