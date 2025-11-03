import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def plot_chart(df, groups):
    chart_title = st.text_input("Enter the graph title:")

    # --- Chọn đơn vị thời gian ---
    time_unit = st.radio("Select time unit:", ["Minute", "Second"], horizontal=True)
    time_col = "Elapsed_min" if time_unit == "Minute" else "Elapsed_s"

    # --- Cột tốc độ (nếu có) ---
    speed_col = "Dyno_Speed_[dyno_speed]"
    available_signals = list(groups.keys())
    if speed_col in df.columns:
        available_signals.append(speed_col)

    # --- Chọn tín hiệu hiển thị ---
    signals_to_plot = st.multiselect("📊 Select signals to display:", available_signals)
    y_scale_mode = st.radio("📉 Y-axis mode:", ["Auto scale", "Start from 0"], horizontal=True)

    # --- Khởi tạo biểu đồ ---
    fig = go.Figure()
    colors = ["#1f77b4", "#ff7f0e", "#7f7f7f", "#bcbd22", "#17becf", "#2ca02c"]

    # --- Vẽ các đường nhiệt độ ---
    for i, sig in enumerate(signals_to_plot):
        if sig == speed_col:
            continue
        if sig in df.columns:
            fig.add_trace(go.Scatter(
                x=df[time_col],
                y=df[sig],
                name=sig,
                line=dict(color=colors[i % len(colors)], width=2)
            ))

    # --- Vẽ tốc độ ---
    if speed_col in signals_to_plot and speed_col in df.columns:
        fig.add_trace(go.Scatter(
            x=df[time_col],
            y=df[speed_col],
            name="Speed",
            line=dict(color="darkblue", width=3),
            yaxis="y2"
        ))

    # --- Tạo lưới dọc ---
    step = 10 if time_unit == "Minute" else 100
    grid_lines = list(range(0, int(df[time_col].max()) + step, step))

    # --- Scale trục ---
    if y_scale_mode == "Start from 0":
        temp_max = df[[sig for sig in signals_to_plot if sig != speed_col]].max().max()
        speed_max = df[speed_col].max() if speed_col in signals_to_plot and speed_col in df.columns else 0
        yaxis_range = [0, temp_max * 1.1] if not pd.isna(temp_max) else [0, 1]
        yaxis2_range = [0, speed_max * 1.1] if not pd.isna(speed_max) else [0, 1]
    else:
        yaxis_range = None
        yaxis2_range = None

    # --- Cài đặt thanh dọc ---
    st.subheader("Set Point Configuration")
    num_markers = st.radio("Number of set points:", [0, 1, 2], index=0, horizontal=True)

    marker_positions = []
    if num_markers > 0:
        max_time = float(df[time_col].max())
        for i in range(num_markers):
            pos = st.slider(
                f"Set point position {i+1}",
                0.0, max_time, value=max_time / (num_markers + 1) * (i + 1),
                step=max_time / 200,
                format="%.2f"
            )
            marker_positions.append(pos)

            # --- Vẽ đường dọc ---
            fig.add_vline(
                x=pos,
                line_width=2,
                line_dash="dash",
                line_color="red" if i == 0 else "green",
                annotation_text=f"Set point {i+1}",
                annotation_position="top"
            )

    # --- Thêm marker + tooltip cho từng trace ---
    if num_markers > 0:
        for pos in marker_positions:
            for i, sig in enumerate(signals_to_plot):
                if sig not in df.columns:
                    continue
                # tìm điểm gần nhất với Set Point
                idx = (df[time_col] - pos).abs().idxmin()
                x_val = df[time_col].iloc[idx]
                y_val = df[sig].iloc[idx]

                # thêm marker có tooltip
                fig.add_trace(go.Scatter(
                    x=[x_val],
                    y=[y_val],
                    mode="markers",
                    marker=dict(
                        size=9,
                        color=colors[i % len(colors)],
                        symbol="circle",
                        line=dict(width=1, color="black")
                    ),
                    text=[f"<b>{sig}</b><br>Time: {x_val:.2f} {'min' if time_unit == 'Minute' else 's'}<br>Value: {y_val:.2f}"],
                    hoverinfo="text",
                    hovertemplate="%{text}<extra></extra>",
                    name=f"{sig} marker",
                    showlegend=False
                ))

    # --- Cấu hình layout ---
    fig.update_layout(
        title=dict(
            text=f"{chart_title} ({'Minute' if time_unit == 'Minute' else 'Second'})",
            x=0.5,                # 👉 Căn giữa theo trục X
            xanchor="center",     # Giữ vị trí trung tâm
            yanchor="top",        # Neo ở phía trên
            font=dict(size=20, color="black", family="Arial")  # Tuỳ chỉnh font nếu muốn
        ),
        xaxis=dict(
            title=f"Time ({'min' if time_unit == 'Minute' else 's'})",
            showgrid=True,
            gridcolor="lightgray",
            tickmode="array",
            tickvals=grid_lines,
            ticktext=[str(x) for x in grid_lines],
        ),
        yaxis=dict(title="Temperature [°C]", range=yaxis_range, gridcolor="lightgray"),
        yaxis2=dict(title="Speed [kph]", overlaying="y", side="right", range=yaxis2_range),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        template="plotly_white",
        height=600,
        margin=dict(t=80, b=80)
    )

    # --- Hiển thị đồ thị ---
    st.plotly_chart(fig, use_container_width=True)

    # --- Hiển thị bảng giá trị ---
    if num_markers > 0:
        st.subheader("📋 Values at set point:")
        results = []
        for i, pos in enumerate(marker_positions):
            idx = (df[time_col] - pos).abs().idxmin()
            row = {"Set point": f"Set point {i+1}", "Time": f"{df[time_col].iloc[idx]:.2f}"}
            for sig in signals_to_plot:
                if sig in df.columns:
                    row[sig] = f"{df[sig].iloc[idx]:.2f}"
            results.append(row)

        res_df = pd.DataFrame(results)
        st.dataframe(res_df)

        # --- Nếu có 2 thanh: hiển thị Δt ---
        if len(marker_positions) == 2:
            delta_t = abs(marker_positions[1] - marker_positions[0])
            unit = "Minute" if time_unit == "Minute" else "Second"
            st.markdown(f"⏱️ **Time difference between 2 points: {delta_t:.2f} {unit}**")

    # --- Hiển thị dữ liệu ---
    with st.expander("📂 View processed data"):
        st.dataframe(df[[time_col] + signals_to_plot].head(30))

    # --- Cho phép tải dữ liệu ---
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download processed data", csv, "thermal_processed.csv", "text/csv")
