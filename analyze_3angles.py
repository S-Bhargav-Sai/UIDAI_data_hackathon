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

def clean(df, date_col='date'):
    # 1. Normalize String
    df['state'] = df['state'].astype(str).str.strip().str.title()
    df['district'] = df['district'].astype(str).str.strip().str.title()
    
    # 2. Filter Invalid Garbage (Numbers, Codes)
    garbage_filter = (
        df['state'].str.match(r'^\d+$') | 
        (df['state'] == '1000000') | 
        df['district'].str.match(r'^\d+$')
    )
    if garbage_filter.sum() > 0:
        print(f"Dropped {garbage_filter.sum()} rows with invalid state/district (e.g. '1000000')")
    df = df[~garbage_filter]

    state_corrections = {
        'Westbengal': 'West Bengal', 'West Bangal': 'West Bengal', 'West  Bengal': 'West Bengal',
        'Daman & Diu': 'Daman And Diu', 'Dadra & Nagar Haveli': 'Dadra And Nagar Haveli',
        'Jammu & Kashmir': 'Jammu And Kashmir', 'Andaman & Nicobar Islands': 'Andaman And Nicobar Islands',
        'Delhi': 'Nct Of Delhi'
    }
    df['state'] = df['state'].replace(state_corrections)
    return df.dropna(subset=[date_col])

print("Loading and Merging...")
bio_df = clean(load_data(BIO_PATH))
demo_df = clean(load_data(DEMO_PATH))
enrol_df = clean(load_data(ENROL_PATH))

# Totals
bio_df['Total_Biometric'] = bio_df['bio_age_5_17'] + bio_df['bio_age_17_']
demo_df['Total_Demographic'] = demo_df['demo_age_5_17'] + demo_df['demo_age_17_']
enrol_df['Total_Enrolment'] = enrol_df['age_0_5'] + enrol_df['age_5_17'] + enrol_df['age_18_greater']

# Group & Merge
group_cols = ['date', 'state', 'district', 'pincode']
bio_grouped = bio_df.groupby(group_cols)[['bio_age_5_17', 'Total_Biometric']].sum().reset_index()
demo_grouped = demo_df.groupby(group_cols)[['demo_age_17_', 'Total_Demographic']].sum().reset_index()
enrol_grouped = enrol_df.groupby(group_cols)[['age_0_5', 'age_5_17', 'age_18_greater', 'Total_Enrolment']].sum().reset_index()

master = pd.merge(enrol_grouped, bio_grouped, on=group_cols, how='outer').fillna(0)
master = pd.merge(master, demo_grouped, on=group_cols, how='outer').fillna(0)
master['Total_Txn'] = master['Total_Enrolment'] + master['Total_Biometric'] + master['Total_Demographic']

# Filter Date
master['date'] = pd.to_datetime(master['date'], dayfirst=True, errors='coerce')
print(f"Original Shape: {master.shape}")
master = master[master['date'] >= '2025-09-01']
print(f"Filtered Shape (Sep-Dec): {master.shape}")
master['Total_Txn'] = master['Total_Enrolment'] + master['Total_Biometric'] + master['Total_Demographic']

print("\n=== ANGLE A: MIGRATION TRACKER ===")
# District Stats
d_stats = master.groupby('district').agg({
    'demo_age_17_': 'sum', 'Total_Demographic': 'sum', 'age_18_greater': 'sum'
}).reset_index()
d_stats = d_stats[d_stats['Total_Demographic'] > 500]

# 1. Migration Flux Index
d_stats['MFI'] = (d_stats['demo_age_17_'] / d_stats['Total_Demographic']) * 100
# 2. Urbanization Pull Ratio
avg_demo = d_stats['Total_Demographic'].mean()
d_stats['Pull_Ratio'] = d_stats['Total_Demographic'] / avg_demo
# 3. Integration Rate
d_stats['Integration_Rate'] = d_stats['demo_age_17_'] / d_stats['age_18_greater'].replace(0, 1)

print("Top 3 Districts (MFI):")
print(d_stats.sort_values('MFI', ascending=False).head(3)[['district', 'MFI']])
print("\nTop 3 Districts (Pull Ratio):")
print(d_stats.sort_values('Pull_Ratio', ascending=False).head(3)[['district', 'Pull_Ratio']])

print("\n=== ANGLE B: DIGITAL MATURITY ===")
# State Stats
s_stats = master.groupby('state').agg({
    'age_0_5': 'sum', 'age_5_17': 'sum', 'Total_Enrolment': 'sum', 
    'bio_age_5_17': 'sum', 'age_18_greater': 'sum'
}).reset_index()
s_stats = s_stats[s_stats['Total_Enrolment'] > 0]

# 4. Infant Velocity
s_stats['Infant_Velocity'] = s_stats['age_0_5'] / s_stats['Total_Enrolment']
# 5. Compliance Score
s_stats['Compliance_Score'] = s_stats['bio_age_5_17'] / s_stats['age_5_17'].replace(0, 1)
# 6. Catch-up Ratio
s_stats['Catchup_Ratio'] = s_stats['age_18_greater'] / s_stats['Total_Enrolment']

print("Top 3 States (Infant Velocity):")
print(s_stats.sort_values('Infant_Velocity', ascending=False).head(3)[['state', 'Infant_Velocity']])
print("\nTop 3 States (Compliance):")
print(s_stats.sort_values('Compliance_Score', ascending=False).head(3)[['state', 'Compliance_Score']])

print("\n=== ANGLE C: ACCESSIBILITY ===")
p_stats = master.groupby('pincode').agg({
    'Total_Txn': 'sum', 'Total_Biometric': 'sum', 'Total_Demographic': 'sum', 'Total_Enrolment': 'sum'
})

# 7. Concentration
top_10_pct = int(len(p_stats) * 0.1)
top_vol = p_stats.sort_values('Total_Txn', ascending=False).head(top_10_pct)['Total_Txn'].sum()
concentration = top_vol / p_stats['Total_Txn'].sum()

# 8. Desert Rate
desert_count = (p_stats['Total_Txn'] < 20).sum()
desert_rate = desert_count / len(p_stats)

# 9. Congestion Index
p_stats['Congestion'] = (p_stats['Total_Biometric'] + p_stats['Total_Demographic']) / p_stats['Total_Enrolment'].replace(0, 1)

print(f"Concentration (Top 10%): {concentration:.1%}")
print(f"Desert Rate: {desert_rate:.1%} ({desert_count} pincodes)")
print(f"Avg Congestion Index: {p_stats['Congestion'].mean():.2f}")

print("\n=== STRATEGIC ACTION FRAMEWORK ===")
# 1. Aggregate State Metrics
s_strat = master.groupby('state').agg({
    'age_0_5': 'sum', 'Total_Enrolment': 'sum',
    'bio_age_5_17': 'sum', 'age_5_17': 'sum',
    'demo_age_17_': 'sum', 'Total_Demographic': 'sum',
    'Total_Txn': 'sum'
}).copy().reset_index()

# Compute Key Metrics (Snake Case as requested)
s_strat['child_capture_velocity'] = s_strat['age_0_5'] / s_strat['Total_Enrolment'].replace(0, 1)
s_strat['teen_biometric_compliance'] = s_strat['bio_age_5_17'] / s_strat['age_5_17'].replace(0, 1)
s_strat['migration_flux_index'] = s_strat['demo_age_17_'] / s_strat['Total_Demographic'].replace(0, 1)

# Desert Rate Calculation
pin_state = master[['pincode', 'state', 'Total_Txn']].groupby(['state', 'pincode']).sum().reset_index()
desert_counts = pin_state[pin_state['Total_Txn'] < 20].groupby('state')['pincode'].count()
total_pincodes = pin_state.groupby('state')['pincode'].count()
desert_rate = (desert_counts / total_pincodes).fillna(0).reset_index(name='service_desert_rate')
s_strat = pd.merge(s_strat, desert_rate, on='state', how='left').fillna(0)

# 2. Logic
def get_action(row):
    if row['child_capture_velocity'] < 0.4: return '🔴 Priority 1: Newborn Enrolment Drive'
    elif row['teen_biometric_compliance'] < 0.6: return '🟠 Priority 2: School-based MBU Camps'
    elif row['migration_flux_index'] > 0.7: return '🔵 Priority 3: Establish Migrant Hubs'
    elif row['service_desert_rate'] > 0.3: return '🟡 Priority 4: Deploy Mobile Vans'
    else: return '🟢 Maintenance: Standard Monitoring'

s_strat['Strategic_Action'] = s_strat.apply(get_action, axis=1)

print("\nStrategic Action Summary:")
# Create valid string for printing
action_counts = s_strat['Strategic_Action'].value_counts()
print(action_counts.to_string().encode('ascii', 'ignore').decode('ascii'))

# 3. Generate Map (Save to HTML for verification)
try:
    import plotly.express as px
    colors = {
        '🔴 Priority 1: Newborn Enrolment Drive': 'red',
        '🟠 Priority 2: School-based MBU Camps': 'orange',
        '🔵 Priority 3: Establish Migrant Hubs': 'blue',
        '🟡 Priority 4: Deploy Mobile Vans': 'yellow',
        '🟢 Maintenance: Standard Monitoring': 'green'
    }
    india_states_geojson = 'https://raw.githubusercontent.com/geohacker/india/master/state/india_state.geojson'
    
    fig = px.choropleth(
        s_strat,
        geojson=india_states_geojson,
        featureidkey='properties.ST_NM',
        locations='state',
        color='Strategic_Action',
        color_discrete_map=colors,
        hover_data=['child_capture_velocity', 'teen_biometric_compliance', 'migration_flux_index', 'service_desert_rate'],
        title='Figure 10: Strategic Intervention Map'
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(mapbox_style="carto-positron")
    fig.write_html("strategic_map.html")
    print("\nMap successfully generated: strategic_map.html")
except Exception as e:
    print(f"\nMap generation failed: {e}")

# Top 5 Intervention
print("\nTop 5 Intervention Districts (Priority 1):")
red_states = s_strat[s_strat['Strategic_Action'].str.contains('Priority 1')]['state']
if not red_states.empty:
    d_int = master[master['state'].isin(red_states)].groupby('district').agg({'age_0_5': 'sum', 'Total_Enrolment': 'sum'})
    d_int['Rate'] = d_int['age_0_5'] / d_int['Total_Enrolment']
    print(d_int.sort_values('Rate').head(5).to_string().encode('ascii', 'ignore').decode('ascii'))
else:
    print("No Red States. Checking Priority 2...")
    orange_states = s_strat[s_strat['Strategic_Action'].str.contains('Priority 2')]['state']
    if not orange_states.empty:
        d_int = master[master['state'].isin(orange_states)].groupby('district').agg({'bio_age_5_17': 'sum', 'age_5_17': 'sum'})
        d_int['Rate'] = d_int['bio_age_5_17'] / d_int['age_5_17']
        print(d_int.sort_values('Rate').head(5).to_string().encode('ascii', 'ignore').decode('ascii'))
