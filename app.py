import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder

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
        st.warning("No audit data found. Please generate audit data in the Input Generator first.")
    else:
        schedule_data = []

        for site, audits in st.session_state.audit_data.items():
            for audit in audits:
                for activity, status in audit['Activities'].items():
                    if status == "✔️":
                        start_time = st.time_input(f"Start Time for {activity} ({site})", key=f"start_{site}_{activity}")
                        end_time = st.time_input(f"End Time for {activity} ({site})", key=f"end_{site}_{activity}")

                        available_auditors = st.session_state.coded_auditors if audit['Core Status'][activity] == "Core" else st.session_state.coded_auditors
                        selected_auditors = st.multiselect(f"Assign Auditors for {activity} ({site})", available_auditors, key=f"auditors_{site}_{activity}")

                        if selected_auditors:
                            for auditor in selected_auditors:
                                if auditor in st.session_state.auditor_assignments:
                                    for existing_start, existing_end in st.session_state.auditor_assignments[auditor]:
                                        if not (end_time <= existing_start or start_time >= existing_end):
                                            st.warning(f"Time clash detected for {auditor} while assigning {activity} at {site}.")
                                            break

                                if auditor not in st.session_state.auditor_assignments:
                                    st.session_state.auditor_assignments[auditor] = []

                                st.session_state.auditor_assignments[auditor].append((start_time, end_time))

                        schedule_data.append({
                            "Site": site,
                            "Audit Type": audit['Audit Type'],
                            "Proposed Date": audit['Proposed Date'],
                            "Activity": activity,
                            "Start Time": start_time.strftime("%H:%M"),
                            "End Time": end_time.strftime("%H:%M"),
                            "Assigned Auditors": ", ".join(selected_auditors)
                        })

        if schedule_data:
            schedule_df = pd.DataFrame(schedule_data)
            st.dataframe(schedule_df)

            # Downloadable Excel file
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                schedule_df.to_excel(writer, index=False, sheet_name='Audit Schedule')

                # Create a pivot table
                workbook = writer.book
                worksheet = writer.sheets['Audit Schedule']

                pivot_worksheet = workbook.add_worksheet('Pivot Table')
                pivot_table = workbook.add_pivot_table(
                    name='PivotTable1',
                    source_data=f"'Audit Schedule'!A1:G{len(schedule_df) + 1}",
                    destination='A1'
                )
                pivot_worksheet.add_table(0, 0, len(schedule_df), 6, {'columns': schedule_df.columns.tolist()})

            output.seek(0)

            st.download_button(
                label="Download Schedule as Excel",
                data=output,
                file_name="Audit_Schedule.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.session_state.schedule_generated = True
