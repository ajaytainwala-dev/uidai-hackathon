
import pandas as pd
from aadhaar_analytics.utils import constants

def add_time_features(df):
    """Adds Month, Year, YearMonth columns."""
    if df.empty or constants.COL_DATE not in df.columns:
        return df
    
    df['year'] = df[constants.COL_DATE].dt.year
    df['month'] = df[constants.COL_DATE].dt.month
    df['month_name'] = df[constants.COL_DATE].dt.month_name()
    # String sortable format
    df['year_month'] = df[constants.COL_DATE].dt.to_period('M').astype(str)
    
    return df

def aggregate_by_region(df, metrics):
    """Aggregates data by State and District."""
    if df.empty:
        return pd.DataFrame()
    
    return df.groupby([constants.COL_STATE, constants.COL_DISTRICT])[metrics].sum().reset_index()

def calculate_kpis(df_enr, df_demo, df_bio):
    """Calculates high-level KPIs."""
    kpis = {}
    
    # Enrolment Total
    if not df_enr.empty:
        kpis['total_enrolments'] = (
            df_enr[constants.COL_ENR_AGE_0_5].sum() +
            df_enr[constants.COL_ENR_AGE_5_17].sum() +
            df_enr[constants.COL_ENR_AGE_18_PLUS].sum()
        )
    else:
        kpis['total_enrolments'] = 0

    # Demo Updates Total
    if not df_demo.empty:
        kpis['total_demo_updates'] = (
            df_demo[constants.COL_DEMO_AGE_5_17].sum() + 
            df_demo[constants.COL_DEMO_AGE_18_PLUS].sum()
        )
    else:
        kpis['total_demo_updates'] = 0

    # Bio Updates Total
    if not df_bio.empty:
        kpis['total_bio_updates'] = (
            df_bio[constants.COL_BIO_AGE_5_17].sum() + 
            df_bio[constants.COL_BIO_AGE_18_PLUS].sum()
        )
    else:
        kpis['total_bio_updates'] = 0
        
    return kpis
