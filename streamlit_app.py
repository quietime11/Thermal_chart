import streamlit as st
from features.upload_data import load_data
from features.group import select_grouping_mode
from features.chart import plot_chart

st.set_page_config(page_title="Automatic HVAC Thermal Graph Tool", page_icon="🌡️", layout="wide")
st.title("🌡️ HVAC Thermal Test Analyzer")

uploaded_file = st.file_uploader("Upload file CSV (E.g.: data_thermal.csv)", type=["csv"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is not None:
        groups = select_grouping_mode(df)
        plot_chart(df, groups)
else:
    st.info("Please upload CSV file of the thermal data.")
