
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_RAW = os.path.join(BASE_DIR, "aadhaar_analytics", "data", "raw")
DATA_PROCESSED = os.path.join(BASE_DIR, "aadhaar_analytics", "data", "processed")

# Column Names (Standardized)
COL_DATE = 'date'
COL_STATE = 'state'
COL_DISTRICT = 'district'
COL_PINCODE = 'pincode'

# Enrolment Columns
COL_ENR_AGE_0_5 = 'age_0_5'
COL_ENR_AGE_5_17 = 'age_5_17'
COL_ENR_AGE_18_PLUS = 'age_18_greater'

# Demographic Update Columns
COL_DEMO_AGE_5_17 = 'demo_age_5_17'
COL_DEMO_AGE_18_PLUS = 'demo_age_17_' # Inferred from "demo_age_17_"

# Biometric Update Columns
COL_BIO_AGE_5_17 = 'bio_age_5_17'
COL_BIO_AGE_18_PLUS = 'bio_age_17_'   # Inferred from "bio_age_17_"

# Mapping folder names to dataset types
DATASET_TYPES = {
    'enrolment': 'api_data_aadhar_enrolment',
    'demographic': 'api_data_aadhar_demographic',
    'biometric': 'api_data_aadhar_biometric'
}
