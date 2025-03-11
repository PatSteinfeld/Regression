import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from io import BytesIO

# Streamlit App Title
st.title("Auditors Planning Schedule")

# Sidebar Navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a section:", ["Input Generator", "Schedule Generator"])

# Initialize session state for data storage
if "audit_data" not in st.session_state:
    st.session_state.audit_data = {}

if "schedule_generated" not in st.session_state:
    st.session_state.schedule_generated = False

if "activity_status" not in st.session_state:
    st.session_state.activity_status = {}

# Predefined Activities
common_activities = {
    "Meeting & Management": [
        "Opening meeting: With top management to explain the scope of the audit, audit methodology, and reporting.",
        "Top management: Focus Area - Context of Organization.",
        "Management Representative: Focus Area.",
        "HR / Training: Roles, responsibility & authority (5).",
        "Purchase / Procurement / Supply chain: Process (4.4), Roles, responsibility & authority.",
        "Stores including scrap yard: Roles, responsibility & authority (5.3), Resource, competence, awareness."
    ],
    "Maintenance Activities": [
        "Mechanical Maintenance: Determining process (4.4), Roles, responsibility.",
        "Electrical Maintenance: Determining process (4.4), Roles.",
        "Instrumentation Maintenance: Determining process (4.4), Roles.",
        "Civil Maintenance: Determining process (4.4).",
        "Utilities: Determining process (4.4), Roles, responsibility.",
        "Summarization of Day: Discussion with management team / MR on the outcome of the day"
    ]
}

# Predefined Audit Types
predefined_audit_types = ["IA", "P1", "P2", "P3", "P4", "P5", "RC"]

# ---------------- INPUT GENERATOR ----------------
if app_mode == "Input Generator":
    st.header("Auditors Planning Schedule Input Generator")

    if st.session_state.schedule_generated:
        st.warning("Schedule has been generated. Editing is locked.")
    else:
        st.subheader("Step 1: Define Sites and Activities")
        num_sites = st.number_input("How many sites do you want to add?", min_value=1, step=1, value=1)

        site_activity_data = {}

        for s in range(num_sites):
            site = st.text_input(f"Enter Site Name {s+1}", key=f"site_{s}")
            if site:
                site_activity_data[site] = {}
                st.session_state.activity_status[site] = {}

                for category, activities in common_activities.items():
                    st.markdown(f"### {category} for {site}")
                    for activity in activities:
                        is_core = st.checkbox(f"Mark '{activity}' as Core", key=f"core_{site}_{activity}")
                        site_activity_data[site][activity] = "Core" if is_core else "Non-Core"
                        st.session_state.activity_status[site][activity] = "Available"

        site_audit_data = {}

        st.subheader("Step 2: Add Audits for Each Site")

        for site in site_activity_data.keys():
            st.markdown(f"## Site: {site}")

            audit_data = []
            num_audits = st.number_input(f"How many audits for {site}?", min_value=1, step=1, value=1, key=f"num_audits_{site}")

            for i in range(num_audits):
                st.markdown(f"### Audit {i+1} for {site}")
                audit_type = st.selectbox(f"Select Audit Type {i+1}", predefined_audit_types, key=f"audit_type_{site}_{i}")
                proposed_date = st.date_input(f"Proposed Date {i+1}", key=f"date_{site}_{i}")
                mandays = st.number_input(f"Mandays {i+1}", min_value=1, step=1, key=f"mandays_{site}_{i}")

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

        if st.button("Save Data for Scheduling"):
            st.session_state.audit_data = site_audit_data
            st.success("Data saved! You can now proceed to the Schedule Generator.")


# ---------------- SCHEDULE GENERATOR ----------------
if app_mode == "Schedule Generator":
    st.header("Schedule Generator")

    if not st.session_state.audit_data:
        st.warning("No data available. Please use the Input Generator to add data.")
    else:
        selected_site = st.selectbox("Select Site", list(st.session_state.audit_data.keys()))
        selected_audit_type = st.selectbox("Select Audit Type", predefined_audit_types)

        auditors = st.text_area("Enter Auditors' Names (One per line)").split('\n')
        coded_auditors = st.multiselect("Select Coded Auditors", auditors)

        if st.button("Generate Schedule"):
            schedule_data = []
            start_time = datetime.strptime('09:00', '%H:%M')
            lunch_start = datetime.strptime('13:00', '%H:%M')
            lunch_end = datetime.strptime('13:30', '%H:%M')
            end_time = datetime.strptime('18:00', '%H:%M')

            for audit in st.session_state.audit_data[selected_site]:
                if audit["Audit Type"] == selected_audit_type:
                    total_hours = audit["Total Hours"]
                    activities = [activity for activity, status in audit["Activities"].items() if status == "✔️"]
                    num_activities = len(activities)
                    time_per_activity = round(total_hours / num_activities, 2) if num_activities > 0 else 0

                    for activity in activities:
                        core_status = audit["Core Status"][activity]
                        if core_status == "Core":
                            allowed_auditors = coded_auditors
                        else:
                            allowed_auditors = auditors

                        assigned_auditor = st.selectbox(f"Assign Auditor for Activity: {activity}", allowed_auditors)
                        actual_time = st.number_input(f"Time Allocated for {activity} (in hours)", min_value=0.0, value=time_per_activity)

                        current_end_time = start_time + timedelta(hours=actual_time)
                        if start_time < lunch_start <= current_end_time:
                            schedule_data.append([
                                audit["Audit Type"],
                                selected_site,
                                "Lunch Break",
                                "N/A",
                                "N/A",
                                lunch_start.strftime('%H:%M'),
                                lunch_end.strftime('%H:%M')
                            ])
                            start_time = lunch_end
                            current_end_time = start_time + timedelta(hours=actual_time)

                        if current_end_time > end_time:
                            st.warning(f"Activity '{activity}' exceeds the end of the working day. Please adjust the allocated time.")

                        schedule_data.append([
                            audit["Audit Type"],
                            selected_site,
                            activity,
                            core_status,
                            assigned_auditor,
                            start_time.strftime('%H:%M'),
                            current_end_time.strftime('%H:%M')
                        ])

                        start_time = current_end_time

            df = pd.DataFrame(schedule_data, columns=["Audit Type", "Site", "Activity", "Core Status", "Assigned Auditor", "Start Time", "End Time"])

            st.write("### Generated Schedule")
            edited_df = st.experimental_data_editor(df, use_container_width=True)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                edited_df.to_excel(writer, sheet_name='Schedule', index=False)
            st.download_button("Download Schedule as Excel", data=output.getvalue(), file_name="Auditors_Planning_Schedule.xlsx")

        st.session_state.schedule_generated = True
























