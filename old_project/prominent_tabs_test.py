import streamlit as st
import pandas as pd
from datetime import date

# Simple dashboard with very prominent tabs
st.set_page_config(page_title="Dashboard with Advanced Stats", layout="wide")

# Add a very prominent notice
st.title("UK Energy Dashboard with Advanced Statistics")
st.markdown("""
### IMPORTANT: This dashboard has 4 tabs - please look for the Advanced Statistics tab
""")

# Make tabs very prominent
st.markdown("## Please click on one of these tabs:")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Demand Analysis", 
    "Generation Analysis", 
    "Balancing Analysis", 
    "ADVANCED STATISTICS ← CLICK HERE"
])

with tab1:
    st.header("Demand Analysis")
    st.write("This is the Demand Analysis tab")

with tab2:
    st.header("Generation Analysis")
    st.write("This is the Generation Analysis tab")

with tab3:
    st.header("Balancing Analysis")
    st.write("This is the Balancing Analysis tab")

with tab4:
    st.header("ADVANCED STATISTICS")
    st.write("This is the ADVANCED STATISTICS tab")
    
    # Simple analysis type selector
    analysis_type = st.selectbox(
        "Choose the type of statistical analysis:",
        ["Descriptive Statistics", "Correlation Analysis", "Time Series Analysis", "Hypothesis Testing", "Regression Analysis"]
    )
    
    st.write(f"You selected: {analysis_type}")
    st.success("The Advanced Statistics tab is working correctly!")
