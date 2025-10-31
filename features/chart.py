import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def plot_chart(df, groups):
    chart_title = st.text_input("Enter the graph title:")

    # --- Time unit ---
    time_unit = st.radio("Select time unit:", ["Minute", "Second"], horizontal=True)
    time_col = "Elapsed_min" if time_unit == "Minute" else "Elapsed_s"

    # --- Speed column (optional) ---
    speed_col = "Dyno_Speed_[dyno_speed]"
    available_signals = list(groups.keys())
    if speed_col in df.columns:
        available_signals.append(speed_col)

    # --- Select signals to display ---
    signals_to_plot = st.multiselect("📊 Select signals to display:", available_signals)
    y_scale_mode = st.radio("📉 Y-axis:", ["Auto scale", "Default (start from 0)"], horizontal=True)

    # --- Initialize chart ---
    fig = go.Figure()
    colors = ["#1f77b4", "#ff7f0e", "#7f7f7f", "#bcbd22", "#17becf", "#2ca02c"]

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

    if speed_col in signals_to_plot and speed_col in df.columns:
        fig.add_trace(go.Scatter(
            x=df[time_col],
            y=df[speed_col],
            name="Speed",
            line=dict(color="darkblue", width=3),
            yaxis="y2"
        ))

    # --- Set axis range ---
    if y_scale_mode == "Default (start from 0)":
        temp_max = df[[sig for sig in signals_to_plot if sig != speed_col]].max().max()
        speed_max = df[speed_col].max() if speed_col in signals_to_plot and speed_col in df.columns else 0
        yaxis_range = [0, temp_max * 1.1] if not pd.isna(temp_max) else [0, 1]
        yaxis2_range = [0, speed_max * 1.1] if not pd.isna(speed_max) else [0, 1]
    else:
        yaxis_range = None
        yaxis2_range = None

    # --- Add set point sliders ---
    st.subheader("Set points")
    num_markers = st.radio("Number of set points:", [0, 1, 2], index=0, horizontal=True)

    marker_positions = []
    if num_markers > 0:
        max_time = float(df[time_col].max())
        for i in range(num_markers):
            pos = st.slider(
                f"Set point position {i+1}",
                0.0, max_time, value=max_time/4*(i+1), step=max_time/200,
                format="%.2f"
            )
            marker_positions.append(pos)

    # --- Add vertical lines and tooltips ---
    annotations = []
    for i, pos in enumerate(marker_positions):
        idx = (df[time_col] - pos).abs().idxmin()
        fig.add_vline(
            x=pos,
            line_width=2,
            line_dash="dash",
            line_color="red" if i == 0 else "green",
            annotation_text=f"Set point {i+1}",
            annotation_position="top"
        )

        # --- Add tooltip marker and text ---
        text_lines = [f"<b>{sig}</b>: {df[sig].iloc[idx]:.2f}" for sig in signals_to_plot if sig in df.columns]
        text_html = "<br>".join(text_lines)
        avg_temp = df[[sig for sig in signals_to_plot if sig != speed_col]].iloc[idx].mean()

        fig.add_trace(go.Scatter(
            x=[pos], y=[avg_temp],
            mode="markers+text",
            text=[f"Set {i+1}<br>{text_html}"],
            textposition="top right",
            marker=dict(color="red" if i == 0 else "green", size=10, symbol="diamond"),
            showlegend=False,
            hoverinfo="skip"
        ))

    # --- Calculate Δt ---
    if len(marker_positions) == 2:
        delta_t = abs(marker_positions[1] - marker_positions[0])
        unit = "Minute" if time_unit == "Minute" else "Second"
        st.markdown(f"⏱️ **Time difference: {delta_t:.2f} {unit}**")

    # --- Layout ---
    fig.update_layout(
        title=f"{chart_title} ({'Minute' if time_unit == 'Minute' else 'Second'})",
        xaxis=dict(
            title=f"Time ({'min' if time_unit == 'Minute' else 's'})",
            showgrid=True,
            gridcolor="lightgray"
        ),
        yaxis=dict(title="Temperature [°C]", range=yaxis_range, gridcolor="lightgray"),
        yaxis2=dict(title="Speed [kph]", overlaying="y", side="right", range=yaxis2_range),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        template="plotly_white",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)
