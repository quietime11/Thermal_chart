
"""
st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)
"""
import subprocess
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

# --- Giao diện tiêu đề ---
st.title("Thermal HVAC graph")

uploaded_file = st.file_uploader("Tải lên file dữ liệu (.xlsx hoặc .csv)", type=["xlsx", "csv"])

if uploaded_file is not None:
    file_name = uploaded_file.name

    # Đọc file tự động
    if file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file, engine="openpyxl")

    # Chuẩn hoá cột
    df.columns = df.columns.str.strip()
    
    st.write("### 👀 Xem trước dữ liệu:")
    st.dataframe(df.head())

    # Chọn cột để vẽ
    columns = df.columns.tolist()
    x_col = st.selectbox("🕒 Chọn cột Thời gian (X)", columns, index=0)
    y_col_speed = st.selectbox("🚗 Chọn cột Tốc độ (Y1)", columns)
    y_col_temp = st.selectbox("🌡️ Chọn cột Nhiệt độ (Y2)", columns)

    # Xử lý dữ liệu: ép kiểu số hoặc thời gian
    df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
    df[y_col_speed] = pd.to_numeric(df[y_col_speed], errors='coerce')
    df[y_col_temp] = pd.to_numeric(df[y_col_temp], errors='coerce')

    df = df.dropna(subset=[x_col, y_col_speed, y_col_temp])

    # Vẽ đồ thị tốc độ
    st.subheader("🚀 Tốc độ theo thời gian")
    fig_speed = px.line(df, x=x_col, y=y_col_speed, markers=True,
                        title=f"{y_col_speed} theo {x_col}")
    st.plotly_chart(fig_speed, use_container_width=True)

    # Vẽ đồ thị nhiệt độ
    st.subheader("🔥 Nhiệt độ theo thời gian")
    fig_temp = px.line(df, x=x_col, y=y_col_temp, markers=True,
                       title=f"{y_col_temp} theo {x_col}")
    st.plotly_chart(fig_temp, use_container_width=True)
