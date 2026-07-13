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
    st.info("Database not found. Generating synthetic data of 5,000 customers...")
    from backend.app.generate_data import build
    build(5000)

# Set page config
st.set_page_config(
    page_title="FinPulse — Explainable Financial Health Score",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Theme match)
st.markdown("""
<style>
    /* Main Layout */
    .stApp {
        background-color: #F2F7F9;
    }
    
    /* Branding */
    .brand-title {
        font-size: 34px;
        font-weight: 900;
        color: #0B1D2E;
        letter-spacing: -0.6px;
        margin-bottom: 2px;
    }
    .brand-title span {
        color: #02C39A;
    }
    .brand-sub {
        font-size: 11px;
        color: #00A896;
        letter-spacing: 2px;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 25px;
    }

    /* Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.72);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(11, 29, 46, 0.08);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(11, 29, 46, 0.04);
        margin-bottom: 15px;
    }
    .metric-label {
        font-size: 11px;
        color: #5A6B72;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 38px;
        font-weight: 900;
        color: #028090;
        line-height: 1;
    }
    .metric-value.danger {
        color: #E07A5F;
    }

    /* Hero Banner */
    .hero-card {
        background: linear-gradient(135deg, #0B1D2E 0%, #0F2942 50%, #028090 100%);
        border-radius: 20px;
        padding: 30px;
        color: #ffffff;
        margin-bottom: 25px;
        box-shadow: 0 12px 48px rgba(11, 29, 46, 0.12);
        display: flex;
        align-items: center;
        gap: 30px;
    }
    .hero-gauge {
        flex-shrink: 0;
        width: 120px;
        height: 120px;
        border-radius: 50%;
        border: 10px solid rgba(255, 255, 255, 0.15);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 36px;
        font-weight: 900;
        position: relative;
    }
    .hero-gauge.Excellent { border-color: #02C39A; color: #02C39A; }
    .hero-gauge.Good { border-color: #00A896; color: #00A896; }
    .hero-gauge.Fair { border-color: #E9B44C; color: #E9B44C; }
    .hero-gauge.Needs-work { border-color: #E08A3C; color: #E08A3C; }
    .hero-gauge.At-risk { border-color: #E07A5F; color: #E07A5F; }

    /* Custom Factor List Row */
    .factor-container {
        padding: 12px 0;
        border-bottom: 1px solid rgba(11, 29, 46, 0.08);
    }
    .factor-container:last-child {
        border-bottom: none;
    }
    .factor-header {
        display: flex;
        justify-content: space-between;
        font-weight: 600;
        font-size: 13px;
        color: #0B1D2E;
        margin-bottom: 4px;
    }
    .factor-val {
        font-weight: 800;
    }
    .factor-reason {
        font-size: 12px;
        color: #5A6B72;
        margin-top: 4px;
    }
    
    /* Recommendations */
    .rec-item {
        background: #ffffff;
        border-radius: 12px;
        border: 1px solid rgba(11, 29, 46, 0.08);
        padding: 15px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: transform 0.2s;
    }
    .rec-body {
        flex: 1;
        padding-right: 15px;
    }
    .rec-title {
        font-weight: 700;
        font-size: 14px;
        color: #0B1D2E;
    }
    .rec-why {
        font-size: 12px;
        color: #5A6B72;
        margin-top: 3px;
    }
    .rec-gain {
        padding: 6px 12px;
        background: linear-gradient(135deg, #02C39A 0%, #00A896 100%);
        color: white;
        border-radius: 20px;
        font-weight: 800;
        font-size: 12px;
        white-space: nowrap;
    }

    /* Badges */
    .delta-badge-pos {
        background: rgba(2, 195, 154, 0.15);
        color: #02C39A;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 14px;
    }
    .delta-badge-neg {
        background: rgba(224, 122, 95, 0.15);
        color: #E07A5F;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# Database helper functions
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

# Navigation in Sidebar
with st.sidebar:
    st.markdown('<div class="brand-title">Fin<span>Pulse</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">IDBI Innovate 2026</div>', unsafe_allow_html=True)
    
    view = st.radio(
        "Navigation",
        ["📊 Portfolio Health", "🎯 Customer Score Card", "⚡ What-if Simulator"],
        label_visibility="collapsed"
    )

    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size: 11px; color: #8FA3AB; line-height: 1.5;'>"
        "Explainable Financial Health Score.<br>"
        "Team NexusBankers.<br>"
        "Runs on the bank's own data — no black box."
        "</div>",
        unsafe_allow_html=True
    )

# ════════════════ PORTFOLIO VIEW ════════════════
if view == "📊 Portfolio Health":
    st.subheader("Portfolio Health")
    st.caption("Relationship manager view")

    stats = get_stats()
    
    # Stat cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Customers Scored</div>
            <div class="metric-value">{stats["total_customers"]:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Average Score</div>
            <div class="metric-value">{stats["avg_score"]}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        at_risk = stats["bands"].get("At risk", 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">At-risk Customers</div>
            <div class="metric-value danger">{at_risk}</div>
        </div>
        """, unsafe_allow_html=True)

    # Score Distribution Chart
    st.markdown("### 📊 Score Distribution")
    hist_df = pd.DataFrame(stats["histogram"])
    hist_df.rename(columns={"bucket": "Score Range", "count": "Count"}, inplace=True)
    st.bar_chart(hist_df, x="Score Range", y="Count", color="#028090")

    # Customer Table
    st.markdown("### 👤 Customers")
    band_options = ["All bands", "Excellent", "Good", "Fair", "Needs work", "At risk"]
    selected_band = st.selectbox("Filter by Band", band_options)
    
    query_band = selected_band if selected_band != "All bands" else None
    customers = get_customers(band=query_band)
    
    if customers:
        df = pd.DataFrame(customers)
        df["cohort"] = df["cohort"].str.replace("_", " ").str.title()
        df["monthly_income"] = df["monthly_income"].apply(lambda x: f"₹{x:,}")
        df.rename(columns={
            "id": "ID",
            "name": "Name",
            "cohort": "Segment",
            "monthly_income": "Monthly Income",
            "score": "Score",
            "band": "Band"
        }, inplace=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No customers found in this category.")

# ════════════════ SCORE CARD VIEW ════════════════
elif view == "🎯 Customer Score Card":
    st.subheader("Customer Score Card")
    st.caption("Detailed view of explainable customer profiles")

    # Search for customer
    customer_id = st.number_input("Enter Customer ID", min_value=1, max_value=5000, value=12, step=1)
    data = get_customer_details(customer_id)

    if data:
        result = compute_score(data["metrics"])
        recs = recommend(data["metrics"], top_n=4)
        
        # Hero Banner
        band_class = data["band"].replace(" ", "-")
        st.markdown(f"""
        <div class="hero-card">
            <div class="hero-gauge {band_class}">{result.score}</div>
            <div>
                <h2 style="margin:0 0 5px 0; color:white; font-size:26px;">{data["name"]}</h2>
                <div style="font-size: 14px; color: rgba(255,255,255,0.85); max-width: 500px; line-height: 1.5;">
                    Financial health for <strong>{data["name"]}</strong>, a {data["cohort"].replace("_", " ")} earning 
                    ₹{data["monthly_income"]:,}/month. Every point is traceable to a factor — no black box.
                </div>
                <div style="display:flex; gap:10px; margin-top:14px; flex-wrap:wrap;">
                    <span style="background:rgba(255,255,255,0.15); padding:4px 10px; border-radius:6px; font-size:12px;">💰 Savings: <strong>{data["metrics"]["savings_rate"]*100:.0f}%</strong></span>
                    <span style="background:rgba(255,255,255,0.15); padding:4px 10px; border-radius:6px; font-size:12px;">📊 DTI: <strong>{data["metrics"]["debt_to_income"]*100:.0f}%</strong></span>
                    <span style="background:rgba(255,255,255,0.15); padding:4px 10px; border-radius:6px; font-size:12px;">🛡️ Buffer: <strong>{data["metrics"]["emergency_months"]:.1f} mo</strong></span>
                    <span style="background:rgba(255,255,255,0.15); padding:4px 10px; border-radius:6px; font-size:12px;">✅ On-time: <strong>{data["metrics"]["on_time_rate"]*100:.0f}%</strong></span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="metric-card" style="min-height:380px;">'
                        '<h4>📋 Why this score</h4><br>', unsafe_allow_html=True)
            for f in result.factors:
                st.markdown(f"""
                <div class="factor-container">
                    <div class="factor-header">
                        <span>{f.label}</span>
                        <span class="factor-val">{int(f.sub_score)}/100</span>
                    </div>
                    <div class="factor-reason">{f.reason}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="metric-card" style="min-height:380px;">'
                        '<h4>🚀 Recommended actions</h4><br>', unsafe_allow_html=True)
            if recs:
                for idx, r in enumerate(recs):
                    st.markdown(f"""
                    <div class="rec-item">
                        <div class="rec-body">
                            <div class="rec-title">{idx+1}. {r["title"]}</div>
                            <div class="rec-why">{r["why"]}</div>
                        </div>
                        <div class="rec-gain">+{r["projected_gain"]} pts</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:#5A6B72;'>✅ No actions needed — this profile is already healthy.</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.error("Customer not found. Please enter a valid ID (1 to 5000).")

# ════════════════ SIMULATOR VIEW ════════════════
else:
    st.subheader("What-if Simulator")
    st.caption("Model financial behavior updates and watch the score move")

    START = {
        "savings_rate": 0.08, "spend_volatility": 0.35, "debt_to_income": 0.4,
        "income_regularity": 0.8, "on_time_rate": 0.85, "emergency_months": 1.5,
    }

    # Base score
    base_res = compute_score(START)

    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.markdown('<div class="metric-card"><h4>🎛️ Adjust metrics</h4>', unsafe_allow_html=True)
        
        sim_metrics = {}
        sim_metrics["savings_rate"] = st.slider("💰 Savings rate", 0.0, 0.45, START["savings_rate"], 0.01, format="%.2f")
        sim_metrics["spend_volatility"] = st.slider("📉 Spending volatility", 0.05, 0.8, START["spend_volatility"], 0.01)
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
            # Setup ideal profile variables
            if st.button("⭐ Load Ideal profile"):
                st.session_state["savings_rate"] = 0.28
                st.session_state["spend_volatility"] = 0.12
                st.session_state["debt_to_income"] = 0.10
                st.session_state["income_regularity"] = 0.95
                st.session_state["on_time_rate"] = 0.99
                st.session_state["emergency_months"] = 6.5
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        # Calculate new score
        new_res = compute_score(sim_metrics)
        delta = new_res.score - base_res.score
        
        band_class = new_res.band.replace(" ", "-")
        
        # Render gauge hero
        st.markdown(f"""
        <div class="hero-card">
            <div class="hero-gauge {band_class}">{new_res.score}</div>
            <div>
                <h3 style="margin:0; color:white;">Projected Score</h3>
                <span class="band-pill" style="color:white; background:rgba(255,255,255,0.15); padding:2px 8px; border-radius:4px; font-size:12px;">{new_res.band}</span>
                <div style="margin-top:15px;">
                    {"<span class='delta-badge-pos'>▲ +" + str(delta) + " points</span>" if delta > 0 else 
                     "<span class='delta-badge-neg'>▼ " + str(delta) + " points</span>" if delta < 0 else 
                     "<span style='color:lightgray; font-size:14px;'>Same as starting profile</span>"}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Factor breakdown
        st.markdown('<div class="metric-card">'
                    '<h4>📋 Live factor breakdown</h4><br>', unsafe_allow_html=True)
        for f in new_res.factors:
            st.markdown(f"""
            <div class="factor-container">
                <div class="factor-header">
                    <span>{f.label}</span>
                    <span class="factor-val">{int(f.sub_score)}/100</span>
                </div>
                <div class="factor-reason">{f.reason}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
