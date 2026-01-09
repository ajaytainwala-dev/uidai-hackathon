
import sys
import os
import pandas as pd

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from aadhaar_analytics.utils import constants
from aadhaar_analytics.ingestion import loader
from aadhaar_analytics.preprocessing import cleaning

print(f"DEBUG: Constants BASE_DIR: {constants.BASE_DIR}")
print(f"DEBUG: Script Location: {os.path.abspath(__file__)}")

def test_load(dtype):
    print(f"\n--- Testing {dtype} ---")
    folder = constants.DATASET_TYPES.get(dtype)
    path = os.path.join(constants.BASE_DIR, folder)
    print(f"Expected Path: {path}")
    print(f"Path Exists: {os.path.exists(path)}")
    
    if os.path.exists(path):
        files = loader.get_all_csv_files(path)
        print(f"Files found: {len(files)}")
        if len(files) > 0:
            print(f"First file: {files[0]}")
    
    df = loader.load_dataset(dtype)
    print(f"Loaded DF Shape: {df.shape}")
    
    if not df.empty:
        print("Columns:", df.columns.tolist())
        print("Head (Raw):")
        print(df.head(2))
        
        # Test Cleaning
        print("Cleaning...")
        df_clean = cleaning.clean_dataframe(df.copy(), dtype)
        print(f"Cleaned DF Shape: {df_clean.shape}")
        if df_clean.empty:
            print("WARNING: DataFrame became empty after cleaning!")
            # Check date parsing
            if 'date' in df.columns:
                 print("Date conversion check:")
                 dates = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
                 print(f"NaT count: {dates.isna().sum()}")
                 print(dates.head())

test_load('enrolment')
