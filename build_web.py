
import os
import json
import shutil
import pandas as pd
import sys
import numpy as np
import logging
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from aadhaar_analytics.ingestion import loader
from aadhaar_analytics.preprocessing import cleaning, feature_engineering
from aadhaar_analytics.analytics.descriptive import DescriptiveAnalytics
from aadhaar_analytics.analytics.diagnostic import DiagnosticAnalytics
from aadhaar_analytics.analytics.predictive import PredictiveAnalytics
from aadhaar_analytics.analytics.prescriptive import PrescriptiveAnalytics
from aadhaar_analytics.ai.gemini_service import GeminiService
from aadhaar_analytics.utils import constants

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BUILD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

# Try to load API Key from env
try:
    from dotenv import load_dotenv
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
except:
    GEMINI_API_KEY = None

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

def get_ai_service():
    if GEMINI_API_KEY:
        return GeminiService(GEMINI_API_KEY)
    return None

def build():
    start_time = time.time()
    
    # 1. Setup Build Dir
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)

    # 2. Data Loading
    logger.info("Loading Datasets...")
    raw_data = loader.load_all_datasets()
    
    data = {}
    for dtype in ['enrolment', 'demographic', 'biometric']:
        df = raw_data.get(dtype, pd.DataFrame())
        if not df.empty:
            df = cleaning.clean_dataframe(df, dtype)
            df = feature_engineering.add_time_features(df)
            # Optimize size: Convert object cols to categories if possible, or just keep needed cols
            # For JSON export, we want Aggregates, not raw rows usually.
        data[dtype] = df

    df_enr = data['enrolment']
    df_demo = data['demographic']
    df_bio = data['biometric']

    # 3. Analytics Engines
    desc = DescriptiveAnalytics(df_enr, df_demo, df_bio)
    diag = DiagnosticAnalytics(df_enr, df_demo, df_bio)
    pred = PredictiveAnalytics(df_enr, df_bio)
    presc = PrescriptiveAnalytics(df_enr, df_bio)
    
    # Init AI
    ai = get_ai_service()
    
    # 4. Generate Data Structure
    # We will export a Structure that supports Filtering by 'state'.
    # Structure:
    # {
    #    "filter_options": { "states": [...] },
    #    "metrics": [ { "state": "All", "kpis": {...}, "trends": {...} }, { "state": "XY", ... } ]
    # }
    # To optimize, we won't dump ALL states fully unless needed. 
    # Let's dump "All" + Top 5 States fully. For others, we might rely on a 'lite' version or client-side aggregation.
    # ACTUALLY: Client-side aggregation is best if data isn't huge.
    # Let's check size. If million rows, client is bad.
    # A better approach for Static Site: Pre-calculate per-state aggregates.
    
    logger.info("Computing Aggregates...")
    
    dataset = {
        "metadata": {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "states": ["All"] + sorted(df_enr[constants.COL_STATE].dropna().unique().tolist()) if not df_enr.empty else []
        },
        "stats": {} # Keyed by state
    }

    # Helper to compute stats for a specific state view
    def compute_view(state_name, df_e, df_d, df_b):
        # Filter (if not All)
        if state_name != "All":
            d_e = df_e[df_e[constants.COL_STATE] == state_name] if not df_e.empty else df_e
            d_d = df_d[df_d[constants.COL_STATE] == state_name] if not df_d.empty else df_d
            d_b = df_b[df_b[constants.COL_STATE] == state_name] if not df_b.empty else df_b
        else:
            d_e, d_d, d_b = df_e, df_d, df_b
            
        view_data = {}
        
        # 1. KPI
        view_data['kpis'] = feature_engineering.calculate_kpis(d_e, d_d, d_b)
        
        # 2. Trends (Enrolment)
        try:
            # Descriptive Analytics expects the full DF and does groupby internally
            # We must instantiate a new engine or manually group.
            # Manual grouping is faster/cleaner here.
            if not d_e.empty:
                # Group by Date and Sum Age columns
                # We need Age 0-5, 5-17, 18+
                cols = [constants.COL_ENR_AGE_0_5, constants.COL_ENR_AGE_5_17, constants.COL_ENR_AGE_18_PLUS]
                trend = d_e.groupby(constants.COL_DATE)[cols].sum().reset_index()
                trend[constants.COL_DATE] = trend[constants.COL_DATE].astype(str)
                view_data['trend_enrolment'] = trend.to_dict(orient='records')
                
                # Age Distribution (Pie)
                age_dist = d_e[cols].sum().to_dict()
                view_data['age_distribution'] = age_dist
                
                # Funnel (Same as Age Dist basically)
                view_data['funnel'] = age_dist
        except Exception as e:
            logger.error(f"Trend error {state_name}: {e}")

        # 3. Trends (Updates)
        try:
            if not d_d.empty:
               cols_d = [constants.COL_DEMO_AGE_5_17, constants.COL_DEMO_AGE_18_PLUS]
               # Ensure cols exist
               valid_cols = [c for c in cols_d if c in d_d.columns]
               if valid_cols:
                   trend_d = d_d.groupby(constants.COL_DATE)[valid_cols].sum().reset_index()
                   trend_d[constants.COL_DATE] = trend_d[constants.COL_DATE].astype(str)
                   view_data['trend_demo'] = trend_d.to_dict(orient='records')
        except: pass
        
        try:
           if not d_b.empty:
               cols_b = [constants.COL_BIO_AGE_5_17, constants.COL_BIO_AGE_18_PLUS]
               valid_cols_b = [c for c in cols_b if c in d_b.columns]
               if valid_cols_b:
                   trend_b = d_b.groupby(constants.COL_DATE)[valid_cols_b].sum().reset_index()
                   trend_b[constants.COL_DATE] = trend_b[constants.COL_DATE].astype(str)
                   view_data['trend_bio'] = trend_b.to_dict(orient='records')
        except: pass

        # 4. Forecasting (Only for National to save build time, or top states)
        # If State == All, do forecast
        if state_name == "All" and not d_e.empty:
            try:
                # Need to use the Class
                local_pred = PredictiveAnalytics(d_e, d_b)
                fc_enr = local_pred.forecast_enrolment_demand()
                if not fc_enr.empty:
                    fc_enr['date'] = fc_enr['date'].astype(str)
                    view_data['forecast_enrolment'] = fc_enr.to_dict(orient='records')
                
                fc_bio = local_pred.forecast_biometric_load()
                if not fc_bio.empty:
                    fc_bio['date'] = fc_bio['date'].astype(str)
                    view_data['forecast_bio'] = fc_bio.to_dict(orient='records')
            except Exception as e:
                logger.error(f"Forecast error: {e}")

        # 5. Outliers / Diagnostic (Only for All, decomposed by State)
        if state_name == "All":
             # State performance Bar
             try:
                 summ = d_e.groupby(constants.COL_STATE)[[constants.COL_ENR_AGE_0_5, constants.COL_ENR_AGE_5_17, constants.COL_ENR_AGE_18_PLUS]].sum()
                 summ['Total'] = summ.sum(axis=1)
                 view_data['state_performance'] = summ.sort_values('Total', ascending=False).head(10).reset_index().to_dict(orient='records')
                 
                 # Treemap Data (State -> District)
                 # Too big to send all? Send Top 50 Districts.
                 tree = d_e.groupby([constants.COL_STATE, constants.COL_DISTRICT])['age_0_5'].sum().reset_index(name='val') # utilizing one col for size proxy
                 # Actually utilize total
                 d_e['Total_Enr'] = d_e[constants.COL_ENR_AGE_0_5] + d_e[constants.COL_ENR_AGE_5_17] + d_e[constants.COL_ENR_AGE_18_PLUS]
                 tree = d_e.groupby([constants.COL_STATE, constants.COL_DISTRICT])['Total_Enr'].sum().reset_index(name='Total')
                 view_data['treemap'] = tree.nlargest(200, 'Total').to_dict(orient='records')
                 
                 # Map Data (State level total)
                 map_d = d_e.groupby(constants.COL_STATE)['Total_Enr'].sum().reset_index()
                 view_data['map_data'] = map_d.to_dict(orient='records')
                 
                 # Recommendations
                 rec_df = presc.get_recommendations()
                 view_data['recommendations'] = rec_df.head(50).to_dict(orient='records') if not rec_df.empty else []
                 
             except Exception as e:
                 logger.error(f"Diag error: {e}")

        # 6. AI Insights (Only for All to save API, or handle efficiently)
        if state_name == "All" and ai:
            view_data['ai'] = {}
            try:
                view_data['ai']['kpi_summary'] = ai.explain_kpis(view_data['kpis'], state_name)
            except: view_data['ai']['kpi_summary'] = "AI Unavailable"
            
            try:
                # Use simplified DF for prompt
                if 'trend_enrolment' in view_data:
                    df_t = pd.DataFrame(view_data['trend_enrolment'])
                    view_data['ai']['trend_analysis'] = ai.analyze_trends(df_t)
            except: pass
            
            try:
                 if 'recommendations' in view_data and view_data['recommendations']:
                     rec_df_ai = pd.DataFrame(view_data['recommendations'])
                     view_data['ai']['policy_draft'] = ai.recommend_policy(rec_df_ai)
            except: pass
            
        return view_data

    # Generate "All" view
    logger.info("Generating National View...")
    dataset['stats']['All'] = compute_view("All", df_enr, df_demo, df_bio)

    # Generate Individual State views (Lite version)
    # We will limit to Top 15 States to ensure build finishes within reasonable time
    all_states = dataset['metadata']['states']
    if 'All' in all_states: all_states.remove('All')
    
    # Sort states by enrolment volume if possible to pick top ones
    # We can use the 'state_performance' metric calculated for All view
    try:
        top_states = [x['state'] for x in dataset['stats']['All']['state_performance']]
        # Add remaining if any, up to limit
        priority_states = top_states + [s for s in all_states if s not in top_states]
        # Slice
        states_to_process = priority_states[:15]
    except:
        states_to_process = all_states[:10] # Fallback
        
    logger.info(f"Processing {len(states_to_process)} priority states...")

    for st in states_to_process:
        # logger.info(f"Generating view for {st}...") 
        dataset['stats'][st] = compute_view(st, df_enr, df_demo, df_bio)

    # 5. Write JSON
    logger.info(f"Saving data.json to {BUILD_DIR}...")
    with open(os.path.join(BUILD_DIR, "data.json"), "w", encoding='utf-8') as f:
        json.dump(dataset, f, cls=NpEncoder)

    # 6. Copy Web Assets
    src_web = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
    if os.path.exists(src_web):
        for item in os.listdir(src_web):
            s = os.path.join(src_web, item)
            d = os.path.join(BUILD_DIR, item)
            if os.path.isdir(s):
                if os.path.exists(d): shutil.rmtree(d) # Clean replace
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
                
    logger.info(f"Build Finished in {time.time() - start_time:.2f}s")
    print("Build Complete.")

if __name__ == "__main__":
    build()
