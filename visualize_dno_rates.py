#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for better visualizations
sns.set(style="whitegrid", palette="muted", font_scale=1.2)
plt.rcParams["figure.figsize"] = (14, 8)

# Load the organized data
# Try to load the fixed data first, then fall back to original data
if os.path.exists("Organised_DNO_By_Date_Fixed.csv"):
    df = pd.read_csv("Organised_DNO_By_Date_Fixed.csv")
    print("Using fixed organized data file")
else:
    df = pd.read_csv("Organised_DNO_By_Date.csv")
    print("Using original organized data file")
print(f"Loaded data with {df.shape[0]} rows and {df.shape[1]} columns")

# Convert Date to datetime for proper plotting
if 'Date' in df.columns:
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
elif 'Year' in df.columns:
    df['Year'] = pd.to_numeric(df['Year'])
    df['Date'] = pd.to_datetime(df['Year'], format='%Y')
else:
    print("Error: Neither Date nor Year column found in the data")
    exit(1)

# Create a directory for plots
os.makedirs("dno_analysis_plots", exist_ok=True)

# 1. Plot Mean Rate trends over time by DNO
plt.figure(figsize=(16, 10))
sns.lineplot(data=df, x='Year', y='Mean_Rate_p_kWh', hue='DNO_Name', marker='o', linewidth=2.5)
plt.title('Mean DUoS Rates by DNO Over Time', fontsize=16)
plt.ylabel('Mean Rate (p/kWh)', fontsize=14)
plt.xlabel('Year', fontsize=14)
plt.xticks(df['Year'].unique())
plt.grid(True, alpha=0.3)
plt.legend(title='DNO', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig('dno_analysis_plots/mean_rates_by_dno_over_time.png', dpi=300)
plt.close()

# 2. Plot Min/Max Rate Range by DNO
plt.figure(figsize=(16, 10))
for i, dno in enumerate(df['DNO_Key'].unique()):
    dno_data = df[df['DNO_Key'] == dno]
    plt.plot(dno_data['Year'], dno_data['Min_Rate_p_kWh'], 'o--', alpha=0.7, label=f"{dno} Min")
    plt.plot(dno_data['Year'], dno_data['Max_Rate_p_kWh'], 's-', alpha=0.7, label=f"{dno} Max")

plt.title('Min and Max DUoS Rates by DNO Over Time', fontsize=16)
plt.ylabel('Rate (p/kWh)', fontsize=14)
plt.xlabel('Year', fontsize=14)
plt.xticks(df['Year'].unique())
plt.grid(True, alpha=0.3)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig('dno_analysis_plots/min_max_rates_by_dno.png', dpi=300)
plt.close()

# 3. Create a heatmap showing rates by DNO and Year
pivot_df = df.pivot_table(index='DNO_Key', columns='Year', values='Mean_Rate_p_kWh', aggfunc='mean')
plt.figure(figsize=(16, 10))
sns.heatmap(pivot_df, annot=True, fmt=".2f", cmap="YlGnBu", linewidths=.5)
plt.title('Mean DUoS Rate Heatmap by DNO and Year', fontsize=16)
plt.tight_layout()
plt.savefig('dno_analysis_plots/duos_rates_heatmap.png', dpi=300)
plt.close()

# 4. Compare median rates across DNOs in latest year
latest_year = df['Year'].max()
latest_data = df[df['Year'] == latest_year]

plt.figure(figsize=(14, 8))
sns.barplot(data=latest_data, x='DNO_Key', y='Median_Rate_p_kWh')
plt.title(f'Median DUoS Rates by DNO in {latest_year}', fontsize=16)
plt.ylabel('Median Rate (p/kWh)', fontsize=14)
plt.xlabel('DNO', fontsize=14)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('dno_analysis_plots/median_rates_latest_year.png', dpi=300)
plt.close()

# 5. Create summary statistics table
summary_stats = df.groupby('DNO_Key').agg({
    'Mean_Rate_p_kWh': ['mean', 'min', 'max', 'std'],
    'Count': 'mean'
}).round(3)

summary_stats.columns = ['Average Mean Rate', 'Min of Mean Rates', 'Max of Mean Rates', 'Std Dev of Rates', 'Avg Count']
summary_stats = summary_stats.reset_index()
summary_stats.to_csv('dno_analysis_plots/dno_rate_statistics.csv', index=False)

print("\nDNO Rate Statistics:")
print(summary_stats)

print("\n✅ Analysis complete! Plots saved to 'dno_analysis_plots' directory")
