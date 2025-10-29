import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Giao diện chính ---
st.set_page_config(page_title="HVAC Cool Down Analyzer", page_icon="❄️", layout="wide")
st.title("❄️ AC Cabin Cool Down Thermal Analyzer (Auto / Manual Grouping)")
st.write("Phân tích dữ liệu HVAC với 2 chế độ nhóm cảm biến: **Tự động** hoặc **Thủ công**.")

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
    df["Elapsed_s"] = (df["Time"] - df["Time"].iloc[0]).dt.total_seconds()
    df["Elapsed_min"] = df["Elapsed_s"] / 60

    # --- Chọn đơn vị thời gian ---
    time_unit = st.radio("🕒 Chọn đơn vị thời gian hiển thị:", ["Phút", "Giây"])
    time_col = "Elapsed_min" if time_unit == "Phút" else "Elapsed_s"

    # --- Chọn chế độ nhóm ---
    mode = st.radio("🔧 Chọn chế độ nhóm cảm biến:", ["Tự động", "Thủ công"])

    # --- Lấy danh sách cảm biến ---
    temp_cols = [c for c in df.columns if "TEMP" in c]
    groups = {}

    # --- CHẾ ĐỘ TỰ ĐỘNG ---
    if mode == "Tự động":
        st.info("🤖 Đang nhóm cảm biến tự động dựa trên đặc trưng nhiệt độ (mean & delta).")

        groups_auto = {"Vent": [], "Head": [], "Outside": []}

        for col in temp_cols:
            series = df[col].dropna()
            if len(series) < 5:
                continue
            mean_temp = series.mean()
            delta_temp = series.max() - series.min()

            if mean_temp < 20 and delta_temp > 20:
                groups_auto["Vent"].append(col)
            elif 20 <= mean_temp < 35 and delta_temp > 10:
                groups_auto["Head"].append(col)
            elif mean_temp > 35 and delta_temp < 5:
                groups_auto["Outside"].append(col)

        groups = groups_auto

        # Hiển thị nhóm đã nhận dạng
        st.write("### 🔍 Kết quả nhóm tự động:")
        for k, v in groups.items():
            st.write(f"**{k}:** {', '.join(v) if v else '(Không có cảm biến phù hợp)'}")

    # --- CHẾ ĐỘ THỦ CÔNG ---
    else:
        st.info("✏️ Chọn thủ công cảm biến theo layout thực tế.")
        Vent_R1 = st.multiselect("Chọn cảm biến Vent R1:", temp_cols)
        Vent_R2 = st.multiselect("Chọn cảm biến Vent R2:", temp_cols)
        Head_R1 = st.multiselect("Chọn cảm biến Head R1:", temp_cols)
        Head_R2 = st.multiselect("Chọn cảm biến Head R2:", temp_cols)
        Outside_Roof = st.multiselect("Chọn cảm biến Outside Roof:", temp_cols)
        Outside_AGS = st.multiselect("Chọn cảm biến Outside AGS:", temp_cols)

        groups = {
            "Vent_R1": Vent_R1,
            "Vent_R2": Vent_R2,
            "Head_R1": Head_R1,
            "Head_R2": Head_R2,
            "Outside_Roof": Outside_Roof,
            "Outside_AGS": Outside_AGS,
        }

    # --- Kiểm tra cột tốc độ ---
    if "Dyno_Speed_[dyno_speed]" not in df.columns:
        st.error("❌ Không tìm thấy cột tốc độ 'Dyno_Speed_[dyno_speed]'.")
        st.stop()

    # --- Tính trung bình từng nhóm ---
    for name, cols in groups.items():
        if len(cols) > 0:
            valid_cols = [c for c in cols if c in df.columns]
            df[name] = df[valid_cols].mean(axis=1)

    # --- Chọn tín hiệu để hiển thị ---
    st.subheader("📊 Chọn tín hiệu hiển thị")
    available_signals = list(groups.keys()) + ["Dyno_Speed_[dyno_speed]"]
    default_signals = [s for s in available_signals if "Vent" in s or "Head" in s or "Outside" in s] + ["Dyno_Speed_[dyno_speed]"]

    signals_to_plot = st.multiselect(
        "Chọn các tín hiệu cần hiển thị:",
        available_signals,
        default=default_signals,
    )

    # --- Tạo đồ thị 2 trục tung ---
    fig = go.Figure()

    # Trục trái (nhiệt độ)
    colors_temp = ["#1f77b4", "#ff7f0e", "#7f7f7f", "#bcbd22", "#17becf", "#2ca02c"]
    for i, sig in enumerate(signals_to_plot):
        if sig == "Dyno_Speed_[dyno_speed]":
            continue
        if sig in df.columns:
            fig.add_trace(go.Scatter(
                x=df[time_col],
                y=df[sig],
                name=sig,
                line=dict(color=colors_temp[i % len(colors_temp)], width=2)
            ))

    # Trục phải (tốc độ)
    if "Dyno_Speed_[dyno_speed]" in signals_to_plot:
        fig.add_trace(go.Scatter(
            x=df[time_col],
            y=df["Dyno_Speed_[dyno_speed]"],
            name="Speed",
            line=dict(color="darkblue", width=3),
            yaxis="y2"
        ))

    # --- Cấu hình lưới dọc ---
    step = 10 if time_unit == "Phút" else 100
    max_time = df[time_col].max()
    grid_lines = list(range(0, int(max_time) + step, step))

    # --- Cấu hình layout ---
    fig.update_layout(
        title=f"AC Cabin Cool Down ({'Phút' if time_unit == 'Phút' else 'Giây'})",
        xaxis=dict(
            title=f"Time ({'min' if time_unit == 'Phút' else 's'})",
            showgrid=True,
            gridcolor="lightgray",
            gridwidth=1,
            tickmode="array",
            tickvals=grid_lines,
            ticktext=[str(x) for x in grid_lines],
        ),
        yaxis=dict(title="Temperature [°C]", gridcolor="lightgray", gridwidth=1),
        yaxis2=dict(title="Speed [kph]", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        template="plotly_white",
        margin=dict(t=80, b=80),
        height=600
    )

    # --- Hiển thị biểu đồ ---
    st.plotly_chart(fig, use_container_width=True)

    # --- Hiển thị dữ liệu ---
    with st.expander("📂 Xem dữ liệu đã xử lý"):
        st.dataframe(df[[time_col] + signals_to_plot].head(30))

    # --- Cho phép tải dữ liệu ---
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Tải xuống dữ liệu đã xử lý", csv, "thermal_processed.csv", "text/csv")

else:
    st.info("⬆️ Hãy tải lên file CSV để bắt đầu phân tích.")
