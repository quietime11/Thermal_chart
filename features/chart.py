import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

def plot_chart(df, groups):
    chart_title = st.text_input("📋 Nhập tên bài test (tiêu đề đồ thị):")

    # --- Chọn đơn vị thời gian ---
    time_unit = st.radio("🕒 Chọn đơn vị thời gian:", ["Phút", "Giây"], horizontal=True)
    time_col = "Elapsed_min" if time_unit == "Phút" else "Elapsed_s"

    # --- Cột tốc độ ---
    speed_col = "Dyno_Speed_[dyno_speed]"
    available_signals = list(groups.keys())
    if speed_col in df.columns:
        available_signals.append(speed_col)

    # --- Chọn tín hiệu ---
    signals_to_plot = st.multiselect("📊 Chọn tín hiệu cần hiển thị:", available_signals)
    y_scale_mode = st.radio("📉 Trục Y:", ["Tự động scale", "Bắt đầu từ 0"], horizontal=True)

    # --- Tạo biểu đồ ---
    fig = go.Figure()
    colors = ["#1f77b4", "#ff7f0e", "#7f7f7f", "#bcbd22", "#17becf", "#2ca02c"]

    for i, sig in enumerate(signals_to_plot):
        if sig == speed_col:
            continue
        if sig in df.columns:
            fig.add_trace(go.Scatter(
                x=df[time_col], y=df[sig],
                name=sig, line=dict(color=colors[i % len(colors)], width=2)
            ))

    if speed_col in signals_to_plot and speed_col in df.columns:
        fig.add_trace(go.Scatter(
            x=df[time_col], y=df[speed_col],
            name="Speed", line=dict(color="darkblue", width=3), yaxis="y2"
        ))

    # --- Cấu hình layout cơ bản ---
    fig.update_layout(
        title=f"{chart_title} ({'Phút' if time_unit == 'Phút' else 'Giây'})",
        xaxis_title=f"Time ({'min' if time_unit == 'Phút' else 's'})",
        yaxis_title="Temperature [°C]",
        yaxis2=dict(title="Speed [kph]", overlaying="y", side="right"),
        template="plotly_white",
        height=600
    )

    # --- Cho phép chọn số thanh dọc ---
    num_markers = st.radio("📍 Số lượng thanh dọc:", [0, 1, 2], horizontal=True)

    # --- Hiển thị biểu đồ có thể tương tác ---
    st.write("👉 Click vào đồ thị để đặt hoặc di chuyển thanh dọc.")
    clicked_points = plotly_events(
        fig, click_event=True, hover_event=False, select_event=False, override_height=600
    )

    # --- Lưu vị trí các thanh dọc trong session ---
    if "marker_positions" not in st.session_state:
        st.session_state.marker_positions = []

    # Nếu click vào biểu đồ → cập nhật marker
    if clicked_points and len(clicked_points) > 0:
        x_clicked = clicked_points[0]["x"]
        # Nếu ít hơn số thanh → thêm mới
        if len(st.session_state.marker_positions) < num_markers:
            st.session_state.marker_positions.append(x_clicked)
        else:
            # Nếu đủ số thanh, thay thế thanh gần nhất
            diffs = [abs(x_clicked - x) for x in st.session_state.marker_positions]
            idx = diffs.index(min(diffs))
            st.session_state.marker_positions[idx] = x_clicked

    # Giới hạn đúng số thanh được chọn
    st.session_state.marker_positions = st.session_state.marker_positions[:num_markers]

    # --- Vẽ các thanh dọc ---
    for i, pos in enumerate(st.session_state.marker_positions):
        fig.add_vline(
            x=pos,
            line_width=2,
            line_dash="dash",
            line_color="red" if i == 0 else "green",
            annotation_text=f"Marker {i+1}",
            annotation_position="top"
        )

    # --- Hiển thị lại biểu đồ với marker ---
    st.plotly_chart(fig, use_container_width=True)

    # --- Hiển thị bảng dữ liệu marker ---
    if st.session_state.marker_positions:
        results = []
        for i, pos in enumerate(st.session_state.marker_positions):
            idx = (df[time_col] - pos).abs().idxmin()
            row = {"Thanh": f"Marker {i+1}", "Thời gian": f"{df[time_col].iloc[idx]:.2f}"}
            for sig in signals_to_plot:
                if sig in df.columns:
                    row[sig] = f"{df[sig].iloc[idx]:.2f}"
            results.append(row)
        st.dataframe(pd.DataFrame(results))

        # --- Hiển thị Δt nếu có 2 thanh ---
        if len(st.session_state.marker_positions) == 2:
            delta_t = abs(st.session_state.marker_positions[1] - st.session_state.marker_positions[0])
            unit = "phút" if time_unit == "Phút" else "giây"
            st.markdown(f"⏱️ **Khoảng thời gian giữa 2 thanh: {delta_t:.2f} {unit}**")
