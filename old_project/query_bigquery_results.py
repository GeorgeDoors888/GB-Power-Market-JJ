"""
Query BigQuery results from UK Energy analysis
"""
from google.cloud import bigquery
import pandas as pd
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np

# Set proper project ID and dataset information
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ANALYTICS = "uk_energy_analysis"

def get_correlation_matrix():
    """Retrieve the correlation matrix and visualize it."""
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    SELECT * FROM `{PROJECT_ID}.{DATASET_ANALYTICS}.correlation_matrix`
    """
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        print("No correlation data found")
        return
    
    # Pivot the data to get a proper correlation matrix
    if 'variable' in df.columns:
        # Get the variable names
        variables = df['variable'].unique()
        
        # Create a correlation matrix
        corr_matrix = pd.DataFrame(index=variables, columns=variables)
        
        # Fill in the matrix
        for _, row in df.iterrows():
            var = row['variable']
            for v in variables:
                if v in row:
                    corr_matrix.loc[var, v] = row[v]
        
        # Print the correlation matrix
        print("\nCorrelation Matrix:")
        print(corr_matrix.round(2))
        
        # Find the strongest correlations (absolute value)
        corrs = []
        for i in range(len(variables)):
            for j in range(i+1, len(variables)):
                var1 = variables[i]
                var2 = variables[j]
                if not pd.isna(corr_matrix.loc[var1, var2]):
                    corrs.append((var1, var2, abs(corr_matrix.loc[var1, var2])))
        
        # Sort by correlation strength
        corrs.sort(key=lambda x: x[2], reverse=True)
        
        print("\nStrongest Correlations:")
        for var1, var2, corr in corrs[:5]:  # Top 5
            direction = "positive" if corr_matrix.loc[var1, var2] > 0 else "negative"
            print(f"{var1} and {var2}: {corr_matrix.loc[var1, var2]:.2f} ({direction})")
    else:
        print(df)

def get_regression_results():
    """Retrieve regression results."""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Carbon intensity regression
    query1 = f"""
    SELECT * FROM `{PROJECT_ID}.{DATASET_ANALYTICS}.regression_carbon_intensity`
    """
    carbon_reg = client.query(query1).to_dataframe()
    
    # Balancing cost regression
    query2 = f"""
    SELECT * FROM `{PROJECT_ID}.{DATASET_ANALYTICS}.regression_balancing_cost`
    """
    balancing_reg = client.query(query2).to_dataframe()
    
    print("\nRegression Results:")
    
    if not carbon_reg.empty:
        print("\nCarbon Intensity Regression:")
        print(f"R-squared: {carbon_reg['r_squared'].values[0]:.3f}")
        print(f"Wind Generation coefficient: {carbon_reg['beta_wind_generation'].values[0]:.3f} (p={carbon_reg['p_wind_generation'].values[0]:.3f})")
        print(f"Temperature coefficient: {carbon_reg['beta_temperature'].values[0]:.3f} (p={carbon_reg['p_temperature'].values[0]:.3f})")
    
    if not balancing_reg.empty:
        print("\nBalancing Cost Regression:")
        print(f"R-squared: {balancing_reg['r_squared'].values[0]:.3f}")
        print(f"Wind Generation coefficient: {balancing_reg['beta_wind_generation'].values[0]:.3f} (p={balancing_reg['p_wind_generation'].values[0]:.3f})")
        print(f"Temperature coefficient: {balancing_reg['beta_temperature'].values[0]:.3f} (p={balancing_reg['p_temperature'].values[0]:.3f})")
        print(f"Carbon Intensity coefficient: {balancing_reg['beta_carbon_intensity'].values[0]:.3f} (p={balancing_reg['p_carbon_intensity'].values[0]:.3f})")

def get_seasonal_patterns():
    """Retrieve seasonal patterns."""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Wind generation seasonal
    query1 = f"""
    SELECT * FROM `{PROJECT_ID}.{DATASET_ANALYTICS}.seasonal_wind_generation`
    """
    wind_seasonal = client.query(query1).to_dataframe()
    
    # Carbon intensity seasonal
    query2 = f"""
    SELECT * FROM `{PROJECT_ID}.{DATASET_ANALYTICS}.seasonal_carbon_intensity`
    """
    carbon_seasonal = client.query(query2).to_dataframe()
    
    print("\nSeasonal Analysis:")
    
    if not wind_seasonal.empty:
        wind_by_season = wind_seasonal[wind_seasonal['period_type'] == 'season']
        print("\nWind Generation by Season:")
        for _, row in wind_by_season.iterrows():
            print(f"{row['period_name']}: {row['mean']:.2f} (std: {row['std']:.2f})")
    
    if not carbon_seasonal.empty:
        carbon_by_season = carbon_seasonal[carbon_seasonal['period_type'] == 'season']
        print("\nCarbon Intensity by Season:")
        for _, row in carbon_by_season.iterrows():
            print(f"{row['period_name']}: {row['mean']:.2f} (std: {row['std']:.2f})")

if __name__ == "__main__":
    print("==== UK Energy BigQuery Analysis Results ====")
    
    # Get correlation matrix
    get_correlation_matrix()
    
    # Get regression results
    get_regression_results()
    
    # Get seasonal patterns
    get_seasonal_patterns()
    
    print("\nAnalysis complete!")
