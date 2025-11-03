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
                line_width=1,
                line_dash="dash",
                line_color="red" if i == 0 else "green",
                annotation_text=f"Set point {i+1}",
                annotation_position="top"
            )

    # --- Thêm tooltip riêng cho từng đường tại Set Point ---
    # Tạo tooltip riêng cho mỗi đường, hiển thị gần điểm giao nhau
    if num_markers > 0:
        for i, pos in enumerate(marker_positions):
            # tìm điểm gần nhất với Set Point (dùng cùng 1 x cho tất cả traces)
            idx = (df[time_col] - pos).abs().idxmin()
            x_val = df[time_col].iloc[idx]
            
            valid_signals = [s for s in signals_to_plot if s in df.columns]
            
            # Tạo tooltip riêng cho từng đường
            for j, sig in enumerate(valid_signals):
                y_val = df[sig].iloc[idx]
                
                # Kiểm tra nếu là đường speed (cần dùng y2 axis)
                is_speed = (sig == speed_col and speed_col in df.columns)
                
                # Thêm marker nhỏ tại điểm giao của từng đường
                fig.add_trace(go.Scatter(
                    x=[x_val],
                    y=[y_val],
                    mode="markers",
                    marker=dict(
                        size=6, #vị trí chỉnh chấm marker
                        color=colors[j % len(colors)] if not is_speed else "darkblue",
                        symbol="circle",
                        line=dict(width=1, color="white")
                    ),
                    yaxis="y2" if is_speed else "y",
                    name=f"{sig} at Set point {i+1}",
                    showlegend=False,
                    hoverinfo="skip"
                ))

                # Tính offset để đặt tooltip chéo 45 độ ở 4 hướng (tránh che đường)
                # Phân bố random giữa 4 góc: trên-trái, trên-phải, dưới-trái, dưới-phải
                diagonal_distance = 35  # Khoảng cách chéo từ điểm giao
                
                # Sử dụng hash để tạo random nhưng ổn định cho mỗi điểm
                import hashlib
                hash_input = f"{i}_{j}_{sig}_{x_val:.2f}_{y_val:.2f}"
                hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
                direction = hash_value % 4  # 0-3 cho 4 hướng
                
                # 4 hướng chéo 45 độ để tránh che đường
                if direction == 0:  # Trên-phải (45°)
                    offset_x = diagonal_distance * 0.707   # cos(45°)
                    offset_y = diagonal_distance * 0.707   # sin(45°)
                elif direction == 1:  # Trên-trái (135°)
                    offset_x = -diagonal_distance * 0.707  # cos(135°)
                    offset_y = diagonal_distance * 0.707   # sin(135°)
                elif direction == 2:  # Dưới-trái (225°)
                    offset_x = -diagonal_distance * 0.707  # cos(225°)
                    offset_y = -diagonal_distance * 0.707  # sin(225°)
                else:  # Dưới-phải (315°)
                    offset_x = diagonal_distance * 0.707   # cos(315°)
                    offset_y = -diagonal_distance * 0.707  # sin(315°)
                
                # Thêm offset nhỏ để tránh chồng chéo khi có nhiều signals
                if len(valid_signals) > 1:
                    extra_offset = (j * 5)  # Offset nhỏ cho từng signal
                    # Điều chỉnh offset theo hướng
                    if direction in [0, 3]:  # Bên phải
                        offset_x += extra_offset
                    else:  # Bên trái
                        offset_x -= extra_offset
                    
                    if direction in [0, 1]:  # Bên trên
                        offset_y += extra_offset * 0.3
                    else:  # Bên dưới
                        offset_y -= extra_offset * 0.3

                # Thêm text annotation chéo 45 độ, chỉ hiển thị giá trị
                # CÁC THÔNG SỐ CÓ THỂ ĐIỀU CHỈNH:
                fig.add_annotation(
                    x=x_val + offset_x/30,  # Chuyển đổi pixel offset sang đơn vị dữ liệu
                    y=y_val + offset_y/8,   # Điều chỉnh tỷ lệ cho trục y
                    text=f"{y_val:.1f}",
                    showarrow=False,  # Bỏ mũi tên
                    yref="y2" if is_speed else "y",  # Sử dụng đúng trục y cho speed
                    
                    # KÍCH THƯỚC & VIỀN TOOLTIP (có thể điều chỉnh):
                    bgcolor="rgba(255,255,255,0.55)",  # Màu nền (thay đổi alpha 0.95 để đậm hơn)
                    bordercolor=colors[j % len(colors)] if not is_speed else "darkblue",
                    borderwidth=2,  # ← ĐIỀU CHỈNH ĐỘ DÀY VIỀN (1→2 để đậm hơn)
                    
                    # KÍCH THƯỚC CHỮ (có thể điều chỉnh):
                    font=dict(
                        size=11,      # ← ĐIỀU CHỈNH KÍCH THƯỚC CHỮ (10→12 để to hơn)
                        color="black",
                        family="Arial, sans-serif"  # Font family để rõ hơn
                    ),
                    
                    # PADDING TOOLTIP (có thể điều chỉnh):
                    xanchor="center",
                    yanchor="middle",
                    # Thêm padding để tooltip to hơn:
                    borderpad=3,    # ← ĐIỀU CHỈNH PADDING BÊN TRONG (mặc định 0→4)
                )

    # --- Cấu hình layout ---
    fig.update_layout(
        title=dict(
            text=f"{chart_title}", #({'Minute' if time_unit == 'Minute' else 'Second'})",
            x=0.5,  # ← ĐIỀU CHỈNH VỊ TRÍ TITLE (0.5 = giữa, 0 = trái, 1 = phải)
            xanchor='center',  # Căn giữa title
            font=dict(
                size=18,  # ← ĐIỀU CHỈNH KÍCH THƯỚC CHỮ TITLE (mặc định ~14, có thể 16-24)
                family="Arial, sans-serif",
                color="black"
            )
        ),
        xaxis=dict(
            title=f"Time ({'min' if time_unit == 'Minute' else 's'})",
            showgrid=True,
            gridcolor="lightgray",
            tickmode="array",
            tickvals=grid_lines,
            ticktext=[str(x) for x in grid_lines],
        ),
        yaxis=dict(title="Temp [°C]", range=yaxis_range, gridcolor="lightgray"),
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
