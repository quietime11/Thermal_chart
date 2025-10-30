import streamlit as st

def select_grouping_mode(df):
    mode = st.radio("🔧 Chọn chế độ nhóm cảm biến:", ["Tự động", "Thủ công"])
    temp_cols = [c for c in df.columns if "TEMP" in c]
    groups = {}

    if mode == "Tự động":
        st.info("🤖 Nhóm cảm biến tự động theo đặc trưng nhiệt độ.")
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
        for k, v in groups.items():
            st.write(f"**{k}:** {', '.join(v) if v else '(Không có cảm biến phù hợp)'}")

    else:
        st.info("✏️ Tạo nhóm cảm biến thủ công.")
        if "groups_manual" not in st.session_state:
            st.session_state.groups_manual = {}
        used_sensors = [s for sensors in st.session_state.groups_manual.values() for s in sensors]
        available_sensors = [s for s in temp_cols if s not in used_sensors]

        with st.expander("➕ Tạo nhóm mới"):
            new_group_name = st.text_input("Tên nhóm mới:")
            new_group_sensors = st.multiselect("Chọn cảm biến:", available_sensors)
            if st.button("Thêm nhóm"):
                if new_group_name and new_group_sensors:
                    st.session_state.groups_manual[new_group_name] = new_group_sensors
                    st.success(f"✅ Thêm nhóm {new_group_name}")
                    st.rerun()

        if st.session_state.groups_manual:
            st.write("### 📋 Nhóm hiện có:")
            for gname, sensors in st.session_state.groups_manual.items():
                st.write(f"**{gname}:** {', '.join(sensors)}")
            remove = st.selectbox("🗑️ Xóa nhóm:", ["(Không)", *st.session_state.groups_manual.keys()])
            if remove != "(Không)" and st.button("Xóa nhóm này"):
                del st.session_state.groups_manual[remove]
                st.success(f"Đã xóa nhóm {remove}")
                st.rerun()

        groups = st.session_state.groups_manual

    for name, cols in groups.items():
        if len(cols) > 0:
            valid_cols = [c for c in cols if c in df.columns]
            df[name] = df[valid_cols].mean(axis=1)

    return groups
