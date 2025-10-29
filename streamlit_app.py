import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Cấu hình giao diện ---
st.set_page_config(page_title="HVAC Cool Down Graph", page_icon="❄️", layout="wide")
st.title("❄️ AC Cabin Cool Down Thermal Analyzer (Dual Y + Grid)")
st.write("Upload file dữ liệu HVAC để vẽ đồ thị có 2 trục tung và đường lưới thời gian như mẫu OEM.")

# --- Upload file ---
uploaded_file = st.file_uploader("📤 Tải lên file CSV (VD: data_thermal.csv)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File đã được tải thành công!")

    # --- Xử lý thời gian ---
    if "Time" not in df.columns:
        st.error("❌ Không tìm thấy cột 'Time' trong file CSV.")
        st.stop()

    df["Time"] = pd.to_datetime(df["Time"], format="%Y.%m.%d._%H:%M:%S.%f", errors="coerce")
    df = df.sort_values("Time").reset_index(drop=True)

    # --- Tính thời gian đếm từ 0 ---
    df["Elapsed_s"] = (df["Time"] - df["Time"].iloc[0]).dt.total_seconds()
    df["Elapsed_min"] = df["Elapsed_s"] / 60

    # --- Chọn đơn vị thời gian ---
    time_unit = st.radio("🕒 Chọn đơn vị thời gian hiển thị:", ["Phút", "Giây"])
    time_col = "Elapsed_min" if time_unit == "Phút" else "Elapsed_s"

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

    # --- Kiểm tra tốc độ ---
    if "Dyno_Speed_[dyno_speed]" not in df.columns:
        st.error("❌ Không tìm thấy cột tốc độ 'Dyno_Speed_[dyno_speed]'.")
        st.stop()

    # --- Chọn tín hiệu để hiển thị ---
    st.subheader("📊 Chọn tín hiệu hiển thị (trục trái = nhiệt độ, trục phải = tốc độ)")
    temp_signals = st.multiselect(
        "Chọn các tín hiệu nhiệt độ:",
        ["Vent_R1", "Vent_R2", "Head_R1", "Head_R2", "Outside_Roof", "Outside_AGS"],
        default=["Vent_R1", "Vent_R2", "Head_R1", "Head_R2", "Outside_Roof", "Outside_AGS"]
    )

    # --- Vẽ đồ thị với 2 trục tung ---
    fig = go.Figure()

    # Trục trái: Nhiệt độ
    colors_temp = ["#1f77b4", "#ff7f0e", "#7f7f7f", "#bcbd22", "#17becf", "#2ca02c"]
    for i, sig in enumerate(temp_signals):
        if sig in df.columns:
            fig.add_trace(go.Scatter(
                x=df[time_col],
                y=df[sig],
                name=sig,
                line=dict(color=colors_temp[i % len(colors_temp)], width=2)
            ))

    # Trục phải: Tốc độ
    fig.add_trace(go.Scatter(
        x=df[time_col],
        y=df["Dyno_Speed_[dyno_speed]"],
        name="Speed",
        line=dict(color="darkblue", width=3),
        yaxis="y2"
    ))

    # --- Tạo các đường lưới dọc theo mốc thời gian ---
    # Tự động xác định bước lưới (mỗi 10 phút hoặc 100 giây)
    step = 10 if time_unit == "Phút" else 100
    max_time = df[time_col].max()
    grid_lines = list(range(0, int(max_time) + step, step))

    # --- Cấu hình đồ thị ---
    fig.update_layout(
        title=f"AC Cabin Cool Down (42°C Ambient) — Time in {time_unit.lower()}",
        xaxis=dict(
            title=f"Time ({'min' if time_unit == 'Phút' else 's'})",
            showgrid=True,
            gridcolor="lightgray",
            gridwidth=1,
            tickmode="array",
            tickvals=grid_lines,
            ticktext=[str(x) for x in grid_lines],
        ),
        yaxis=dict(title="Temperature [°C]", range=[0, None], gridcolor="lightgray", gridwidth=1),
        yaxis2=dict(title="Speed [kph]", overlaying="y", side="right", range=[0, None]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        template="plotly_white",
        margin=dict(t=80, b=80),
        height=600
    )

    # Hiển thị biểu đồ
    st.plotly_chart(fig, use_container_width=True)

    # --- Hiển thị dữ liệu ---
    with st.expander("📂 Xem dữ liệu đã xử lý"):
        st.dataframe(df[[time_col] + temp_signals + ["Dyno_Speed_[dyno_speed]"]].head(30))

    # --- Cho phép tải dữ liệu ---
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Tải xuống dữ liệu đã xử lý", csv, "thermal_processed.csv", "text/csv")

else:
    st.info("⬆️ Hãy tải lên file CSV để bắt đầu phân tích.")
