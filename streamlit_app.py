import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Giao diện chính ---
st.set_page_config(page_title="Automatic HVAC Thermal Graph Tool", page_icon="🌡️", layout="wide")
st.title("HVAC Thermal Test")
# st.write("Phân tích dữ liệu HVAC với 2 chế độ nhóm cảm biến: **Tự động** hoặc **Thủ công**.")

# --- Upload file ---
uploaded_file = st.file_uploader("📤 Tải lên file data CSV (VD: data_thermal.csv)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File đã được tải thành công!")

    # --- Nhập tên đồ thị ---
    chart_title = st.text_input("📋 Nhập tên bài test (tiêu đề đồ thị):")
    
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
        st.info("✏️ Chọn thủ công cảm biến theo layout thực tế hoặc tự đặt tên nhóm mới.")

        # --- Khởi tạo session lưu nhóm ---
        if "groups_manual" not in st.session_state:
            st.session_state.groups_manual = {}

        # --- Xác định cảm biến còn lại chưa dùng ---
        used_sensors = [s for sensors in st.session_state.groups_manual.values() for s in sensors]
        available_sensors = [s for s in temp_cols if s not in used_sensors]

        # --- Tạo nhóm mới ---
        with st.expander("➕ Tạo nhóm cảm biến mới"):
            new_group_name = st.text_input("Nhập tên nhóm mới (VD: Vent_R1, Cabin_Front, Battery_Inlet):")
            new_group_sensors = st.multiselect(
                "Chọn cảm biến cho nhóm này:",
                available_sensors,
                key=f"select_{len(st.session_state.groups_manual)}"
            )

            if st.button("Thêm nhóm vào danh sách"):
                if new_group_name and new_group_sensors:
                    st.session_state.groups_manual[new_group_name] = new_group_sensors
                    st.success(f"✅ Đã thêm nhóm **{new_group_name}** ({len(new_group_sensors)} cảm biến).")
                    st.rerun()  # Cập nhật lại danh sách cảm biến còn lại
                else:
                    st.warning("⚠️ Hãy nhập tên và chọn ít nhất 1 cảm biến trước khi thêm.")
        
        # --- Hiển thị danh sách nhóm hiện có ---
        if st.session_state.groups_manual:
            st.subheader("📋 Danh sách nhóm hiện tại:")
            for gname, sensors in st.session_state.groups_manual.items():
                st.write(f"**{gname}:** {', '.join(sensors)}")

            # Cho phép xóa nhóm
            remove_group = st.selectbox("🗑️ Xóa nhóm:", ["(Không)", *st.session_state.groups_manual.keys()])
            if remove_group != "(Không)" and st.button("Xóa nhóm này"):
                del st.session_state.groups_manual[remove_group]
                st.success(f"🗑️ Đã xóa nhóm **{remove_group}**.")
                st.rerun()

        else:
            st.info("Chưa có nhóm nào. Hãy thêm nhóm mới ở trên.")

        groups = st.session_state.groups_manual

    # --- Tính trung bình từng nhóm ---
    for name, cols in groups.items():
        if len(cols) > 0:
            valid_cols = [c for c in cols if c in df.columns]
            df[name] = df[valid_cols].mean(axis=1)
    
    # --- Kiểm tra cột tốc độ ---
    if "Dyno_Speed_[dyno_speed]" not in df.columns:
        st.error("❌ Không tìm thấy cột tốc độ 'Dyno_Speed_[dyno_speed]'.")
        st.stop()

    # --- Chọn tín hiệu hiển thị ---
    st.subheader("📊 Chọn tín hiệu hiển thị")
    available_signals = list(groups.keys())
    default_signals = [s for s in available_signals if "Vent" in s or "Head" in s or "Outside" in s] + ["Dyno_Speed_[dyno_speed]"]

    # --- Nếu có cột tốc độ thì cho phép người dùng tùy chọn thêm ---
    speed_col = "Dyno_Speed_[dyno_speed]"
    add_speed = False
    if speed_col in df.columns:
        add_speed = st.checkbox("Thêm tín hiệu tốc độ Dyno vào danh sách", value=False)
        if add_speed:
            available_signals.append(speed_col)
            
    signals_to_plot = st.multiselect(
        "Chọn các tín hiệu cần hiển thị:",
        available_signals,
        default=list(groups.keys()),
    )

    
    # --- Chọn kiểu hiển thị trục Y ---
    y_scale_mode = st.radio(
        "📉 Chọn chế độ hiển thị trục Y:",
        ["Tự động scale", "Bắt đầu từ 0"],
        horizontal=True
    )
    
    # --- Tạo đồ thị 2 trục tung ---
    fig = go.Figure()

    # Trục trái (nhiệt độ)
    colors_temp = ["#1f77b4", "#ff7f0e", "#7f7f7f", "#bcbd22", "#17becf", "#2ca02c"]
    for i, sig in enumerate(signals_to_plot):
        if sig == speed_col:
            continue
        if sig in df.columns:
            fig.add_trace(go.Scatter(
                x=df[time_col],
                y=df[sig],
                name=sig,
                line=dict(color=colors_temp[i % len(colors_temp)], width=2)
            ))

    # Trục phải (tốc độ)
    if speed_col in signals_to_plot:
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
        title=f"{chart_title} ({'Phút' if time_unit == 'Phút' else 'Giây'})",
        xaxis=dict(
            title=f"Time ({'min' if time_unit == 'Phút' else 's'})",
            showgrid=True,
            gridcolor="lightgray",
            tickmode="array",
            tickvals=grid_lines,
            ticktext=[str(x) for x in grid_lines],
        ),
        yaxis=dict(
            title="Temperature [°C]",
            gridcolor="lightgray",
            rangemode="tozero" if y_scale_mode == "Bắt đầu từ 0" else "normal"
        ),
        yaxis2=dict(
            title="Speed [kph]",
            overlaying="y",
            side="right",
            rangemode="tozero" if y_scale_mode == "Bắt đầu từ 0" else "normal"
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        template="plotly_white",
        height=600,
        margin=dict(t=80, b=80)
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
