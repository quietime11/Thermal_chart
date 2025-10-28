import streamlit as st
import pandas as pd
import plotly.express as px

# --- Giao diện chính ---
st.set_page_config(page_title="HVAC Thermal Plot", page_icon="❄️", layout="wide")

st.title("❄️ AC Cabin Cool Down Thermal Analyzer")
st.write("Upload file dữ liệu HVAC để tự động phân tích và vẽ đồ thị nhiệt độ – tốc độ.")

# --- Upload file CSV ---
uploaded_file = st.file_uploader("📤 Tải lên file CSV dữ liệu thử nghiệm (VD: data_thermal.csv)", type=["csv"])

if uploaded_file is not None:
    # --- Đọc dữ liệu ---
    df = pd.read_csv(uploaded_file)
    st.success("✅ File đã được tải thành công!")

    # --- Xử lý thời gian ---
    if "Time" in df.columns:
        df["Time"] = pd.to_datetime(df["Time"], format="%Y.%m.%d._%H:%M:%S.%f", errors="coerce")
        df = df.sort_values("Time").reset_index(drop=True)
    else:
        st.error("❌ Không tìm thấy cột 'Time' trong file CSV.")
        st.stop()

    # --- Tính thời gian đếm từ 0 ---
    df["Elapsed_s"] = (df["Time"] - df["Time"].iloc[0]).dt.total_seconds()
    df["Elapsed_min"] = df["Elapsed_s"] / 60

    # --- Cho phép người dùng chọn đơn vị thời gian hiển thị ---
    time_unit = st.radio("🕒 Chọn đơn vị thời gian hiển thị:", ["Phút", "Giây"])
    time_col = "Elapsed_min" if time_unit == "Phút" else "Elapsed_s"

    # --- Kiểm tra cột tốc độ ---
    if "Dyno_Speed_[dyno_speed]" not in df.columns:
        st.error("❌ Không tìm thấy cột 'Dyno_Speed_[dyno_speed]' trong file.")
        st.stop()

    # --- Mapping layout cảm biến ---
    groups = {
        "Outside_AGS": ["Station3_469_M1_CH1_TempK_1_[ST3_TEMP1]"],
        "Outside_Roof": ["Station3_469_M1_CH2_TempK_2_[ST3_TEMP2]"],
        "Vent_R1": [
            "Station3_469_M2_CH1_TempK_3_[ST3_TEMP3]",
            "Station3_469_M2_CH2_TempK_4_[ST3_TEMP4]",
            "Station3_469_M3_CH1_TempK_5_[ST3_TEMP5]",
            "Station3_469_M3_CH2_TempK_6_[ST3_TEMP6]",
        ],
        "Head_R1": [
            "Station3_469_M4_CH1_TempK_7_[ST3_TEMP7]",
            "Station3_469_M4_CH2_TempK_8_[ST3_TEMP8]",
            "Station3_469_M5_CH1_TempK_9_[ST3_TEMP9]",
            "Station3_469_M5_CH2_TempK_10_[ST3_TEMP10]",
        ],
        "Vent_R2": [
            "Station3_469_M6_CH1_TempK_11_[ST3_TEMP11]",
            "Station3_469_M6_CH2_TempK_12_[ST3_TEMP12]",
        ],
        "Head_R2": [
            "Station3_469_M7_CH1_TempK_13_[ST3_TEMP13]",
            "Station3_469_M7_CH2_TempK_14_[ST3_TEMP14]",
            "Station3_469_M8_CH1_TempK_15_[ST3_TEMP15]",
            "Station3_469_M8_CH2_TempK_16_[ST3_TEMP16]",
        ],
    }

    # --- Tính trung bình từng nhóm ---
    for name, cols in groups.items():
        valid_cols = [c for c in cols if c in df.columns]
        if valid_cols:
            df[name] = df[valid_cols].mean(axis=1)
        else:
            st.warning(f"⚠️ Không tìm thấy cột dữ liệu cho nhóm {name}")

    # --- Chọn dữ liệu để vẽ ---
    st.subheader("📊 Chọn dữ liệu hiển thị trên đồ thị")
    options = st.multiselect(
        "Chọn các tín hiệu muốn hiển thị:",
        ["Vent_R1", "Vent_R2", "Head_R1", "Head_R2", "Outside_Roof", "Outside_AGS", "Dyno_Speed_[dyno_speed]"],
        default=["Vent_R1", "Vent_R2", "Head_R1", "Head_R2", "Outside_Roof", "Outside_AGS", "Dyno_Speed_[dyno_speed]"],
    )

    # --- Vẽ đồ thị ---
    st.subheader("📈 Kết quả đồ thị (Elapsed Time)")
    fig = px.line(
        df,
        x=time_col,
        y=options,
        title=f"AC Cabin Cool Down Performance ({'Phút' if time_unit == 'Phút' else 'Giây'})",
        labels={"value": "Temperature [°C] / Speed [km/h]", time_col: f"Thời gian ({'phút' if time_unit == 'Phút' else 'giây'})"},
    )
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
    st.plotly_chart(fig, use_container_width=True)

    # --- Hiển thị dữ liệu ---
    with st.expander("📂 Xem dữ liệu đã xử lý"):
        st.dataframe(df[[time_col] + options].head(30))

    # --- Cho phép tải dữ liệu ---
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Tải xuống dữ liệu đã xử lý", csv, "thermal_processed.csv", "text/csv")

else:
    st.info("⬆️ Hãy tải lên file CSV để bắt đầu phân tích.")
