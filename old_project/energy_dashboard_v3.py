"""
energy_dashboard_v3.py
Starter Streamlit dashboard for NESO API, GeoJSONs, and analytics.
"""
import streamlit as st
import requests
import pandas as pd
import json

# --- Config ---
NESO_API_BASE = "https://api.neso.energy/api/3/action/"

# --- Sidebar ---
st.sidebar.title("Energy Dashboard v3")
st.sidebar.markdown("""
- NESO API integration
- GeoJSON overlays
- Analytics & provenance
""")

# --- API/Data Portal Mapping ---
API_PORTAL_MAP = {
    "organization": "Data Group",
    "package": "Dataset",
    "resource": "Data File"
}

# --- Supported NESO API Endpoints ---
NESO_ENDPOINTS = [
    ("organization_list", "List Data Groups"),
    ("package_list", "List Datasets"),
    ("tag_list", "List Tags"),
    ("package_search", "Search Datasets"),
    ("resource_search", "Search Data Files"),
    ("resource_show", "Show Resource Metadata"),
    ("package_show", "Show Dataset Details"),
    ("datastore_search", "Tabular Data Search"),
    ("datastore_search_sql", "SQL Data Search")
]

# --- Helper: Call NESO API ---
def neso_api_call(endpoint, params=None):
    url = NESO_API_BASE + endpoint
    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API call failed: {e}")
        return None

# --- GeoJSON Loader (stub) ---
def load_geojsons():
    st.subheader("GeoJSON Overlays")
    st.info("GeoJSON upload/view coming soon.")
    # Example: st.file_uploader("Upload GeoJSON", type=["geojson"])

# --- NESO API Explorer ---
def neso_api_explorer():
    st.subheader("NESO API Explorer")
    st.markdown("**Supported Endpoints:**")
    for ep, desc in NESO_ENDPOINTS:
        st.markdown(f"- `{ep}`: {desc}")
    st.markdown("---")
    endpoint = st.selectbox("Select NESO API endpoint", [ep for ep, _ in NESO_ENDPOINTS])
    params = {}
    if endpoint == "package_search":
        params["q"] = st.text_input("Search query (q)", "BSUOS")
    elif endpoint == "resource_search":
        params["q"] = st.text_input("Resource search query (q)", "name:BSUOS")
    elif endpoint == "resource_show":
        params["id"] = st.text_input("Resource ID (id)")
    elif endpoint == "package_show":
        params["id"] = st.text_input("Dataset ID (id)")
    elif endpoint == "datastore_search":
        params["resource_id"] = st.text_input("Resource ID (resource_id)")
        params["limit"] = st.number_input("Limit", 1, 10000, 5)
    elif endpoint == "datastore_search_sql":
        params["sql"] = st.text_area("SQL Query", "SELECT * FROM \"resource_id\" LIMIT 5")
    # Add more parameter fields as needed
    if st.button("Call API"):
        result = neso_api_call(endpoint, params)
        st.write(result)

# --- Main App ---
def main():
    st.title("Energy Dashboard v3 (Starter)")
    st.markdown("""
    - NESO API integration (see sidebar for features)
    - GeoJSON overlays (coming soon)
    - Analytics, provenance, and more (stubs)
    """)
    load_geojsons()
    neso_api_explorer()
    st.markdown("---")
    st.info("Analytics, provenance, and geospatial overlays will be added in future versions.")

if __name__ == "__main__":
    main()
