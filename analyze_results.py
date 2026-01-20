import pandas as pd
import glob
import os

pd.options.display.float_format = '{:.2f}'.format

# Paths
BIO_PATH = 'c:/Users/Dell/data_hackathon/api_data_aadhar_biometric'
DEMO_PATH = 'c:/Users/Dell/data_hackathon/api_data_aadhar_demographic'
ENROL_PATH = 'c:/Users/Dell/data_hackathon/api_data_aadhar_enrolment'

def load_data(path, pattern='*.csv'):
    files = glob.glob(os.path.join(path, pattern))
    if not files: return pd.DataFrame()
    dfs = [pd.read_csv(f) for f in files]
    return pd.concat(dfs, ignore_index=True)

def preprocess(df):
    df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
    df['state'] = df['state'].astype(str).str.strip().str.title()
    state_corrections = {
        'Westbengal': 'West Bengal',
        'West Bangal': 'West Bengal',
        'West  Bengal': 'West Bengal',
        'Daman & Diu': 'Daman And Diu',
        'Dadra & Nagar Haveli': 'Dadra And Nagar Haveli',
        'Jammu & Kashmir': 'Jammu And Kashmir',
        'Andaman & Nicobar Islands': 'Andaman And Nicobar Islands'
    }
    df['state'] = df['state'].replace(state_corrections)
    return df.dropna(subset=['date'])

print("Loading and Processing...")
bio_df = preprocess(load_data(BIO_PATH))
demo_df = preprocess(load_data(DEMO_PATH))
enrol_df = preprocess(load_data(ENROL_PATH))

bio_df['Total'] = bio_df['bio_age_5_17'] + bio_df['bio_age_17_']
demo_df['Total'] = demo_df['demo_age_5_17'] + demo_df['demo_age_17_']
enrol_df['Total'] = enrol_df['age_0_5'] + enrol_df['age_5_17'] + enrol_df['age_18_greater']

print("\n--- INSIGHTS ---")

# 1. Total Volume
print(f"Total Enrolments: {enrol_df['Total'].sum():,}")
print(f"Total Demo Updates: {demo_df['Total'].sum():,}")
print(f"Total Bio Updates: {bio_df['Total'].sum():,}")

# 2. Top States
print("\nTop 5 States (Enrolment):")
print(enrol_df.groupby('state')['Total'].sum().sort_values(ascending=False).head(5))

print("\nTop 5 States (Updates - Demo):")
print(demo_df.groupby('state')['Total'].sum().sort_values(ascending=False).head(5))

# 3. Monthly Trend (Peak Month)
enrol_df['Month'] = enrol_df['date'].dt.to_period('M')
monthly_enrol = enrol_df.groupby('Month')['Total'].sum()
print("\nPeak Enrolment Month:")
print(monthly_enrol.idxmax(), monthly_enrol.max())

# 4. Age Split
print("\nEnrolment Age Split:")
print(enrol_df[['age_0_5', 'age_5_17', 'age_18_greater']].sum())

# 5. Low Enrolment States (Bottom 5)
print("\nBottom 5 States (Enrolment):")
print(enrol_df.groupby('state')['Total'].sum().sort_values().head(5))
