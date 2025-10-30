import streamlit as st
from pages.upload_data import load_data
from pages.grouping import select_grouping_mode
from pages.chart import plot_chart

st.set_page_config(page_title="HVAC Thermal Graph Tool", page_icon="🌡️", layout="wide")
st.title("🌡️ HVAC Thermal Test Analyzer")

uploaded_file = st.file_uploader("📤 Tải lên file CSV (VD: data_thermal.csv)", type=["csv"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is not None:
        groups = select_grouping_mode(df)
        plot_chart(df, groups)
else:
    st.info("⬆️ Hãy tải lên file CSV để bắt đầu phân tích.")
