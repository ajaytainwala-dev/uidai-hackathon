
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
import json

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from aadhaar_analytics.ingestion import loader
from aadhaar_analytics.preprocessing import cleaning, feature_engineering
from aadhaar_analytics.analytics.descriptive import DescriptiveAnalytics
from aadhaar_analytics.analytics.diagnostic import DiagnosticAnalytics
from aadhaar_analytics.analytics.predictive import PredictiveAnalytics
from aadhaar_analytics.analytics.prescriptive import PrescriptiveAnalytics
from aadhaar_analytics.ai.gemini_service import GeminiService
from aadhaar_analytics.visualization import charts
from aadhaar_analytics.utils import constants

st.set_page_config(page_title="UIDAI Aadhaar Analytics", layout="wide", page_icon="🇮🇳")

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: #000000;
    }
    h1, h2, h3 {
        color: #2c3e50;
        font-family: 'Inter', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# Add specific css for metrics separately to ensure it overrides defaults
st.markdown("""
<style>
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: #000000 !important;
    }
    .css-1r6slb0.e1tzin5v2 {
        background-color: #ffffff;
        border: 1px solid #dcdcdc;
        border-radius: 10px;
        padding: 20px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 5px;
        padding: 10px 20px;
        color: #000000;
        font-weight: bold;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .ai-box {
        background-color: #f0f7ff;
        border-left: 5px solid #0068c9;
        padding: 15px;
        border-radius: 5px;
        margin-top: 10px;
        color: #000000;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Loads and cleans data."""
    data = loader.load_all_datasets()
    
    # Enrolment
    df_enr = data.get('enrolment', pd.DataFrame())
    df_enr = cleaning.clean_dataframe(df_enr, 'enrolment')
    df_enr = feature_engineering.add_time_features(df_enr)

    # Demographic
    df_demo = data.get('demographic', pd.DataFrame())
    df_demo = cleaning.clean_dataframe(df_demo, 'demographic')
    df_demo = feature_engineering.add_time_features(df_demo)

    # Biometric
    df_bio = data.get('biometric', pd.DataFrame())
    df_bio = cleaning.clean_dataframe(df_bio, 'biometric')
    df_bio = feature_engineering.add_time_features(df_bio)

    return df_enr, df_demo, df_bio

# Load Data
with st.spinner('Loading Aadhaar Datasets...'):
    df_enr, df_demo, df_bio = load_data()

# --- Sidebar Filters ---
# --- Sidebar Filters & AI Config ---
st.sidebar.header("Configuration")

# API Key
# api_key = ""
try:
    from dotenv import load_dotenv
    load_dotenv()
    api_key_env = os.getenv("GEMINI_API_KEY")
except ImportError:
    api_key_env = None

api_key = api_key_env or st.sidebar.text_input("🔑 Gemini API Key", type="password", help="Enter your Google Gemini API Key to enable AI insights.")
gemini = GeminiService(api_key) if api_key else None

if not api_key:
    st.sidebar.warning("⚠️ Enter API Key for AI features")

st.sidebar.divider()
st.sidebar.header("Debug Info")
st.sidebar.text(f"CWD: {os.getcwd()}")
st.sidebar.text(f"Base: {constants.BASE_DIR}")
chk_path = os.path.join(constants.BASE_DIR, "api_data_aadhar_enrolment")
st.sidebar.text(f"Path Exists: {os.path.exists(chk_path)}")
if os.path.exists(chk_path):
    st.sidebar.text(f"Files: {len(os.listdir(chk_path))}")
    st.sidebar.text(f"Sample: {os.listdir(chk_path)[:2]}")
else:
    st.sidebar.error(f"Missing: {chk_path}")

st.sidebar.divider()
st.sidebar.header("Filter Options")

# State Filter
# State Filter
all_states = set()
if not df_enr.empty and constants.COL_STATE in df_enr.columns:
    all_states.update(df_enr[constants.COL_STATE].dropna().unique().tolist())
if not df_demo.empty and constants.COL_STATE in df_demo.columns:
    all_states.update(df_demo[constants.COL_STATE].dropna().unique().tolist())
if not df_bio.empty and constants.COL_STATE in df_bio.columns:
    all_states.update(df_bio[constants.COL_STATE].dropna().unique().tolist())

all_states = sorted(list(all_states))
selected_state = st.sidebar.selectbox("Select State", ["All"] + all_states)

# Filter Dataframes
if selected_state != "All":
    df_enr = df_enr[df_enr[constants.COL_STATE] == selected_state] if not df_enr.empty else df_enr
    df_demo = df_demo[df_demo[constants.COL_STATE] == selected_state] if not df_demo.empty else df_demo
    df_bio = df_bio[df_bio[constants.COL_STATE] == selected_state] if not df_bio.empty else df_bio

# Initialize Analytics Modules
desc_analytics = DescriptiveAnalytics(df_enr, df_demo, df_bio)
diag_analytics = DiagnosticAnalytics(df_enr, df_demo, df_bio)
pred_analytics = PredictiveAnalytics(df_enr, df_bio)
presc_analytics = PrescriptiveAnalytics(df_enr, df_bio)

# --- Header ---
st.title("INDIA UIDAI Aadhaar Analytics Dashboard")
st.markdown("""
### Policy-Grade Decision Support System
This dashboard provides a comprehensive 360-degree view of the Aadhaar ecosystem. It is designed to empower decision-makers with:
- **Real-time Lifecycle Monitoring**: Tracking the journey from enrolment to updates.
- **Fraud & Anomaly Detection**: Identifying suspicious activities using statistical outliers.
- **Predictive Resource Planning**: Forecasting demand to optimize infrastructure allocation.
- **AI-Driven Intelligence**: Leveraging Generative AI to provide automated, context-aware executive summaries and policy drafts.
""")

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Overview (KPIs)", "Enrolment Analytics", "Demographic Updates", 
    "Biometric Updates", "Predictions", "Recommendations", "Advanced Diagnostics"
])

# --- Tab 1: Overview ---
with tab1:
    kpis = feature_engineering.calculate_kpis(df_enr, df_demo, df_bio)
    
    # --- Gauge & KPI Section ---
    g1, g2 = st.columns([1, 2])
    
    with st.container():
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Enrolments", f"{kpis['total_enrolments']:,}")
        c2.metric("Total Demographic Updates", f"{kpis['total_demo_updates']:,}", delta_color="normal")
        c3.metric("Total Biometric Updates", f"{kpis['total_bio_updates']:,}")
    
    if kpis['total_enrolments'] == 0:
        st.error("⚠️ No Data Loaded! The dataset appears to be empty. Please check the 'Debug Info' in the sidebar to verify file paths.")
    # with g1:
        # Gauge Chart for System Health (Update Saturation)
    total_updates = kpis.get('total_demo_updates', 0) + kpis.get('total_bio_updates', 0)
    total_enr = kpis.get('total_enrolments', 1) # Avoid div 0
    saturation = (total_updates / total_enr) * 100 if total_enr > 0 else 0
    # Update Intensity Score
    st.markdown("""
    **Update Intensity Score**  
    This metric measures the ratio of lifecycle updates (demographic and biometric) relative to total enrolments. 
    A higher score indicates a mature ecosystem where the focus has shifted from initial population coverage to data maintenance and accuracy.
    """)
    fig_gauge = charts.plot_gauge(saturation, "Update Intensity Score", 0, 100)
    st.plotly_chart(fig_gauge, use_container_width=True)
    with st.expander("💡 Analyst Insights: Update Intensity", expanded=True):
            st.markdown("""
            **Detected Patterns**:
            - **< 10% (Acquisition Phase)**: Focus is on new enrolments.
            - **> 40% (Mature Phase)**: Population saturated; focus shifts to maintenance (updates).
            - **Urban Skew**: Higher intensity in metros due to high mobility/rental changes.
            
            **Predictive & Decision Making**:
            - **Budget Shift**: Rising score signals need to shift budget from *Enrolment Machines* to *Update Centers*.
            - **Anomaly**: Spikes >80% may indicate fraud rings or sudden localized mandates.
            """)
        
    # with g2:
   
    
    # --- Bullet Chart for Daily Targets (Hypothetical) ---
    st.divider()
    avg_daily_enr = kpis['total_enrolments'] / 30 # Approx for month
    target_daily = 50000 
    st.header("Daily Enrollment Average (DEA)")
    fig_bullet = charts.plot_bullet("DEA", avg_daily_enr, target_daily, target_daily*1.5)
    st.plotly_chart(fig_bullet, use_container_width=True)
    with st.expander("💡 Analyst Insights: Performance Tracking", expanded=True):
        st.markdown("""
        **Patterns & Anomalies**:
        - **Fiscal Rush**: Surges in March for benefit renewals.
        - **Overshooting (>150%)**: May indicate "forced" mass enrolments, leading to data quality errors.
        
        **Prescriptive Measures**:
        - **Automated Alerts**: Trigger notices for DMs if district stays in "Poor" band (Gray) for > 7 days.
        - **Incentives**: Use this metric for Regional Office (RO) performance reviews.
        """)

    if gemini:
        # Generate unique key for caching based on state and total enrolments (as a proxy for data change)
        kpi_state_key = f"kpi_summary_{selected_state}_{kpis.get('total_enrolments', 0)}"
        
        if kpi_state_key not in st.session_state:
            with st.spinner("🤖 AI Analyst is generating Executive Summary..."):
                try:
                    summary = gemini.explain_kpis(kpis, selected_state)
                    st.session_state[kpi_state_key] = summary
                except Exception as e:
                    st.session_state[kpi_state_key] = f"AI Analysis failed: {str(e)}"

        st.markdown(f"""
        <div class="ai-box">
            <b>🤖 AI Executive Summary:</b><br>
            {st.session_state[kpi_state_key]}
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    st.subheader("Regional Performance (Bar)")
if not df_enr.empty:
    summary = desc_analytics.get_state_wise_summary('enrolment')
    if not summary.empty:
        summary['Total'] = summary.sum(axis=1, numeric_only=True)
        fig = charts.plot_bar_metrics(summary.sort_values('Total', ascending=False).head(10), constants.COL_STATE, 'Total', "Top 10 States by Enrolment")
        st.plotly_chart(fig, width="stretch")
        st.caption("Detailed breakdown of enrolment volumes by state. Identifies the primary contributors to the national database.")

st.subheader("Geographic Distribution (Treemap)")
if not df_enr.empty:
    with st.spinner("Generating Treemap..."):
        cols = [constants.COL_ENR_AGE_0_5, constants.COL_ENR_AGE_5_17, constants.COL_ENR_AGE_18_PLUS]
        treemap_df = feature_engineering.aggregate_by_region(df_enr, cols)
        treemap_df['Total'] = treemap_df[cols].sum(axis=1)
        if len(treemap_df) > 1000:
            treemap_df = treemap_df.nlargest(1000, 'Total')
            
        fig_tree = charts.plot_treemap(treemap_df, [constants.COL_STATE, constants.COL_DISTRICT], 'Total', "Enrolment Distribution Hierarchy")
        st.plotly_chart(fig_tree, width="stretch")

    # Geospatial Map
    st.subheader("Geospatial Analysis (Map)")
    geojson_path = os.path.join(os.path.dirname(__file__), '../data/geo/india_states.geojson')
    
    if os.path.exists(geojson_path):
        with open(geojson_path, 'r') as f:
            india_geojson = json.load(f)
        
        # Aggregate by State for the map
        if not df_enr.empty:
            map_df = df_enr.groupby(constants.COL_STATE).size().reset_index(name='Total Enrolments')
            
            # Using 'properties.ST_NM' as the key in GeoJSON for State Name
            fig_map = charts.plot_choropleth(
                map_df, 
                india_geojson, 
                constants.COL_STATE, 
                'Total Enrolments', 
                'properties.ST_NM', 
                "State-wise Enrolment Density"
            )
            st.plotly_chart(fig_map, use_container_width=True)
            st.caption("**Geospatial Map**: Color intensity represents the volume of enrolments across different states. Darker regions indicate higher saturation.")
    else:
        st.info("⚠️ Geospatial data not found. Please run `setup_geo.py` to download the map data.")

# --- Tab 2: Enrolment Analytics ---
with tab2:
    st.subheader("Enrolment Trends & Distribution")
    
    col1, col2 = st.columns(2)
    
    # with col1:
        # Age breakdown
    if not df_enr.empty:
        summary_age = df_enr[[constants.COL_ENR_AGE_0_5, constants.COL_ENR_AGE_5_17, constants.COL_ENR_AGE_18_PLUS]].sum().reset_index()
        summary_age.columns = ['Age Group', 'Count']
        fig_age = px.pie(summary_age, values='Count', names='Age Group', title="Enrolment by Age Group", hole=0.4)
        st.plotly_chart(fig_age, width="stretch")
        st.markdown("""
        **Age-Wise Enrollment Profile**  
        This chart visualizes the distribution of enrolments across three primary lifecycle categories: 
        - **Infants (0-5)**: Focus on new birth registrations (Baal Aadhaar).
        - **Youth (5-17)**: Targeting school-age children and mandatory biometric updates.
        - **Adult (18+)**: Capturing late-stage enrolments and saturation among the adult population.
        """)

        # Funnel Chart
        st.subheader("Lifecycle Funnel")
        if not df_enr.empty:
            funnel_data = {
                'Infant (0-5)': df_enr[constants.COL_ENR_AGE_0_5].sum(),
                'Youth (5-17)': df_enr[constants.COL_ENR_AGE_5_17].sum(),
                'Adult (18+)': df_enr[constants.COL_ENR_AGE_18_PLUS].sum()
            }
            fig_funnel = charts.plot_funnel(funnel_data, "Enrolment Lifecycle Stages")
            st.plotly_chart(fig_funnel, width="stretch")
            
            with st.expander("💡 Analyst Insights: Lifecycle Funnel", expanded=True):
                 st.markdown("""
                 **Critical Anomaly (MBU Failure)**:
                 - If the **Youth (5-17)** band is significantly narrower than **Infant (0-5)**, it indicates children turning 5 are **NOT** updating biometrics.
                 
                 **Prescriptive**:
                 - **School Intervention**: Target schools for 'Baal Aadhaar' camps.
                 - **Policy**: Link mandatory biometric updates to school ID issuance to fix leakage.
                 """)
    
    # with col2:
        # Trend
    trend_df = desc_analytics.get_trend_analysis('enrolment')
    if not trend_df.empty:
        # Need to melt for multi-line
        trend_melt = trend_df.melt(id_vars=[constants.COL_DATE], var_name='Age Group', value_name='Count')
        fig_trend = charts.plot_trend(trend_melt, "Monthly Enrolment Trend", x_col=constants.COL_DATE, y_col='Count', color_col='Age Group')
        st.plotly_chart(fig_trend, width="stretch")
        
        with st.expander("💡 Analyst Insights: Trend & Seasonality", expanded=True):
            st.markdown("""
            **Detected Patterns**:
            - **School Cycles**: Peaks in **May-July** correlate with admission seasons (Age 5-17).
            - **Adult Flatline**: Adult enrolments should be near zero in 90%+ saturated states.
            
            **Security Red Flag**:
            - **Adult Surge**: Sudden rise in *fresh* Adult enrolments (18+) in border states could indicate **illegal infiltration**.
            
            **Resource Planning**:
            - **Pre-emptive Scaling**: Scale server capacity in April to handle May-July rush.
            """)
            
    st.divider()
    st.subheader("Age Composition Over Time (Stacked)")
    if 'trend_df' in locals() and not trend_df.empty:
        trend_melt = trend_df.melt(id_vars=[constants.COL_DATE], var_name='Age Group', value_name='Count')
        fig_area = charts.plot_stacked_area(trend_melt, constants.COL_DATE, 'Count', 'Age Group', "Enrolment Composition Shift")
        st.plotly_chart(fig_area, width="stretch")

    if gemini and 'trend_df' in locals() and not trend_df.empty:
        trend_key = f"trend_analysis_{selected_state}_{trend_df.shape[0]}"
        
        if trend_key not in st.session_state:
             with st.spinner("🤖 AI Analyst is detecting trend patterns..."):
                 try:
                    analysis = gemini.analyze_trends(trend_df, "Enrolment")
                    st.session_state[trend_key] = analysis
                 except Exception as e:
                     st.session_state[trend_key] = "Could not generate trend analysis."

        with st.expander("✨ AI Trend Analysis", expanded=True):
             st.markdown("#### Intelligent Pattern Recognition")
             st.markdown(st.session_state[trend_key])

# --- Tab 3: Demographic Updates ---
with tab3:
    st.subheader("Demographic Update Patterns")
    
    col_diag_1, col_diag_2 = st.columns(2)
    
    with col_diag_1:
        if not df_demo.empty:
            trend_demo = desc_analytics.get_trend_analysis('demographic')
            if not trend_demo.empty:
                 trend_melt = trend_demo.melt(id_vars=[constants.COL_DATE], var_name='Age Group', value_name='Count')
                 fig = charts.plot_trend(trend_melt, "Demographic Updates Over Time", x_col=constants.COL_DATE, y_col='Count', color_col='Age Group')
                 st.plotly_chart(fig, width="stretch")
        
    with col_diag_2:
        ratio_df = diag_analytics.calculate_update_vs_enrolment_ratio()
        if not ratio_df.empty:
            st.markdown("**Update-to-Enrolment Ratio (Service Pressure)**")
            st.dataframe(ratio_df[[constants.COL_STATE, 'update_enrolment_ratio', 'total_updates', 'total_enrolments']].head(15), width="stretch")
            
    st.divider()
    
    st.subheader("Advanced Diagnostic Metrics")
    d1, d2 = st.columns(2)
    
    with d1:
        st.markdown("**Correlation Matrix (Enrolment vs Updates)**")
        with st.spinner("Calculating Correlations..."):
            corr_mat = diag_analytics.get_correlation_matrix()
            if not corr_mat.empty:
                fig_corr = charts.plot_correlation_heatmap(corr_mat)
                st.plotly_chart(fig_corr, width="stretch")
                
    with d2:
        st.markdown("**Outlier Detection (Districts)**")
        dataset_type_outlier = st.selectbox("Select Dataset for Outliers", ["enrolment", "biometric"])
        with st.spinner("Detecting Outliers..."):
            outliers = diag_analytics.detect_district_outliers(dataset_type_outlier)
            if not outliers.empty:
                # Plot Box Plot
                fig_box = charts.plot_box_distribution(outliers, constants.COL_STATE, 'total', f"Distribution & Outliers ({dataset_type_outlier.capitalize()})")
                st.plotly_chart(fig_box, width="stretch")
                
                with st.expander("💡 Analyst Insights: Outlier Detection", expanded=True):
                    st.markdown("""
                    **Anomaly Detection**:
                    - **Extreme Outliers**: Districts far above the upper whisker suggest **Operator Malpractice** (fake updates for profit).
                    
                    **Prescriptive Action**:
                    - **Vigilance Squads**: Dispatch inspection teams to the top 3 outlier districts.
                    - **Blacklisting**: Suspend licenses in these districts pending audit.
                    """)
                
                 # Show Table
                st.caption("Top Anomalous Districts")
                st.dataframe(outliers.head(5), width="stretch")

    st.divider()
    
    # Scatter Plot for In-Depth Correlation
    st.subheader("Multi-Variate Analysis (Scatter)")
    if not ratio_df.empty:
        # Create a more rich dataset for scatter
        # ratio_df has State, but we might want District level if available or stick to State
        fig_scatter = charts.plot_scatter(ratio_df, 'total_enrolments', 'total_updates', size_col='update_enrolment_ratio', color_col=constants.COL_STATE, title="Enrolment vs Updates (Size = Ratio)")
        st.plotly_chart(fig_scatter, width="stretch")
        with st.expander("💡 Analyst Insights: Service Pressure Matrix", expanded=True):
            st.markdown("""
            **Quadrant Analysis**:
            - **Top-Right (High Enrolment, High Updates)**: "Hyper-Active" zones. Require mega-update centers.
            - **Top-Left (Low Enrolment, High Updates)**: **Suspicious**. Small population updating frequently? Potential **Identity Fraud** (Name/DOB changes).
            
            **Policy Action**:
            - **Fraud Filters**: Apply stricter limits on # of demographic updates for users in Top-Left quadrant.
            """)

# --- Tab 4: Biometric Updates ---
with tab4:
    st.subheader("Biometric Update Analysis")
    if not df_bio.empty:
         trend_bio = desc_analytics.get_trend_analysis('biometric')
         if not trend_bio.empty:
             trend_melt = trend_bio.melt(id_vars=[constants.COL_DATE], var_name='Age Group', value_name='Count')
             fig = charts.plot_trend(trend_melt, "Biometric Updates Trend", x_col=constants.COL_DATE, y_col='Count', color_col='Age Group')
             st.plotly_chart(fig, width="stretch")
         
         # Heatmap of Bio Updates by District (if State selected)
         if selected_state != "All" and not df_bio.empty:
             agg_bio = feature_engineering.aggregate_by_region(df_bio, [constants.COL_BIO_AGE_5_17, constants.COL_BIO_AGE_18_PLUS])
             agg_bio['Total'] = agg_bio[constants.COL_BIO_AGE_5_17] + agg_bio[constants.COL_BIO_AGE_18_PLUS]
             fig_map = px.bar(agg_bio.sort_values('Total', ascending=False).head(20), x=constants.COL_DISTRICT, y='Total', title=f"Top Districts in {selected_state} for Bio Updates")
             st.plotly_chart(fig_map, width="stretch")

# --- Tab 5: Predictions ---
with tab5:
    st.subheader("Future Demand Forecasting (Next 3 Months)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Enrolment Forecast**")
        forecast_enr = pred_analytics.forecast_enrolment_demand()
        if not forecast_enr.empty:
            fig_pred = charts.plot_trend(forecast_enr, "Enrolment Forecast", x_col='date', y_col='forecast', color_col='type')
            st.plotly_chart(fig_pred, width="stretch")
            st.info("**Capacity Planning**: If Forecast > System Capacity, schedule 'Burst Capacity' contracts for localized hardware.")
        else:
            st.warning("Not enough data for Enrolment forecast")
            
    with col2:
        st.markdown("**Biometric Load Forecast**")
        forecast_bio = pred_analytics.forecast_biometric_load()
        if not forecast_bio.empty:
            fig_pred_bio = charts.plot_trend(forecast_bio, "Biometric Update Forecast", x_col='date', y_col='forecast', color_col='type')
            st.plotly_chart(fig_pred_bio, width="stretch")
            st.info("**Risk Alert**: Divergence between Forecast and Actuals suggests external 'Shock Events' (e.g., new Govt scheme).")
        else:
            st.warning("Not enough data for Biometric forecast")

# --- Tab 6: Recommendations ---
with tab6:
    st.subheader("Policy Recommendations (Prescriptive)")
    
    # Sliders for thresholds
    th_enr = st.slider("Enrolment High Load Threshold", 100, 10000, 1000)
    th_bio = st.slider("Biometric High Load Threshold", 100, 5000, 500)
    
    recs = presc_analytics.get_recommendations(threshold_enr=th_enr, threshold_bio=th_bio)
    
    if not recs.empty:
        col_rec_1, col_rec_2 = st.columns([2, 1])
        
        with col_rec_1:
            st.warning(f" Identified {len(recs)} Actionable Areas")
            st.dataframe(recs, width="stretch")
            
            # Radar Chart for Top High Pressure Areas
            st.subheader("Pressure Analysis (Radar)")
            # Mocking normalization for radar
            radar_df = recs.head(3).copy()
            # Add dummy metrics for radar visualization if real ones aren't diverse enough
            # We will use simple counts normalized
            if 'Issue' in radar_df.columns:
                 # Extract numbers or use random for demo if strictly needed, but let's try to map real data
                 # We don't have columns in recs other than Issue/Action etc.
                 # Let's use the 'total' computed in prescriptive if available, or skip.
                 # Prescriptive returns just text mostly based on threshold.
                 pass
            
            # Since recs DF is limited, let's show Radar of State Performance instead (Overview Context)
            if not summary.empty:
                 top_3_states = summary.head(3)
                 # Normalize
                 max_val = top_3_states['Total'].max()
                 if max_val > 0:
                     radar_data = []
                     for _, row in top_3_states.iterrows():
                         radar_data.append(dict(theta='Age 0-5', r=row.get(constants.COL_ENR_AGE_0_5, 0)/max_val, name=row[constants.COL_STATE]))
                         radar_data.append(dict(theta='Age 5-17', r=row.get(constants.COL_ENR_AGE_5_17, 0)/max_val, name=row[constants.COL_STATE]))
                         radar_data.append(dict(theta='Age 18+', r=row.get(constants.COL_ENR_AGE_18_PLUS, 0)/max_val, name=row[constants.COL_STATE]))
                     
                     r_df = pd.DataFrame(radar_data)
                     fig_radar = px.line_polar(r_df, r='r', theta='theta', color='name', line_close=True, title="Demographic Profile Comparison (Normalized)")
                     fig_radar.update_traces(fill='toself')
                     st.plotly_chart(fig_radar, width="stretch")
                     with st.expander("💡 Analyst Insights: Demographic Strategy", expanded=True):
                        st.markdown("""
                        **Strategy Customization**:
                        - **Young States (Skewed 0-5)**: Focus on Tablet-based Enrolments in Hospitals.
                        - **Mature States (Skewed 18+)**: Focus on Self-Service Update Portals.
                        - **Transition**: A shrinking 0-5 axis over time predicts a future shrinking workforce.
                        """)

        with col_rec_2:
            st.markdown("### Actions")
            # Download button
            csv = recs.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Action Plan", csv, "action_plan.csv", "text/csv")
            
            if gemini:
                rec_key = f"policy_draft_{selected_state}_{len(recs)}"
                if rec_key not in st.session_state:
                     with st.spinner("🤖 AI Policy Consultant is drafting a directive..."):
                         try:
                             directive = gemini.recommend_policy(recs)
                             st.session_state[rec_key] = directive
                         except:
                             st.session_state[rec_key] = "Policy generation pending..."
                
                st.markdown("### 🏛️ Draft Policy Directive (AI Generated)")
                st.text_area("Official Directive Draft", st.session_state[rec_key], height=300)
    else:
        st.success("No critical high-load areas identified with current thresholds.")

