
import os
import glob
import pandas as pd
from aadhaar_analytics.utils import constants
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_all_csv_files(directory):
    """Recursively find all CSV files in a directory."""
    return [y for x in os.walk(directory) for y in glob.glob(os.path.join(x[0], '*.csv'))]

def load_dataset(dataset_type):
    """
    Loads all CSVs for a given dataset type (enrolment, demographic, biometric).
    Returns a merged DataFrame.
    """
    folder_name = constants.DATASET_TYPES.get(dataset_type)
    if not folder_name:
        raise ValueError(f"Unknown dataset type: {dataset_type}")

    # Search in BASE_DIR
    search_path = os.path.join(constants.BASE_DIR, folder_name)
    
    if not os.path.exists(search_path):
        logger.error(f"Directory not found: {search_path}")
        return pd.DataFrame() # Return empty if not found

    csv_files = get_all_csv_files(search_path)
    if not csv_files:
        logger.warning(f"No CSV files found in {search_path}")
        return pd.DataFrame()

    logger.info(f"Found {len(csv_files)} files for {dataset_type}...")
    
    dfs = []
    for f in csv_files:
        try:
            # Read CSV
            df = pd.read_csv(f)
            # Normalize Columns: strip whitespace, lowercase
            df.columns = [c.strip().lower() for c in df.columns]
            dfs.append(df)
        except Exception as e:
            logger.error(f"Error reading file {f}: {e}")

    if not dfs:
        return pd.DataFrame()

    final_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded {dataset_type} dataset with {len(final_df)} rows.")
    return final_df

def load_all_datasets():
    """Loads all three datasets."""
    data = {}
    for key in constants.DATASET_TYPES.keys():
        data[key] = load_dataset(key)
    return data
