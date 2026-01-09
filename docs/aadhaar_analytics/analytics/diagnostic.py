
import pandas as pd
import numpy as np
from aadhaar_analytics.utils import constants

class DiagnosticAnalytics:
    def __init__(self, df_enr, df_demo, df_bio):
        self.df_enr = df_enr
        self.df_demo = df_demo
        self.df_bio = df_bio

    def calculate_update_vs_enrolment_ratio(self):
        """Calculates ratio of total updates (demo+bio) to enrolments per state."""
        if self.df_enr.empty or (self.df_demo.empty and self.df_bio.empty):
            return pd.DataFrame()

        # Enrolment Total per State
        enr_cols = [constants.COL_ENR_AGE_0_5, constants.COL_ENR_AGE_5_17, constants.COL_ENR_AGE_18_PLUS]
        enr_agg = self.df_enr.groupby(constants.COL_STATE)[enr_cols].sum().sum(axis=1).reset_index(name='total_enrolments')

        # Demo Total
        demo_cols = [constants.COL_DEMO_AGE_5_17, constants.COL_DEMO_AGE_18_PLUS]
        demo_agg = pd.DataFrame()
        if not self.df_demo.empty:
            demo_agg = self.df_demo.groupby(constants.COL_STATE)[demo_cols].sum().sum(axis=1).reset_index(name='total_demo')
        
        # Bio Total
        bio_cols = [constants.COL_BIO_AGE_5_17, constants.COL_BIO_AGE_18_PLUS]
        bio_agg = pd.DataFrame()
        if not self.df_bio.empty:
            bio_agg = self.df_bio.groupby(constants.COL_STATE)[bio_cols].sum().sum(axis=1).reset_index(name='total_bio')

        # Merge
        merged = enr_agg
        if not demo_agg.empty:
            merged = pd.merge(merged, demo_agg, on=constants.COL_STATE, how='outer').fillna(0)
        else:
            merged['total_demo'] = 0
            
        if not bio_agg.empty:
            merged = pd.merge(merged, bio_agg, on=constants.COL_STATE, how='outer').fillna(0)
        else:
            merged['total_bio'] = 0

        merged['total_updates'] = merged['total_demo'] + merged['total_bio']
        
        # Avoid division by zero
        merged['update_enrolment_ratio'] = merged.apply(
            lambda x: x['total_updates'] / x['total_enrolments'] if x['total_enrolments'] > 0 else 0, axis=1
        )
        
        return merged.sort_values('update_enrolment_ratio', ascending=False)

    def get_correlation_matrix(self):
        """Calculates correlation between Enrolments, Demographic Updates, and Biometric Updates over time."""
        # We need to aggregate by date across all datasets
        
        data_frames = []
        
        if not self.df_enr.empty:
            enr = self.df_enr.groupby(constants.COL_DATE)[[constants.COL_ENR_AGE_0_5, constants.COL_ENR_AGE_5_17, constants.COL_ENR_AGE_18_PLUS]].sum().sum(axis=1).rename('Enrolments')
            data_frames.append(enr)
            
        if not self.df_demo.empty:
            demo = self.df_demo.groupby(constants.COL_DATE)[[constants.COL_DEMO_AGE_5_17, constants.COL_DEMO_AGE_18_PLUS]].sum().sum(axis=1).rename('Demographic Updates')
            data_frames.append(demo)
            
        if not self.df_bio.empty:
            bio = self.df_bio.groupby(constants.COL_DATE)[[constants.COL_BIO_AGE_5_17, constants.COL_BIO_AGE_18_PLUS]].sum().sum(axis=1).rename('Biometric Updates')
            data_frames.append(bio)
            
        if not data_frames:
            return pd.DataFrame()
            
        combined = pd.concat(data_frames, axis=1).fillna(0)
        return combined.corr()

    def detect_district_outliers(self, dataset_type='enrolment'):
        """
        Detects outliers in district performance using IQR (Inter-Quartile Range).
        Returns a DataFrame of anomalous districts.
        """
        df = None
        target_col = 'total'
        
        if dataset_type == 'enrolment':
            df = self.df_enr.copy()
            cols = [constants.COL_ENR_AGE_0_5, constants.COL_ENR_AGE_5_17, constants.COL_ENR_AGE_18_PLUS]
        elif dataset_type == 'biometric':
            df = self.df_bio.copy()
            cols = [constants.COL_BIO_AGE_5_17, constants.COL_BIO_AGE_18_PLUS]
        else:
            return pd.DataFrame()
            
        if df.empty:
            return pd.DataFrame()
            
        df[target_col] = df[cols].sum(axis=1)
        
        # Group by District Aggregates (Sum over time)
        dist_agg = df.groupby([constants.COL_STATE, constants.COL_DISTRICT])[target_col].mean().reset_index()
        
        # Calculate IQR
        Q1 = dist_agg[target_col].quantile(0.25)
        Q3 = dist_agg[target_col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = dist_agg[(dist_agg[target_col] < lower_bound) | (dist_agg[target_col] > upper_bound)]
        outliers['status'] = outliers[target_col].apply(lambda x: 'High Outlier' if x > upper_bound else 'Low Outlier')
        
        return outliers.sort_values(target_col, ascending=False)
