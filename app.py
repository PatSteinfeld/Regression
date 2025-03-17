import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder

# Streamlit App Title
st.set_page_config(page_title="Auditors Planning Schedule", layout="wide")
st.title("🗂️ Auditors Planning Schedule")

# Sidebar Navigation
st.sidebar.title("🔍 Navigation")
app_mode = st.sidebar.radio("Choose a section:", ["Input Generator", "Schedule Generator"])

# Initialize session state
if "audit_data" not in st.session_state:
    st.session_state.audit_data = {}

if "schedule_generated" not in st.session_state:
    st.session_state.schedule_generated = False

if "activity_status" not in st.session_state:
    st.session_state.activity_status = {}

if "schedule_data" not in st.session_state:
    st.session_state.schedule_data = None

# Predefined Activities
common_activities = {
    "Meeting & Management": [
        "Opening meeting with top management",
        "Top management interview - Context of Organization",
        "Management Representative Interview",
        "HR / Training - Roles, responsibility & authority",
        "Procurement Process Audit",
        "Stores & Scrap Yard Inspection"
    ],
    "Maintenance Activities": [
        "Mechanical Maintenance Audit",
        "Electrical Maintenance Audit",
        "Instrumentation Maintenance Audit",
        "Civil Maintenance Inspection",
        "Utilities Process Audit",
        "End of Day Summary with Management"
    ]
}

# Predefined Audit Types
predefined_audit_types = ["IA", "P1", "P2", "P3", "P4", "P5", "RC"]

# ---------------- INPUT GENERATOR ----------------
if app_mode == "Input Generator":
    st.header("📋 Input Generator")

    if st.session_state.schedule_generated:
        st.warning("⚠️ Schedule has been generated. Editing is locked.")
    else:
        st.subheader("Step 1: Define Sites and Activities")
        num_sites = st.number_input("🔹 Number of sites:", min_value=1, step=1, value=1)

        site_activity_data = {}

        for s in range(num_sites):
            site = st.text_input(f"🏢 Enter Site Name {s+1}", key=f"site_{s}")
            if site:
                site_activity_data[site] = {}
                st.session_state.activity_status[site] = {}

                for category, activities in common_activities.items():
                    with st.expander(f"{category} for {site}"):
                        for activity in activities:
                            is_core = st.checkbox(f"✅ Mark '{activity}' as Core", key=f"core_{site}_{activity}")
                            site_activity_data[site][activity] = "Core" if is_core else "Non-Core"
                            st.session_state.activity_status[site][activity] = "Available"

        site_audit_data = {}

        st.subheader("Step 2: Add Audits for Each Site")

        for site in site_activity_data.keys():
            with st.expander(f"📍 Site: {site}"):
                audit_data = []
                num_audits = st.number_input(f"📝 How many audits for {site}?", min_value=1, step=1, value=1, key=f"num_audits_{site}")

                for i in range(num_audits):
                    audit_type = st.selectbox(f"📌 Select Audit Type {i+1}", predefined_audit_types, key=f"audit_type_{site}_{i}")
                    proposed_date = st.date_input(f"📅 Proposed Date {i+1}", key=f"date_{site}_{i}")
                    mandays = st.number_input(f"⏳ Mandays {i+1}", min_value=1, step=1, key=f"mandays_{site}_{i}")

                    available_activities = {activity: status for activity, status in st.session_state.activity_status[site].items() if status == "Available"}
                    selected_activities = {activity: st.checkbox(activity, key=f"{activity}_{site}_{i}") for activity in available_activities.keys()}

                    for activity, selected in selected_activities.items():
                        if selected:
                            st.session_state.activity_status[site][activity] = "Selected"

                    audit_entry = {
                        "Audit Type": audit_type,
                        "Proposed Date": proposed_date.strftime("%Y-%m-%d"),
                        "Mandays": mandays,
                        "Total Hours": mandays * 8,
                        "Activities": {activity: "✔️" if selected else "✖️" for activity, selected in selected_activities.items()},
                        "Core Status": {activity: site_activity_data[site][activity] for activity in selected_activities}
                    }

                    audit_data.append(audit_entry)

                site_audit_data[site] = audit_data

        if st.button("💾 Save Data for Scheduling"):
            st.session_state.audit_data = site_audit_data
            st.success("✅ Data saved! Proceed to the Schedule Generator.")

# ---------------- SCHEDULE GENERATOR ----------------
if app_mode == "Schedule Generator":
    st.header("📆 Schedule Generator")

    if not st.session_state.audit_data:
        st.warning("⚠️ No data available. Please use the Input Generator.")
    else:
        selected_site = st.selectbox("📍 Select Site", list(st.session_state.audit_data.keys()))
        selected_audit_type = st.selectbox("📌 Select Audit Type", predefined_audit_types)

        auditors = st.text_area("📝 Enter Auditors' Names (One per line)").split('\n')
        coded_auditors = st.multiselect("🛠️ Select Coded Auditors", auditors)

        if st.button("📅 Generate Schedule"):
            schedule_data = []
            start_time = datetime.strptime('09:00', '%H:%M')

            for audit in st.session_state.audit_data[selected_site]:
                if audit["Audit Type"] == selected_audit_type:
                    activities = [activity for activity, status in audit["Activities"].items() if status == "✔️"]

                    for activity in activities:
                        core_status = audit["Core Status"].get(activity, "Non-Core")
                        allowed_auditors = coded_auditors if core_status == "Core" else auditors

                        schedule_data.append({
                            "Activity": activity,
                            "Core Status": core_status,
                            "Start Time": start_time.strftime('%H:%M'),
                            "End Time": "",
                            "Assigned Auditor": "",
                            "Allowed Auditors": ", ".join(allowed_auditors)
                        })

                        start_time += timedelta(minutes=90)
                        if start_time.strftime('%H:%M') == '13:00':
                            start_time += timedelta(minutes=30)

            st.session_state.schedule_data = pd.DataFrame(schedule_data)

        if st.session_state.schedule_data is not None:
            st.write("### 📝 Editable Schedule")

            gb = GridOptionsBuilder.from_dataframe(st.session_state.schedule_data)
            gb.configure_default_column(editable=True)
            grid_options = gb.build()
            edited_data = AgGrid(st.session_state.schedule_data, gridOptions=grid_options, height=400)

            # Gantt Chart Visualization
            fig = px.timeline(st.session_state.schedule_data, x_start="Start Time", x_end="End Time", y="Assigned Auditor", color="Core Status")
            st.plotly_chart(fig)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                edited_data["data"].to_excel(writer, sheet_name='Schedule', index=False)
            st.download_button("📥 Download Schedule as Excel", data=output.getvalue(), file_name="Auditors_Planning_Schedule.xlsx")

        st.session_state.schedule_generated = True




