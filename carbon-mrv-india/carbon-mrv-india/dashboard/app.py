"""
dashboard/app.py
----------------
CarbonMRV India — Interactive Streamlit Dashboard

Run with: streamlit run dashboard/app.py

Features:
- Region selector with India map context
- NDVI time series visualization
- Carbon stock estimation
- Credit valuation across markets
- Startup revenue projections
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from satellite_data import (
    INDIA_FOREST_REGIONS,
    generate_mock_ndvi_timeseries,
    generate_spatial_ndvi_grid,
    get_all_regions_summary
)
from carbon_calculator import (
    calculate_carbon_stock,
    calculate_annual_sequestration,
    FOREST_TYPE_FACTORS
)
from credit_estimator import (
    estimate_credit_value,
    calculate_platform_revenue_projection,
    MARKET_PRICES
)

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="CarbonMRV India",
    page_icon="logo2.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .stMetric label { color: #166534 !important; }
    .hero-text { color: #14532d; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.shields.io/badge/CarbonMRV-India-green?style=for-the-badge", use_column_width=True)
    st.markdown("### CarbonMRV India")
    st.markdown("*AI-Powered Carbon Verification Platform*")
    st.divider()
    
    st.markdown("**Select Forest Region**")
    region_display = {
        k: f"{v['state']} — {v['forest_type']}"
        for k, v in INDIA_FOREST_REGIONS.items()
    }
    selected_region_key = st.selectbox(
        "Region",
        options=list(region_display.keys()),
        format_func=lambda x: region_display[x],
        label_visibility="collapsed"
    )
    
    st.divider()
    region_info = INDIA_FOREST_REGIONS[selected_region_key]
    st.markdown(f"**Area:** {region_info['area_hectares']:,} ha")
    st.markdown(f"**Forest Type:** {region_info['forest_type']}")
    st.markdown(f"**State:** {region_info['state']}")
    st.markdown(f"*{region_info['description']}*")
    
    st.divider()
    st.markdown("**Data Source**")
    data_source = st.radio(
        "Source",
        ["🔬 Simulation (Mock)", "🛰️ Sentinel-2 (GEE — requires auth)"],
        label_visibility="collapsed"
    )
    
    st.divider()
    st.markdown("**Market Settings**")
    market_type = st.selectbox(
        "Target Market",
        ["India VCM", "CCTS Compliance", "International VCM"]
    )
    
    st.divider()
    st.caption("v0.1.0 | MIT License | [GitHub](#)")

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────

@st.cache_data
def load_region_data(region_key):
    ndvi_data = generate_mock_ndvi_timeseries(region_key, years=3)
    region = INDIA_FOREST_REGIONS[region_key]
    
    estimate = calculate_carbon_stock(
        ndvi=ndvi_data["mean_ndvi"],
        area_hectares=region["area_hectares"],
        forest_type=region["forest_type"],
        region_name=region_key.replace("_", " ").title()
    )
    
    sequestration = calculate_annual_sequestration(
        ndvi_data["ndvi_values"],
        region["area_hectares"],
        region["forest_type"]
    )
    
    valuation = estimate_credit_value(
        verified_credits=estimate.baseline_credits,
        region_name=region_key,
        total_co2e=estimate.total_co2e
    )
    
    spatial_grid = generate_spatial_ndvi_grid(region_key, grid_size=30)
    
    return ndvi_data, estimate, sequestration, valuation, spatial_grid

ndvi_data, estimate, sequestration, valuation, spatial_grid = load_region_data(selected_region_key)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

# st.markdown("#  CarbonMRV India")
import base64

with open("logo2.png", "rb") as img_file:
    logo_base64 = base64.b64encode(img_file.read()).decode()

st.markdown(
    f"""
    <div style="display:flex; align-items:center;">
        <img src="data:image/png;base64,{logo_base64}" width="45">
        <h1 style="margin:0 0 0 10px; font-size:48px;">
            CarbonMRV India
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("**AI-Powered Carbon Credit Measurement, Reporting & Verification Platform**")
st.caption(f"Analyzing: **{region_info['state']}** | {region_info['forest_type']} | {region_info['area_hectares']:,} hectares")

# ─────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────

st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Mean NDVI", f"{estimate.mean_ndvi:.3f}", f"{estimate.confidence_level} Confidence")
with col2:
    st.metric("Carbon Stock", f"{estimate.carbon_stock_per_ha:,.0f} tC/ha", "per hectare")
with col3:
    st.metric("Total CO2e", f"{estimate.total_co2e/1000:,.1f}K tCO2e", f"{region_info['area_hectares']:,} ha")
with col4:
    st.metric("Verified Credits", f"{estimate.baseline_credits/1000:,.1f}K", "tCO2e (80% buffer)")
with col5:
    best_val_cr = valuation.best_market_value_inr / 1e7
    st.metric("Credit Value", f"₹{best_val_cr:.1f} Cr", valuation.best_market)

st.markdown("---")

# ─────────────────────────────────────────────
# TAB LAYOUT
# ─────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "🛰️ NDVI Analysis",
    "🌱 Carbon Estimation",
    "💰 Credit Valuation",
    "📈 Platform Revenue"
])

# ── TAB 1: NDVI Analysis ──────────────────────

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("NDVI Time Series — 3 Year Trend")
        
        df_ndvi = pd.DataFrame({
            "Date": pd.to_datetime(ndvi_data["dates"]),
            "NDVI": ndvi_data["ndvi_values"]
        })
        
        fig_ndvi = go.Figure()
        fig_ndvi.add_trace(go.Scatter(
            x=df_ndvi["Date"],
            y=df_ndvi["NDVI"],
            mode="lines",
            name="NDVI",
            line=dict(color="#16a34a", width=2),
            fill="tozeroy",
            fillcolor="rgba(22, 163, 74, 0.1)"
        ))
        
        # Monsoon annotation bands
        for year in [2022, 2023, 2024]:
            fig_ndvi.add_vrect(
                x0=f"{year}-06-01", x1=f"{year}-09-30",
                fillcolor="rgba(59, 130, 246, 0.08)",
                line_width=0,
                annotation_text="Monsoon" if year == 2022 else "",
                annotation_position="top left"
            )
        
        fig_ndvi.add_hline(y=0.6, line_dash="dot", line_color="green",
                           annotation_text="Dense Forest Threshold (0.6)")
        fig_ndvi.add_hline(y=0.4, line_dash="dot", line_color="orange",
                           annotation_text="Moderate Vegetation (0.4)")
        
        fig_ndvi.update_layout(
            height=350,
            yaxis_title="NDVI Value",
            yaxis=dict(range=[0, 1]),
            hovermode="x unified",
            plot_bgcolor="black",
            paper_bgcolor="black",
            legend=dict(orientation="h")
        )
        
        st.plotly_chart(fig_ndvi, use_container_width=True)
    
    with col2:
        st.subheader("Spatial NDVI Heatmap")
        st.caption("Satellite tile simulation (30×30 grid)")
        
        fig_heat = px.imshow(
            spatial_grid,
            color_continuous_scale=[
                [0, "#8B4513"],
                [0.3, "#DAA520"],
                [0.5, "#90EE90"],
                [0.7, "#228B22"],
                [1.0, "#006400"]
            ],
            zmin=0.1, zmax=0.9,
            labels=dict(color="NDVI"),
            title=f"{region_info['state']} Forest Cover"
        )
        fig_heat.update_layout(height=320, coloraxis_showscale=True)
        st.plotly_chart(fig_heat, use_container_width=True)
    
    # NDVI Classification
    st.subheader("NDVI Classification Breakdown")
    ndvi_arr = np.array(ndvi_data["ndvi_values"])
    
    classes = {
        "Dense Forest (>0.6)": (ndvi_arr > 0.6).sum(),
        "Moderate (0.4–0.6)": ((ndvi_arr >= 0.4) & (ndvi_arr <= 0.6)).sum(),
        "Sparse (<0.4)": (ndvi_arr < 0.4).sum()
    }
    
    cols = st.columns(3)
    colors = ["#15803d", "#ca8a04", "#dc2626"]
    for i, (label, count) in enumerate(classes.items()):
        pct = count / len(ndvi_arr) * 100
        cols[i].metric(label, f"{pct:.1f}%", f"{count} months")

# ── TAB 2: Carbon Estimation ──────────────────

with tab2:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Biomass & Carbon Breakdown")
        
        breakdown_data = {
            "Component": ["Above Ground Biomass", "Below Ground Biomass", "Carbon Stock", "CO2 Equivalent"],
            "Per Hectare": [
                estimate.agb_per_ha,
                estimate.bgb_per_ha,
                estimate.carbon_stock_per_ha,
                estimate.co2e_per_ha
            ],
            "Unit": ["t DM/ha", "t DM/ha", "tC/ha", "tCO2e/ha"]
        }
        
        df_breakdown = pd.DataFrame(breakdown_data)
        
        fig_bar = go.Figure(go.Bar(
            x=df_breakdown["Per Hectare"],
            y=df_breakdown["Component"],
            orientation="h",
            marker_color=["#15803d", "#4ade80", "#0369a1", "#0ea5e9"],
            text=[f"{v:.1f} {u}" for v, u in zip(df_breakdown["Per Hectare"], df_breakdown["Unit"])],
            textposition="outside"
        ))
        fig_bar.update_layout(
            height=320,
            xaxis_title="Value per hectare",
            plot_bgcolor="black",
            paper_bgcolor="black"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.subheader("Annual Carbon Sequestration")
        
        annual_df = pd.DataFrame(sequestration["annual_data"])
        
        fig_seq = go.Figure()
        fig_seq.add_trace(go.Bar(
            x=annual_df["year"].astype(str),
            y=annual_df["total_co2e"] / 1000,
            name="Total Carbon Stock",
            marker_color="#15803d"
        ))
        fig_seq.add_trace(go.Bar(
            x=annual_df["year"].astype(str),
            y=annual_df.get("incremental_credits", pd.Series([0]*len(annual_df))) / 1000,
            name="Incremental Credits (Tradeable)",
            marker_color="#86efac"
        ))
        
        fig_seq.update_layout(
            height=320,
            yaxis_title="Thousand tCO2e",
            barmode="group",
            plot_bgcolor="black",
            paper_bgcolor="black",
            legend=dict(orientation="h", y=-0.2)
        )
        st.plotly_chart(fig_seq, use_container_width=True)
    
    # Methodology note
    st.info(
        f"**Methodology:** {estimate.methodology} | "
        f"**Confidence Level:** {estimate.confidence_level} | "
        f"**Data:** {'Sentinel-2 Simulation' if 'mock' in ndvi_data['data_source'] else 'Live Satellite'}"
    )

# ── TAB 3: Credit Valuation ───────────────────

with tab3:
    st.subheader("Carbon Credit Market Comparison")
    
    col1, col2, col3 = st.columns(3)
    
    markets = [
        ("CCTS Compliance", valuation.ccts_value_inr, "#0369a1", "Regulated industries"),
        ("India VCM", valuation.vcm_domestic_value_inr, "#15803d", "Corporate ESG buyers"),
        ("International VCM", valuation.vcm_international_value_inr, "#7c3aed", "Global MNCs / CORSIA")
    ]
    
    for col, (name, val_inr, color, buyer) in zip([col1, col2, col3], markets):
        is_best = name == valuation.best_market
        with col:
            suffix = " ✅ BEST" if is_best else ""
            st.markdown(f"**{name}{suffix}**")
            st.metric(
                "Credit Value",
                f"₹{val_inr/1e7:.2f} Cr",
                f"${val_inr/83.5/1e6:.2f}M"
            )
            st.caption(f"Buyers: {buyer}")
    
    st.markdown("---")
    
    # Price sensitivity chart
    st.subheader("Credit Value vs. Carbon Price Sensitivity")
    
    price_range = list(range(200, 4200, 200))
    values_inr = [valuation.verified_credits * p for p in price_range]
    
    fig_sens = go.Figure()
    fig_sens.add_trace(go.Scatter(
        x=price_range,
        y=[v / 1e7 for v in values_inr],
        mode="lines+markers",
        line=dict(color="#15803d", width=2),
        fill="tozeroy",
        fillcolor="rgba(21, 128, 61, 0.1)"
    ))
    
    # Mark current market prices
    for market_key, market_data in MARKET_PRICES.items():
        fig_sens.add_vline(
            x=market_data["price_inr_per_tonne"],
            line_dash="dash",
            line_color="gray",
            annotation_text=market_data["name"].split(" ")[0]
        )
    
    fig_sens.update_layout(
        height=300,
        xaxis_title="Carbon Price (₹/tonne)",
        yaxis_title="Total Value (₹ Crore)",
        plot_bgcolor="black",
        paper_bgcolor="black"
    )
    st.plotly_chart(fig_sens, use_container_width=True)
    
    # Platform revenue
    st.subheader("CarbonMRV Platform Revenue from This Project")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("MRV Verification Fee", f"₹{valuation.mrv_fee_revenue_inr:,.0f}", "₹12/tonne")
    with col2:
        st.metric("Marketplace Commission", f"₹{valuation.marketplace_revenue_inr:,.0f}", "2.5% of GMV")

# ── TAB 4: Platform Revenue ───────────────────

with tab4:
    st.subheader("🚀 CarbonMRV Startup — Revenue Projection Model")
    
    st.markdown("""
    > **Business Model:** We don't sell carbon credits — we are the **infrastructure layer** 
    that verifies, routes, and tracks them. Revenue from MRV fees, SaaS, and marketplace commission.
    """)
    
    # Projection inputs
    col1, col2, col3 = st.columns(3)
    with col1:
        proj_tonnes = st.slider("Annual Tonnes Verified (M)", 0.5, 50.0, 5.0, 0.5)
    with col2:
        proj_clients = st.slider("Enterprise ESG Clients", 5, 500, 50, 5)
    with col3:
        proj_gmv_cr = st.slider("Marketplace GMV (₹ Cr)", 10, 1000, 100, 10)
    
    rev = calculate_platform_revenue_projection(
        proj_tonnes * 1_000_000,
        proj_clients,
        proj_gmv_cr * 1e7
    )
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("MRV Revenue", f"₹{rev['mrv_verification_revenue_inr']/1e7:.1f} Cr")
    col2.metric("Dashboard SaaS", f"₹{rev['dashboard_saas_revenue_inr']/1e7:.1f} Cr")
    col3.metric("Marketplace", f"₹{rev['marketplace_commission_inr']/1e7:.1f} Cr")
    col4.metric("**TOTAL ARR**", f"₹{rev['total_revenue_crore']} Cr", f"${rev['total_revenue_usd_million']}M")
    
    st.markdown("---")
    
    # 5-year projection chart
    st.subheader("5-Year Revenue Roadmap")
    
    projections = []
    growth_stages = [
        (1, 0.5, 10, 10, "Seed"),
        (2, 3, 30, 60, "Series A"),
        (3, 15, 100, 300, "Series A+"),
        (4, 35, 250, 800, "Series B"),
        (5, 60, 500, 2000, "Series B+")
    ]
    
    for year, tonnes_m, clients, gmv_cr, stage in growth_stages:
        r = calculate_platform_revenue_projection(tonnes_m * 1e6, clients, gmv_cr * 1e7)
        projections.append({
            "Year": f"Y{year} ({stage})",
            "MRV Fees": r["mrv_verification_revenue_inr"] / 1e7,
            "SaaS": r["dashboard_saas_revenue_inr"] / 1e7,
            "Marketplace": r["marketplace_commission_inr"] / 1e7,
            "Total": r["total_revenue_crore"]
        })
    
    proj_df = pd.DataFrame(projections)
    
    fig_proj = go.Figure()
    for col, color in [("MRV Fees", "#15803d"), ("SaaS", "#0369a1"), ("Marketplace", "#7c3aed")]:
        fig_proj.add_trace(go.Bar(
            name=col,
            x=proj_df["Year"],
            y=proj_df[col],
            marker_color=color
        ))
    
    fig_proj.update_layout(
        barmode="stack",
        height=380,
        yaxis_title="Revenue (₹ Crore)",
        plot_bgcolor="black",
        paper_bgcolor="black",
        legend=dict(orientation="h", y=-0.2)
    )
    
    st.plotly_chart(fig_proj, use_container_width=True)
    
    # $100M milestone
    target_rev = proj_df[proj_df["Total"] >= 100/83.5*100]
    if not target_rev.empty:
        milestone_year = target_rev.iloc[0]["Year"]
        st.success(f"🎯 **$100M ARR milestone reached: {milestone_year}** based on current projections")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────

st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🌿 CarbonMRV India | v0.1.0")
with col2:
    st.caption("📋 Methodology: IPCC Tier 2 | India FSI BCF")
with col3:
    st.caption("🛰️ Data: Sentinel-2 Simulation | GEE-ready")
