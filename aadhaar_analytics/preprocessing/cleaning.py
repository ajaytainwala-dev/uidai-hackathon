
import pandas as pd
from aadhaar_analytics.utils import constants

def clean_dataframe(df, dataset_type):
    """
    Applies standard cleaning operations:
    - Convert date to datetime
    - Ensure numeric columns are numeric (handling errors)
    - Fill missing values
    """
    if df.empty:
        return df

    # 1. Date Conversion
    if constants.COL_DATE in df.columns:
        # Format seems to be DD-MM-YYYY based on '31-12-2025'
        df[constants.COL_DATE] = pd.to_datetime(df[constants.COL_DATE], format='%d-%m-%Y', errors='coerce')

    # 2. Pincode to String/Category (preserve leading zeros if any, though Indian pincodes are 6 digits)
    if constants.COL_PINCODE in df.columns:
        df[constants.COL_PINCODE] = df[constants.COL_PINCODE].astype(str).str.replace(r'\.0$', '', regex=True)

    # 3. Handle Numeric Columns based on dataset type
    if dataset_type == 'enrolment':
        cols = [constants.COL_ENR_AGE_0_5, constants.COL_ENR_AGE_5_17, constants.COL_ENR_AGE_18_PLUS]
    elif dataset_type == 'demographic':
        cols = [constants.COL_DEMO_AGE_5_17, constants.COL_DEMO_AGE_18_PLUS]
    elif dataset_type == 'biometric':
        cols = [constants.COL_BIO_AGE_5_17, constants.COL_BIO_AGE_18_PLUS]
    else:
        cols = []

    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)

    # 4. Normalize State/District strings & Optimize Memory
    if constants.COL_STATE in df.columns:
        df[constants.COL_STATE] = df[constants.COL_STATE].astype(str).str.title().str.strip().astype('category')
    if constants.COL_DISTRICT in df.columns:
        df[constants.COL_DISTRICT] = df[constants.COL_DISTRICT].astype(str).str.title().str.strip().astype('category')
        
    # Drop rows where date is NaT if Date is critical (it is)
    df = df.dropna(subset=[constants.COL_DATE])

    return df
