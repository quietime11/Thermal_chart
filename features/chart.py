import streamlit as st
import plotly.graph_objects as go

def plot_chart(df, groups):
    chart_title = st.text_input("📋 Nhập tên bài test (tiêu đề đồ thị):")

    time_unit = st.radio("🕒 Chọn đơn vị thời gian:", ["Phút", "Giây"])
    time_col = "Elapsed_min" if time_unit == "Phút" else "Elapsed_s"

    speed_col = "Dyno_Speed_[dyno_speed]"
    available_signals = list(groups.keys())
    if speed_col in df.columns:
        available_signals.append(speed_col)

    signals_to_plot = st.multiselect("📊 Chọn tín hiệu:", available_signals,)
    y_scale_mode = st.radio("📉 Trục Y:", ["Tự động scale", "Bắt đầu từ 0"], horizontal=True)

    fig = go.Figure()
    colors = ["#1f77b4", "#ff7f0e", "#7f7f7f", "#bcbd22", "#17becf", "#2ca02c"]

    for i, sig in enumerate(signals_to_plot):
        if sig == speed_col:
            continue
        fig.add_trace(go.Scatter(
            x=df[time_col], y=df[sig], name=sig,
            line=dict(color=colors[i % len(colors)], width=2)
        ))

    if speed_col in signals_to_plot:
        fig.add_trace(go.Scatter(
            x=df[time_col], y=df[speed_col],
            name="Speed", line=dict(color="darkblue", width=3), yaxis="y2"
        ))

    step = 10 if time_unit == "Phút" else 100
    grid_lines = list(range(0, int(df[time_col].max()) + step, step))

    if y_scale_mode == "Bắt đầu từ 0":
        # Lấy giá trị cực đại cho các trục
        temp_max = df[[sig for sig in signals_to_plot if sig != speed_col]].max().max()
        speed_max = df[speed_col].max() if speed_col in signals_to_plot and speed_col in df.columns else 0

        # Giới hạn range cho đồng bộ
        yaxis_range = [0, temp_max * 1.1] if not pd.isna(temp_max) else [0, 1]
        yaxis2_range = [0, speed_max * 1.1] if not pd.isna(speed_max) else [0, 1]
    else:
        yaxis_range = None
        yaxis2_range = None
    
    # --- Cập nhật layout ---
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
            range=yaxis_range
        ),
        yaxis2=dict(
            title="Speed [kph]",
            overlaying="y",
            side="right",
            range=yaxis2_range
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        template="plotly_white",
        height=600,
        margin=dict(t=80, b=80)
    )

    st.plotly_chart(fig, use_container_width=True)
