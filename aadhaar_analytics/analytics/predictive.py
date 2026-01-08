
import pandas as pd
import numpy as np
from aadhaar_analytics.utils import constants

class PredictiveAnalytics:
    def __init__(self, df_enr, df_bio):
        self.df_enr = df_enr
        self.df_bio = df_bio

    def forecast_enrolment_demand(self, periods=3):
        """
        Simple Moving Average + Linear Trend forecast for next `periods` months.
        Returns DataFrame with actuals and forecast.
        """
        if self.df_enr.empty:
            return pd.DataFrame()

        # Aggregating total enrolments by month
        df = self.df_enr.copy()
        df['total'] = df[constants.COL_ENR_AGE_0_5] + df[constants.COL_ENR_AGE_5_17] + df[constants.COL_ENR_AGE_18_PLUS]
        
        # Resample to Monthly
        if constants.COL_DATE not in df.columns:
            # Assumes index is datetime if col missing, else return empty
            return pd.DataFrame()

        ts = df.set_index(constants.COL_DATE)['total'].resample('ME').sum()
        
        if len(ts) < 2:
            return pd.DataFrame() # Not enough data
            
        # Simple Linear Regression (y = mx + c)
        x = np.arange(len(ts))
        y = ts.values
        
        # Fit
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        
        # Forecast
        future_x = np.arange(len(ts), len(ts) + periods)
        forecast_y = p(future_x)
        
        # Create result DF
        last_date = ts.index[-1]
        future_dates = pd.date_range(start=last_date, periods=periods+1, freq='ME')[1:]
        
        forecast_df = pd.DataFrame({
            'date': future_dates,
            'forecast': forecast_y,
            'type': 'Forecast'
        })
        
        history_df = pd.DataFrame({
            'date': ts.index,
            'forecast': ts.values,
            'type': 'Actual'
        })
        
        return pd.concat([history_df, forecast_df], ignore_index=True)

    def forecast_biometric_load(self, periods=3):
        """Forecast for Biometric Updates."""
        if self.df_bio.empty:
            return pd.DataFrame()

        df = self.df_bio.copy()
        df['total'] = df[constants.COL_BIO_AGE_5_17] + df[constants.COL_BIO_AGE_18_PLUS]
        
        ts = df.set_index(constants.COL_DATE)['total'].resample('ME').sum()
        
        if len(ts) < 2:
            return pd.DataFrame()
            
        x = np.arange(len(ts))
        y = ts.values
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        
        future_x = np.arange(len(ts), len(ts) + periods)
        forecast_y = p(future_x)
        
        last_date = ts.index[-1]
        future_dates = pd.date_range(start=last_date, periods=periods+1, freq='ME')[1:]
        
        forecast_df = pd.DataFrame({
            'date': future_dates,
            'forecast': forecast_y,
            'type': 'Forecast'
        })
        
        history_df = pd.DataFrame({
            'date': ts.index,
            'forecast': ts.values,
            'type': 'Actual'
        })
        
        return pd.concat([history_df, forecast_df], ignore_index=True)
