
import gradio as gr
import pandas as pd
import plotly.express as px
import sys
import os
import json
import logging
import numpy as np

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

# --- MEASURE GENERATORS ---
def get_measure_gauge(ratio):
    if ratio < 30:
        return "🇮🇳 **Strategic Measure**: ecosystem is in **Acquisition Mode**. \n**Action**: State Govt must deploy 'Mobile Aadhaar Vans' to uncovered Gram Panchayats immediately to boost enrolment numbers."
    return "🇮🇳 **Strategic Measure**: ecosystem is in **Maintenance Mode**. \n**Action**: Shift focus to **Data Hygiene**. Launch awareness campaigns for residents to update their POI/POA documents online."

def get_measure_bullet(val, target):
    if val < target:
        return "⚠️ **Correction Required**: Daily targets missed. \n**Action**: Regional Offices (RO) must review operator attendance and machine uptime. Consider incentives for operators working on weekends."
    return "✅ **On Track**: Targets met. \n**Action**: Maintain momentum. Conduct random quality audits to ensure speed isn't compromising data quality."

def get_measure_map():
    return "🗺️ **Regional Strategy**: \n**Action**: For 'Low Saturation' states (Lighter), integrate Aadhaar Enrolment with PDS (Ration) shops. For 'High Saturation' states (Darker), focus on Biometric Update Centers."

def get_measure_bar():
    return "📊 **Volume Management**: \n**Action**: Top 3 states require dedicated 'Server Lanes' in the CIDR backend to prevent latency during peak hours."

def get_measure_tree():
    return "🌳 **Demographic targeting**: \n**Action**: If 0-5 age group is small in any district, District Magistrates should mandate 'Aadhaar Camps' in Anganwadis and Maternity Wards."

def get_measure_pie():
    return "🍰 **Lifecycle Policy**: \n**Action**: **Baal Aadhaar (0-5)** requires 100% linkage with Birth Certificates. **Youth (5-17)** requires mandatory camps in Schools before Board Exams."

def get_measure_funnel():
    return "🔻 **Retention Strategy**: \n**Action**: High drop-off from Enrolment to Update suggests citizens forget Mandatory Biometric Updates (MBU). \n**Measure**: Send SMS alerts to parents when child turns 5 and 15."

def get_measure_trend():
    return "📈 **Capacity Planning**: \n**Action**: Correlate peaks with harvest or school admission seasons. Pre-book additional hardware for these months to avoid queues."

def get_measure_area():
    return "🌊 **Composition Policy**: \n**Action**: As the 'Adult' band shrinks in new enrolments, re-train operators from 'Enrolment' to 'Update/Correction' specialists."

def get_measure_scatter():
    return "💠 **Growth Zones**: \n**Action**: **Sleeping Giants** (High Pop, Low Growth) need political intervention/Chief Secretary review. **Fast Movers** need more kits."

def get_measure_demo_trend():
    return "📉 **Update Compliance**: \n**Action**: Vertical spikes in address updates often precede local elections. Ensure strict document verification (FOV) during these times to prevent voter fraud."

def get_measure_outliers():
    return "📦 **Fraud Prevention**: \n**Action**: Districts flagged as outliers must undergo **100% Packet Audit** for the next 30 days. Suspend rogue operators immediately."

def get_measure_bio_trend():
    return "🧬 **Biometric Security**: \n**Action**: If biometric updates are low, banking auth failures will rise. \n**Measure**: Partner with Banks to set up Iris Scanners at branches for localized updates."

# --- STATIC ANALYSIS HELPERS ---
def analyze_kpi_health(kpis):
    total_enr = kpis.get('total_enrolments', 0)
    total_updates = kpis.get('total_demo_updates', 0) + kpis.get('total_bio_updates', 0)
    
    if total_enr == 0:
        return "⚠️ **CRITICAL**: No Enrolment Data Found. System Check Required."
    
    ratio = (total_updates / total_enr) * 100
    
    analysis = f"""
    ### 📊 Static Diagnostic Report
    
    **System Maturity Score**: `{ratio:.1f}%` (Updates vs Enrolments)
    """
    return analysis

def analyze_demographic_anomalies(ratio_display):
    if ratio_display.empty:
        return "No data for analysis."
    top_district = ratio_display.iloc[0]
    avg_ratio = ratio_display['update_enrolment_ratio'].mean()
    
    analysis = f"""
    ### 🕵️‍♂️ Diagnostic: Demographic Pressure
    **Top High-Pressure District**: `{top_district[constants.COL_DISTRICT] if constants.COL_DISTRICT in top_district else top_district[constants.COL_STATE]}`
    **Ratio Deviation**: `{top_district['update_enrolment_ratio']:.2f}` vs Avg `{avg_ratio:.2f}`
    """
    return analysis

# --- DATA LOADING ---
print("Loading Datasets...")
raw_data = loader.load_all_datasets()
df_enr_all = cleaning.clean_dataframe(raw_data.get('enrolment', pd.DataFrame()), 'enrolment')
df_enr_all = feature_engineering.add_time_features(df_enr_all)

df_demo_all = cleaning.clean_dataframe(raw_data.get('demographic', pd.DataFrame()), 'demographic')
df_demo_all = feature_engineering.add_time_features(df_demo_all)

df_bio_all = cleaning.clean_dataframe(raw_data.get('biometric', pd.DataFrame()), 'biometric')
df_bio_all = feature_engineering.add_time_features(df_bio_all)
print("Data Loaded.")

# Load GeoJSON
geojson_path = os.path.join(os.path.dirname(__file__), '../data/geo/india_states.geojson')
india_geojson = None
if os.path.exists(geojson_path):
    with open(geojson_path, 'r') as f:
        india_geojson = json.load(f)

# Helper to get states
all_states = set()
if not df_enr_all.empty and constants.COL_STATE in df_enr_all.columns:
    all_states.update(df_enr_all[constants.COL_STATE].dropna().unique().tolist())
all_states = sorted(list(all_states))

def filter_data(selected_state):
    if selected_state == "All":
        return df_enr_all, df_demo_all, df_bio_all
    
    e = df_enr_all[df_enr_all[constants.COL_STATE] == selected_state] if not df_enr_all.empty else df_enr_all
    d = df_demo_all[df_demo_all[constants.COL_STATE] == selected_state] if not df_demo_all.empty else df_demo_all
    b = df_bio_all[df_bio_all[constants.COL_STATE] == selected_state] if not df_bio_all.empty else df_bio_all
    return e, d, b

def update_overview(selected_state, api_key):
    df_e, df_d, df_b = filter_data(selected_state)
    
    # KPIs
    kpis = feature_engineering.calculate_kpis(df_e, df_d, df_b)
    kpi_text = (
        f"### Total Enrolments: {kpis.get('total_enrolments', 0):,}\n"
        f"### Demographic Updates: {kpis.get('total_demo_updates', 0):,}\n"
        f"### Biometric Updates: {kpis.get('total_bio_updates', 0):,}"
    )
    
    # Static Analysis
    static_analysis_text = analyze_kpi_health(kpis)
    
    # Gauge
    total_updates = kpis.get('total_demo_updates', 0) + kpis.get('total_bio_updates', 0)
    total_enr = kpis.get('total_enrolments', 1)
    saturation = (total_updates / total_enr) * 100 if total_enr > 0 else 0
    fig_gauge = charts.plot_gauge(saturation, "System Maturity (Update Intensity %) ", 0, 100)
    m_gauge = get_measure_gauge(saturation)
    
    # Bullet
    avg_daily_enr = kpis.get('total_enrolments', 0) / 30
    target_daily = 50000 
    fig_bullet = charts.plot_bullet("Daily Run Rate (DEA)", avg_daily_enr, target_daily, target_daily*1.5)
    m_bullet = get_measure_bullet(avg_daily_enr, target_daily)
    
    # Bar Chart
    desc_analytics = DescriptiveAnalytics(df_e, df_d, df_b)
    fig_bar = None
    if not df_e.empty:
        summary = desc_analytics.get_state_wise_summary('enrolment')
        if not summary.empty:
            summary['Total'] = summary.sum(axis=1, numeric_only=True)
            top_10 = summary.sort_values('Total', ascending=False).head(10)
            fig_bar = charts.plot_bar_metrics(top_10, constants.COL_STATE, 'Total', "Top 10 High Volume States")
    m_bar = get_measure_bar()
        
    # Treemap
    fig_tree = None
    if not df_e.empty:
        cols = [constants.COL_ENR_AGE_0_5, constants.COL_ENR_AGE_5_17, constants.COL_ENR_AGE_18_PLUS]
        treemap_df = feature_engineering.aggregate_by_region(df_e, cols)
        treemap_df['Total'] = treemap_df[cols].sum(axis=1)
        if len(treemap_df) > 1000:
            treemap_df = treemap_df.nlargest(1000, 'Total')
        fig_tree = charts.plot_treemap(treemap_df, [constants.COL_STATE, constants.COL_DISTRICT], 'Total', "Geo-Hierarchy of Enrolment")
    m_tree = get_measure_tree()

    # Geo Map (New)
    fig_map = None
    if india_geojson and not df_e.empty:
         map_df = df_e.groupby(constants.COL_STATE).size().reset_index(name='Total')
         fig_map = charts.plot_choropleth(map_df, india_geojson, constants.COL_STATE, 'Total', 'properties.ST_NM', "State-wise Enrolment Saturation")
    m_map = get_measure_map()

    # AI Summary
    ai_output = "🤖 **AI Analyst**: Enter an API Key to generate specific insights."
    if api_key:
        gemini = GeminiService(api_key)
        try:
            ai_output = gemini.explain_kpis(kpis, selected_state)
        except Exception as e:
            ai_output = f"Error: {e}"
            
    return kpi_text, static_analysis_text, fig_gauge, m_gauge, fig_bullet, m_bullet, fig_bar, m_bar, fig_tree, m_tree, fig_map, m_map, ai_output

def update_enrolment(selected_state, api_key):
    df_e, df_d, df_b = filter_data(selected_state)
    desc_analytics = DescriptiveAnalytics(df_e, df_d, df_b)
    
    # Age Pie
    fig_pie = None
    if not df_e.empty:
        summary_age = df_e[[constants.COL_ENR_AGE_0_5, constants.COL_ENR_AGE_5_17, constants.COL_ENR_AGE_18_PLUS]].sum().reset_index()
        summary_age.columns = ['Age Group', 'Count']
        fig_pie = px.pie(summary_age, values='Count', names='Age Group', title="Enrolment Demographics (Age)", hole=0.4)
        fig_pie.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    m_pie = get_measure_pie()
        
    # Funnel
    fig_funnel = None
    if not df_e.empty:
        funnel_data = {
            'Infant (0-5)': df_e[constants.COL_ENR_AGE_0_5].sum(),
            'Youth (5-17)': df_e[constants.COL_ENR_AGE_5_17].sum(),
            'Adult (18+)': df_e[constants.COL_ENR_AGE_18_PLUS].sum()
        }
        fig_funnel = charts.plot_funnel(funnel_data, "Lifecycle Funnel (Retention)")
    m_funnel = get_measure_funnel()
        
    # Trend & Area
    fig_trend = None
    fig_area = None
    trend_df = desc_analytics.get_trend_analysis('enrolment')
    if not trend_df.empty:
        trend_melt = trend_df.melt(id_vars=[constants.COL_DATE], var_name='Age Group', value_name='Count')
        fig_trend = charts.plot_trend(trend_melt, "Monthly Enrolment Velocity", x_col=constants.COL_DATE, y_col='Count', color_col='Age Group')
        fig_area = charts.plot_stacked_area(trend_melt, constants.COL_DATE, 'Count', 'Age Group', "Net Composition Change Area")
    m_trend = get_measure_trend()
    m_area = get_measure_area()
        
    # Scatter
    fig_scatter = None
    if not df_e.empty:
         state_agg = df_e.groupby(constants.COL_STATE).sum(numeric_only=True)
         state_agg['Total'] = state_agg[constants.COL_ENR_AGE_0_5] + state_agg[constants.COL_ENR_AGE_5_17] + state_agg[constants.COL_ENR_AGE_18_PLUS]
         state_agg['Birth_Rate_Proxy'] = state_agg[constants.COL_ENR_AGE_0_5] / state_agg['Total']
         state_agg = state_agg.reset_index()
         fig_scatter = charts.plot_scatter(state_agg, 'Total', 'Birth_Rate_Proxy', size_col='Total', color_col=constants.COL_STATE, title="State Growth Matrix")
    m_scatter = get_measure_scatter()
        
    # AI Trend
    ai_trend = "🤖 **AI Trend Hunter**: Waiting for inputs..."
    if api_key and not trend_df.empty:
        gemini = GeminiService(api_key)
        try:
            ai_trend = gemini.analyze_trends(trend_df, "Enrolment")
        except Exception as e:
            ai_trend = f"Error: {e}"
            
    return fig_pie, m_pie, fig_funnel, m_funnel, fig_trend, m_trend, fig_area, m_area, fig_scatter, m_scatter, ai_trend

def update_demo(selected_state):
    df_e, df_d, df_b = filter_data(selected_state)
    desc_analytics = DescriptiveAnalytics(df_e, df_d, df_b)
    diag_analytics = DiagnosticAnalytics(df_e, df_d, df_b)
    
    # Trend
    fig_trend = None
    if not df_d.empty:
        trend_demo = desc_analytics.get_trend_analysis('demographic')
        if not trend_demo.empty:
             trend_melt = trend_demo.melt(id_vars=[constants.COL_DATE], var_name='Age Group', value_name='Count')
             fig_trend = charts.plot_trend(trend_melt, "Demographic Updates Timeline", x_col=constants.COL_DATE, y_col='Count', color_col='Age Group')
    m_trend = get_measure_demo_trend()
        
    # Ratio Table
    ratio_df = diag_analytics.calculate_update_vs_enrolment_ratio()
    ratio_display = pd.DataFrame()
    static_analysis = "No data."
    if not ratio_df.empty:
        ratio_display = ratio_df[[constants.COL_STATE, 'update_enrolment_ratio', 'total_updates', 'total_enrolments']].head(15)
        static_analysis = analyze_demographic_anomalies(ratio_display)
    
    # Correlation
    corr_mat = diag_analytics.get_correlation_matrix()
    fig_corr = charts.plot_correlation_heatmap(corr_mat, title="Variable Correlation Heatmap") if not corr_mat.empty else None
    
    # Outliers
    outliers = diag_analytics.detect_district_outliers("enrolment")
    fig_box = charts.plot_box_distribution(outliers, constants.COL_STATE, 'total', "Outlier Detection Boxplot") if not outliers.empty else None
    m_box = get_measure_outliers()
    
    return fig_trend, m_trend, ratio_display, static_analysis, fig_corr, fig_box, m_box

def update_bio(selected_state):
    df_e, df_d, df_b = filter_data(selected_state)
    desc_analytics = DescriptiveAnalytics(df_e, df_d, df_b)
    
    fig_trend = None
    fig_bar = None
    
    if not df_b.empty:
         trend_bio = desc_analytics.get_trend_analysis('biometric')
         if not trend_bio.empty:
             trend_melt = trend_bio.melt(id_vars=[constants.COL_DATE], var_name='Age Group', value_name='Count')
             fig_trend = charts.plot_trend(trend_melt, "Biometric Updates Trend", x_col=constants.COL_DATE, y_col='Count', color_col='Age Group')
         
         if selected_state != "All":
             agg_bio = feature_engineering.aggregate_by_region(df_b, [constants.COL_BIO_AGE_5_17, constants.COL_BIO_AGE_18_PLUS])
             agg_bio['Total'] = agg_bio[constants.COL_BIO_AGE_5_17] + agg_bio[constants.COL_BIO_AGE_18_PLUS]
             fig_bar = px.bar(agg_bio.sort_values('Total', ascending=False).head(20), x=constants.COL_DISTRICT, y='Total', title=f"Top High-Traffic Districts in {selected_state}")
             fig_bar.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
         else:
             agg_bio = df_b.groupby(constants.COL_STATE)[['bio_age_5_17', 'bio_age_17_']].sum().reset_index()
             agg_bio['Total'] = agg_bio['bio_age_5_17'] + agg_bio['bio_age_17_']
             fig_bar = px.bar(agg_bio.sort_values('Total', ascending=False).head(20), x=constants.COL_STATE, y='Total', title="Top High-Traffic States for Biometrics")
             fig_bar.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    
    m_trend = get_measure_bio_trend()
    return fig_trend, m_trend, fig_bar

def update_pred(selected_state):
    df_e, df_d, df_b = filter_data(selected_state)
    pred_analytics = PredictiveAnalytics(df_e, df_b)
    
    forecast_enr = pred_analytics.forecast_enrolment_demand()
    fig_enr = charts.plot_trend(forecast_enr, "Enrolment Demand Forecast (3 Months)", x_col='date', y_col='forecast', color_col='type') if not forecast_enr.empty else None
    
    forecast_bio = pred_analytics.forecast_biometric_load()
    fig_bio = charts.plot_trend(forecast_bio, "Biometric Load Forecast (3 Months)", x_col='date', y_col='forecast', color_col='type') if not forecast_bio.empty else None
    
    analysis = """
    ### 🔮 Static Analysis & Measures
    **If Forecast > Current Capacity**: Trigger `Auto-Scale` protocols. Hire temporary operators.
    **If Forecast < Capacity**: Consolidate centers.
    """
    return fig_enr, fig_bio, analysis

def update_recs(selected_state, th_enr, th_bio, api_key):
    df_e, df_d, df_b = filter_data(selected_state)
    presc_analytics = PrescriptiveAnalytics(df_e, df_b)
    
    recs = presc_analytics.get_recommendations(threshold_enr=th_enr, threshold_bio=th_bio)
    policy_text = "Policy Draft (Enter API Key)"
    if api_key and not recs.empty:
        gemini = GeminiService(api_key)
        try:
            policy_text = gemini.recommend_policy(recs)
        except:
            policy_text = "Policy generation failed."
    
    logic_expl = f"""
    ### 🧠 Recommendation Engine Logic
    **Thresholds Applied**: Enrolment > `{th_enr}`, Biometric > `{th_bio}`.
    **Logic**: IF Load > Threshold AND Trend Rising -> **"Mobilize Van"**.
    """
    return recs, policy_text, logic_expl

# --- CSS Styling ---
custom_css = """
    /* Main Background - Deep Dark Blue */
    body, .gradio-container { 
        background-color: #0b0f19 !important; 
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    
    /* Global Text Color - White */
    .gradio-container, .prose, p, div, span, label, td, th { 
        color: #e5e7eb !important; 
    }
    
    /* Headings */
    h1, h2, h3, h4, h5, h6 { 
        color: #ffffff !important; 
        font-weight: 700;
    }

    /* Cards/Containers - Lighter Dark Blue */
    .contain { 
        background-color: #111827 !important; 
        border: 1px solid #1f2937;
        border-radius: 12px; 
        padding: 24px; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); 
        margin-bottom: 20px;
    }
    
    /* Sidebar specific */
    .gradio-sidebar {
        background-color: #111827 !important;
        border-right: 1px solid #1f2937;
    }
    
    input, textarea, select, .gr-input, .gr-box, tr, td, th {
        background-color: #1f2937 !important;
        color: white !important;
        border: 1px solid #374151 !important;
    }
    
    button.primary { 
        background: #3b82f6 !important; 
        color: white !important;
        border: none !important;
        font-weight: 600;
    }
    
    .tab-nav button { color: #9ca3af !important; }
    .tab-nav button.selected { color: #60a5fa !important; border-bottom: 2px solid #60a5fa; }
"""

# --- Layout ---
theme = gr.themes.Base(
    primary_hue="blue",
    neutral_hue="slate",
    text_size="sm",
    spacing_size="sm",
    radius_size="lg",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
).set(
    body_background_fill="#0b0f19",
    body_text_color="#e5e7eb",
    background_fill_primary="#111827", 
    background_fill_secondary="#1f2937", 
    border_color_primary="#1f2937",
    block_background_fill="#111827",
    block_label_text_color="#e5e7eb",
    block_title_text_color="#ffffff",
    input_background_fill="#1f2937",
)

with gr.Blocks(theme=theme, title="UIDAI Aadhaar Analytics 3.0", css=custom_css) as app:
    
    with gr.Sidebar(open=True, label="🎛️ Control Panel"):
        gr.Markdown("### ⚙️ Settings")
        state_input = gr.Dropdown(["All"] + all_states, label="🌍 Select Region", value="All", elem_id="state_select", interactive=True)
        api_key_input = gr.Textbox(label="🔑 Gemini API Key", type="password", placeholder="sk-...", info="For AI Insights")
        refresh_btn = gr.Button("🔄 Refresh Data", variant="primary")
        
        gr.Markdown("---")
        gr.Markdown("**System Status**: ✅ Online\n**Version**: v3.2.0")

    with gr.Column(elem_classes="contain"):
        gr.Markdown("# 🇮🇳 INDIA UIDAI Aadhaar Analytics Dashboard\n### Policy-Grade Decision Support System")

        with gr.Tabs():
            # TAB 1: OVERVIEW
            with gr.TabItem("📊 Overview"):
                with gr.Row():
                    with gr.Column(scale=2):
                        kpi_overview = gr.Markdown("Loading KPIs...")
                    with gr.Column(scale=3):
                        static_analysis_mkdn = gr.Markdown("Loading Analysis...")
                
                with gr.Column():
                    gr.Markdown("### 🎯 Update Intensity Index (Gauge)")
                    gauge_plot = gr.Plot(label="Maturity")
                    m_gauge = gr.Markdown("Loading Measure...")
                    
                    gr.Markdown("### 🚀 Operational Velocity (DEA)")
                    bullet_plot = gr.Plot(label="(DEA)")
                    m_bullet = gr.Markdown("Loading Measure...")
                
                gr.Markdown("### 🗺️ Geospatial Intelligence")
                with gr.Column():
                    gr.Markdown("### 🇮🇳 State-wise Saturation Map (Choropleth)")
                    map_plot = gr.Plot(label="Map")
                    m_map = gr.Markdown("Loading Measure...")
                    
                    gr.Markdown("### 📊 Top Volume Contributors (Bar)")
                    bar_plot = gr.Plot(label="Bar")
                    m_bar = gr.Markdown("Loading Measure...")
                    
                    gr.Markdown("### 🌳 Hierarchical Breakdown (Treemap)")
                    tree_plot = gr.Plot(label="Treemap")
                    m_tree = gr.Markdown("Loading Measure...")
                
                ai_summary = gr.Markdown("### 🤖 AI Insight: Waiting for Key...")
                
                # Auto-Load
                app.load(update_overview, [state_input, api_key_input], [kpi_overview, static_analysis_mkdn, gauge_plot, m_gauge, bullet_plot, m_bullet, bar_plot, m_bar, tree_plot, m_tree, map_plot, m_map, ai_summary])
                refresh_btn.click(update_overview, [state_input, api_key_input], [kpi_overview, static_analysis_mkdn, gauge_plot, m_gauge, bullet_plot, m_bullet, bar_plot, m_bar, tree_plot, m_tree, map_plot, m_map, ai_summary])
                state_input.change(update_overview, [state_input, api_key_input], [kpi_overview, static_analysis_mkdn, gauge_plot, m_gauge, bullet_plot, m_bullet, bar_plot, m_bar, tree_plot, m_tree, map_plot, m_map, ai_summary])

            # TAB 2: ENROLMENT
            with gr.TabItem("📝 Enrolment"):
                gr.Markdown("### Lifecycle & Growth Analytics")
                with gr.Column():
                    gr.Markdown("### 🍰 Demographic Composition (Pie)")
                    pie_plot = gr.Plot(label="Pie")
                    m_pie = gr.Markdown("Loading Measure...")
                    
                    gr.Markdown("### 🔽 Retention Funnel")
                    funnel_plot = gr.Plot(label="Funnel")
                    m_funnel = gr.Markdown("Loading Measure...")
                
                with gr.Column():
                    gr.Markdown("### 📈 Velocity Trend (Time Series)")
                    trend_plot = gr.Plot(label="Trend")
                    m_trend = gr.Markdown("Loading Measure...")
                    
                    gr.Markdown("### 🌊 Composition Shift (Stacked Area)")
                    area_plot = gr.Plot(label="Area")
                    m_area = gr.Markdown("Loading Measure...")
                
                gr.Markdown("### 💠 Growth Matrix (Scatter)")
                scatter_plot = gr.Plot(label="Scatter")
                m_scatter = gr.Markdown("Loading Measure...")
                
                ai_trend_text = gr.Markdown("Waiting...")
                
                # Auto-Load
                app.load(update_enrolment, [state_input, api_key_input], [pie_plot, m_pie, funnel_plot, m_funnel, trend_plot, m_trend, area_plot, m_area, scatter_plot, m_scatter, ai_trend_text])
                refresh_btn.click(update_enrolment, [state_input, api_key_input], [pie_plot, m_pie, funnel_plot, m_funnel, trend_plot, m_trend, area_plot, m_area, scatter_plot, m_scatter, ai_trend_text])
                state_input.change(update_enrolment, [state_input, api_key_input], [pie_plot, m_pie, funnel_plot, m_funnel, trend_plot, m_trend, area_plot, m_area, scatter_plot, m_scatter, ai_trend_text])

            # TAB 3: DEMOGRAPHIC
            with gr.TabItem("🔄 Demographic"):
                gr.Markdown("### Update Behavior & Anomalies")
                gr.Markdown("### 📉 Update Frequency Trend")
                demo_trend_plot = gr.Plot(label="Trend")
                m_trend_demo = gr.Markdown("Loading Measure...")
                
                with gr.Column():
                    gr.Markdown("### 🚨 High Pressure Zones (Table)")
                    ratio_table = gr.Dataframe(label="Table", interactive=False)
                    demo_analysis_mkdn = gr.Markdown("Loading Analysis...")
                
                with gr.Column():
                    gr.Markdown("### 🌡️ Variable Correlation (Heatmap)")
                    corr_plot = gr.Plot(label="Corr")
                    
                    gr.Markdown("### 📦 Outlier Detection (Box Plot)")
                    box_plot = gr.Plot(label="Box")
                    m_box = gr.Markdown("Loading Measure...")
                
                # Auto-Load
                app.load(update_demo, [state_input], [demo_trend_plot, m_trend_demo, ratio_table, demo_analysis_mkdn, corr_plot, box_plot, m_box])
                refresh_btn.click(update_demo, [state_input], [demo_trend_plot, m_trend_demo, ratio_table, demo_analysis_mkdn, corr_plot, box_plot, m_box])
                state_input.change(update_demo, [state_input], [demo_trend_plot, m_trend_demo, ratio_table, demo_analysis_mkdn, corr_plot, box_plot, m_box])

            # TAB 4: BIOMETRIC
            with gr.TabItem("Fingerprint/Iris"):
                gr.Markdown("### Biometric Update Tracking")
                with gr.Column():
                    gr.Markdown("### 📉 Biometric Trends")
                    bio_trend_plot = gr.Plot(label="Trend")
                    m_bio_trend = gr.Markdown("Loading Measure...")
                    
                    gr.Markdown("### 📍 Geographic Hotspots (Bar)")
                    bio_dist_plot = gr.Plot(label="Hotspots")
                
                # Auto-Load
                app.load(update_bio, [state_input], [bio_trend_plot, m_bio_trend, bio_dist_plot])
                refresh_btn.click(update_bio, [state_input], [bio_trend_plot, m_bio_trend, bio_dist_plot])
                state_input.change(update_bio, [state_input], [bio_trend_plot, m_bio_trend, bio_dist_plot])

            # TAB 5: PREDICTIONS
            with gr.TabItem("🔮 Predictions"):
                gr.Markdown("### AI-Driven Forecasts")
                with gr.Column():
                    gr.Markdown("### 🔮 Enrolment Demand Forecast (3 Months)")
                    pred_enr_plot = gr.Plot(label="Enrolment Forecast")
                    gr.Markdown("### 🔮 Biometric Load Forecast (3 Months)")
                    pred_bio_plot = gr.Plot(label="Biometric Forecast")
                pred_analysis_mkdn = gr.Markdown("### Static Analysis")
                
                app.load(update_pred, [state_input], [pred_enr_plot, pred_bio_plot, pred_analysis_mkdn])
                refresh_btn.click(update_pred, [state_input], [pred_enr_plot, pred_bio_plot, pred_analysis_mkdn])
                state_input.change(update_pred, [state_input], [pred_enr_plot, pred_bio_plot, pred_analysis_mkdn])
            
            # TAB 6: ACTIONS
            with gr.TabItem("✅ Actions"):
                gr.Markdown("### Prescriptive Intelligence Engine")
                with gr.Column():
                    with gr.Column():
                        gr.Markdown("#### 🎛️ Sensitivity Controls")
                        th_enr_sl = gr.Slider(100, 10000, value=1000, label="High Load Threshold (Enrolment)")
                        th_bio_sl = gr.Slider(100, 5000, value=500, label="High Load Threshold (Biometric)")
                    with gr.Column():
                        rec_logic_mkdn = gr.Markdown("Loading Logic...")
                with gr.Column():
                    recs_table = gr.Dataframe(label="Action Zones")
                    policy_output = gr.Textbox(label="Draft Directive", lines=15)
                rec_btn = gr.Button("🚀 Generate Action Plan", variant="primary")
                rec_btn.click(update_recs, [state_input, th_enr_sl, th_bio_sl, api_key_input], [recs_table, policy_output, rec_logic_mkdn])

if __name__ == "__main__":
    app.launch()
