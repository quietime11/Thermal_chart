
"""
st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# --- Giao diện tiêu đề ---
st.title("📈 Tool Vẽ Đồ Thị Nhiệt Độ & Vận Tốc Theo Thời Gian")

# --- Upload file ---
uploaded_file = st.file_uploader("Tải lên file Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    # Đọc dữ liệu từ file
    df = pd.read_excel(uploaded_file)

    # Hiển thị preview
    st.subheader("📋 Dữ liệu đầu vào (5 dòng đầu)")
    st.dataframe(df.head())

    # --- Nhận diện các cột ---
    time_col = [col for col in df.columns if 'Time' in col][0]
    speed_col = [col for col in df.columns if 'Speed' in col][0]
    temp_cols = [col for col in df.columns if 'Temp' in col]

    st.write(f"🕒 Cột thời gian: **{time_col}**")
    st.write(f"🚗 Cột vận tốc: **{speed_col}**")
    st.write(f"🌡️ Số lượng cảm biến nhiệt độ: {len(temp_cols)}")

    # --- Chọn cảm biến cần vẽ ---
    selected_temps = st.multiselect("Chọn cảm biến nhiệt độ muốn hiển thị:", temp_cols, default=temp_cols[:3])

    # --- Xử lý dữ liệu thời gian ---
    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
    df = df.dropna(subset=[time_col])

    # --- Vẽ đồ thị tốc độ ---
    fig_speed = px.line(df, x=time_col, y=speed_col, title="Vận tốc theo thời gian", labels={speed_col: "Tốc độ", time_col: "Thời gian"})
    st.plotly_chart(fig_speed, use_container_width=True)

    # --- Vẽ đồ thị nhiệt độ ---
    if selected_temps:
        df_melt = df.melt(id_vars=[time_col], value_vars=selected_temps, var_name="Cảm biến", value_name="Nhiệt độ")
        fig_temp = px.line(df_melt, x=time_col, y="Nhiệt độ", color="Cảm biến", title="Nhiệt độ theo thời gian")
        st.plotly_chart(fig_temp, use_container_width=True)

    # --- Thống kê nhanh ---
    st.subheader("📊 Thống kê nhanh")
    st.write(df[selected_temps].describe())
else:
    st.info("⬆️ Hãy tải lên file Excel để bắt đầu.")