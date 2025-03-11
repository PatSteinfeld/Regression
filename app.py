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

if "auditor_assignments" not in st.session_state:
    st.session_state.auditor_assignments = {}

if "coded_auditors" not in st.session_state:
    st.session_state.coded_auditors = []

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

























