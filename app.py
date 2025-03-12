import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from io import BytesIO
import uuid



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
if "schedule_data" not in st.session_state:
    st.session_state.schedule_data = pd.DataFrame()  # Initialize as an empty DataFrame


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
if "schedule_data" not in st.session_state:
    st.session_state.schedule_data = pd.DataFrame()
if "auditor_assignments" not in st.session_state:
    st.session_state.auditor_assignments = {}
if "auditors" not in st.session_state:
    st.session_state.auditors = []
if "schedule_generated" not in st.session_state:
    st.session_state.schedule_generated = False
if "auditor_selection" not in st.session_state:
    st.session_state.auditor_selection = {}

st.title("Audit Schedule Generator")

# Input auditors
st.session_state.auditors = st.text_area("Enter Auditors' Names (One per line)", key="auditors_input").split('\n')
coded_auditors = st.multiselect("Select Coded Auditors", st.session_state.auditors)

if st.button("Generate Schedule"):
    schedule_data = []
    start_time = datetime.strptime('09:00', '%H:%M')

    for i in range(5):  # Example with 5 activities
        activity_name = f"Activity {i+1}"
        core_status = "Core" if i % 2 == 0 else "Non-Core"
        allowed_auditors = coded_auditors if core_status == "Core" else st.session_state.auditors
        assigned_auditor = allowed_auditors[0] if allowed_auditors else "No Auditor"

        schedule_data.append([
            activity_name,
            core_status,
            start_time.strftime('%H:%M'),
            (start_time + timedelta(minutes=90)).strftime('%H:%M'),
            assigned_auditor
        ])

        start_time += timedelta(minutes=90)
        if start_time.strftime('%H:%M') == '13:00':  # Lunch break
            start_time += timedelta(minutes=30)

    st.session_state.schedule_data = pd.DataFrame(schedule_data, columns=["Activity", "Core Status", "Start Time", "End Time", "Assigned Auditor"])
    st.session_state.auditor_selection = {i: "None" for i in range(len(schedule_data))}

if not st.session_state.schedule_data.empty:
    st.write("### Editable Schedule")
    edited_schedule = st.session_state.schedule_data.copy()

    for index, row in edited_schedule.iterrows():
        st.write(f"### {row['Activity']}")

        start_time_input = st.text_input(f"Start Time for {row['Activity']}", value=row['Start Time'])
        if start_time_input:
            try:
                activity_start = datetime.strptime(start_time_input, '%H:%M')
                activity_hours = st.number_input(f"Enter Hours for '{row['Activity']}'", min_value=0.5, max_value=8.0, value=1.5, step=0.5)
                activity_end = activity_start + timedelta(hours=activity_hours)
                edited_schedule.at[index, 'Start Time'] = start_time_input
                edited_schedule.at[index, 'End Time'] = activity_end.strftime('%H:%M')
            except ValueError:
                st.warning("Invalid time format. Please use HH:MM.")

        assigned_auditor = st.selectbox(f"Assign Auditor for '{row['Activity']}'", 
                                        options=["None"] + st.session_state.auditors, 
                                        index=(st.session_state.auditors.index(st.session_state.auditor_selection.get(index, "None")) + 1 if st.session_state.auditor_selection.get(index, "None") != "None" else 0),
                                        key=f"auditor_{index}")
        
        if assigned_auditor != "None":
            st.session_state.auditor_selection[index] = assigned_auditor
            edited_schedule.at[index, 'Assigned Auditor'] = assigned_auditor
        else:
            st.session_state.auditor_selection[index] = "None"
    
    st.session_state.schedule_data = edited_schedule

    # Display the final table
    st.write("### Final Schedule Table")
    st.dataframe(st.session_state.schedule_data)

    # Download as Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state.schedule_data.to_excel(writer, sheet_name='Schedule', index=False)
    st.download_button("Download Schedule as Excel", data=output.getvalue(), file_name="Auditors_Planning_Schedule.xlsx")

