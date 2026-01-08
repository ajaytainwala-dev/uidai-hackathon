
import pandas as pd
from aadhaar_analytics.utils import constants

class DescriptiveAnalytics:
    def __init__(self, df_enr, df_demo, df_bio):
        self.df_enr = df_enr
        self.df_demo = df_demo
        self.df_bio = df_bio

    def get_state_wise_summary(self, dataset_type='enrolment'):
        """Returns aggregated metrics by State."""
        if dataset_type == 'enrolment':
            df = self.df_enr
            cols = [constants.COL_ENR_AGE_0_5, constants.COL_ENR_AGE_5_17, constants.COL_ENR_AGE_18_PLUS]
        elif dataset_type == 'demographic':
            df = self.df_demo
            cols = [constants.COL_DEMO_AGE_5_17, constants.COL_DEMO_AGE_18_PLUS]
        elif dataset_type == 'biometric':
            df = self.df_bio
            cols = [constants.COL_BIO_AGE_5_17, constants.COL_BIO_AGE_18_PLUS]
        else:
            return pd.DataFrame()

        if df.empty:
            return pd.DataFrame()

        return df.groupby(constants.COL_STATE)[cols].sum().reset_index()

    def get_trend_analysis(self, dataset_type='enrolment', freq='ME'):
        """Returns time-series trend."""
        if dataset_type == 'enrolment':
            df = self.df_enr
            cols = [constants.COL_ENR_AGE_0_5, constants.COL_ENR_AGE_5_17, constants.COL_ENR_AGE_18_PLUS]
        elif dataset_type == 'demographic':
            df = self.df_demo
            cols = [constants.COL_DEMO_AGE_5_17, constants.COL_DEMO_AGE_18_PLUS]
        elif dataset_type == 'biometric':
            df = self.df_bio
            cols = [constants.COL_BIO_AGE_5_17, constants.COL_BIO_AGE_18_PLUS]
        else:
            return pd.DataFrame()

        if df.empty:
            return pd.DataFrame()
            
        # Group by Date (resampled)
        # using set_index for resampling
        temp = df.set_index(constants.COL_DATE)
        resampled = temp[cols].resample(freq).sum()
        return resampled.reset_index()
