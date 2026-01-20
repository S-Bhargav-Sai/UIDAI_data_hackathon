import pandas as pd
import glob
import os

# Paths
biometric_path = 'c:/Users/Dell/data_hackathon/api_data_aadhar_biometric'
demographic_path = 'c:/Users/Dell/data_hackathon/api_data_aadhar_demographic'
enrolment_path = 'c:/Users/Dell/data_hackathon/api_data_aadhar_enrolment'

def load_and_merge(path, name):
    print(f"\n--- Loading {name} ---")
    files = glob.glob(os.path.join(path, '*.csv'))
    print(f"Found {len(files)} files in {path}")
    dfs = []
    for f in files:
        try:
            print(f"Reading {os.path.basename(f)}...")
            df = pd.read_csv(f)
            dfs.append(df)
        except Exception as e:
            print(f"Error reading {f}: {e}")
    
    if dfs:
        full_df = pd.concat(dfs, ignore_index=True)
        print(f"Merged {name} shape: {full_df.shape}")
        print(f"Columns: {list(full_df.columns)}")
        print("Head:")
        print(full_df.head())
        print("Info:")
        print(full_df.info())
        return full_df
    else:
        print(f"No data for {name}")
        return None

# Load Datasets
bio_df = load_and_merge(biometric_path, "Biometric Updates")
demo_df = load_and_merge(demographic_path, "Demographic Updates")
enrol_df = load_and_merge(enrolment_path, "Enrolments")
