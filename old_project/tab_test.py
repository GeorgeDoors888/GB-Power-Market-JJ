import streamlit as st

st.set_page_config(page_title="Tab Test", layout="wide")
st.title("Tab Test")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Tab 1", "Tab 2", "Tab 3", "Advanced Statistics"])

with tab1:
    st.write("This is tab 1")

with tab2:
    st.write("This is tab 2")

with tab3:
    st.write("This is tab 3")

with tab4:
    st.header("Advanced Statistics")
    st.write("This is the Advanced Statistics tab")
