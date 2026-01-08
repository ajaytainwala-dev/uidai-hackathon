
import pandas as pd
from aadhaar_analytics.utils import constants

class PrescriptiveAnalytics:
    def __init__(self, df_enr, df_bio):
        self.df_enr = df_enr
        self.df_bio = df_bio

    def get_recommendations(self, threshold_enr=1000, threshold_bio=500):
        """
        Identify high-pressure districts.
        Rule: If Enrolment > threshold -> "Deploy Mobile Van"
        Rule: If Bio Updates > threshold -> "Open Special Camp"
        """
        recommendations = []
        
        # 1. High Enrolment Load
        if not self.df_enr.empty:
            df = self.df_enr.copy()
            df['total'] = df[constants.COL_ENR_AGE_0_5] + df[constants.COL_ENR_AGE_5_17] + df[constants.COL_ENR_AGE_18_PLUS]
            # Group by District (mean monthly load or total)
            # Assuming data is monthly, let's take average monthly load per district
            load = df.groupby([constants.COL_STATE, constants.COL_DISTRICT])['total'].mean().reset_index()
            
            high_load = load[load['total'] > threshold_enr]
            for _, row in high_load.iterrows():
                recommendations.append({
                    'State': row[constants.COL_STATE],
                    'District': row[constants.COL_DISTRICT],
                    'Issue': f"High Enrolment Load (Avg {int(row['total'])}/month)",
                    'Action': 'Deploy Mobile Aadhaar Van',
                    'Priority': 'High'
                })

        # 2. High Biometric Update Load
        if not self.df_bio.empty:
            df = self.df_bio.copy()
            df['total'] = df[constants.COL_BIO_AGE_5_17] + df[constants.COL_BIO_AGE_18_PLUS]
            load = df.groupby([constants.COL_STATE, constants.COL_DISTRICT])['total'].mean().reset_index()
            
            high_bio = load[load['total'] > threshold_bio]
            for _, row in high_bio.iterrows():
                recommendations.append({
                    'State': row[constants.COL_STATE],
                    'District': row[constants.COL_DISTRICT],
                    'Issue': f"High Biometric Update Load (Avg {int(row['total'])}/month)",
                    'Action': 'Schedule Special Biometric Camp for Children',
                    'Priority': 'Medium'
                })

        return pd.DataFrame(recommendations)
