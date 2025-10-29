import streamlit as st
import pandas as pd

def load_data(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)
        st.success("✅ File đã được tải thành công!")

        if "Time" not in df.columns:
            st.error("❌ Không tìm thấy cột 'Time' trong file CSV.")
            return None

        df["Time"] = pd.to_datetime(df["Time"], format="%Y.%m.%d._%H:%M:%S.%f", errors="coerce")
        df = df.sort_values("Time").reset_index(drop=True)
        df["Elapsed_s"] = (df["Time"] - df["Time"].iloc[0]).dt.total_seconds()
        df["Elapsed_min"] = df["Elapsed_s"] / 60

        return df
    except Exception as e:
        st.error(f"⚠️ Lỗi khi đọc file: {e}")
        return None
