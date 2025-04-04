import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import xlsxwriter

# Initialize session state
def initialize_session_state():
    if "audit_data" not in st.session_state:
        st.session_state.audit_data = {}
    if "schedule_data" not in st.session_state:
        st.session_state.schedule_data = pd.DataFrame(columns=[
            "Site", "Activity", "Core Status", "Proposed Date", "Start Time", "End Time", "Assigned Auditor", "Allowed Auditors"
        ])
    if "assigned_auditors" not in st.session_state:
        st.session_state.assigned_auditors = {}

def define_common_activities():
    return {
        "Meeting & Management": [
            "Opening meeting with top management",
            "Top management focus area: Context of Organization",
            "Management Representative focus area",
            "HR / Training: Roles, responsibility & authority",
            "Purchase / Procurement / Supply chain process",
            "Stores including scrap yard: Resource, competence, awareness"
        ],
        "Maintenance Activities": [
            "Mechanical Maintenance process",
            "Electrical Maintenance process",
            "Instrumentation Maintenance process",
            "Civil Maintenance process",
            "Utilities process",
            "Summarization of Day"
        ]
    }

def input_generator():
    st.header("Auditors Planning Schedule Input Generator")
    common_activities = define_common_activities()
    num_sites = st.number_input("Number of sites to add", min_value=1, step=1, value=1)

    site_activity_data = {}

    for s in range(num_sites):
        site = st.text_input(f"Enter Site Name {s+1}", key=f"site_{s}")
        if site:
            site_activity_data[site] = {}
            for category, activities in common_activities.items():
                st.markdown(f"### {category} for {site}")
                for activity in activities:
                    is_core = st.checkbox(f"Mark '{activity}' as Core", key=f"core_{site}_{activity}")
                    site_activity_data[site][activity] = "Core" if is_core else "Non-Core"

    site_audit_data = {}

    for site in site_activity_data.keys():
        st.markdown(f"## Site: {site}")
        num_audits = st.number_input(f"Number of audits for {site}", min_value=1, step=1, value=1, key=f"num_audits_{site}")
        audit_data = []
        for i in range(num_audits):
            audit_type = st.selectbox(f"Select Audit Type {i+1}", ["IA", "P1", "P2", "P3", "P4", "P5", "RC"], key=f"audit_type_{site}_{i}")
            proposed_date = st.date_input(f"Proposed Date {i+1}", key=f"date_{site}_{i}")
            mandays = st.number_input(f"Mandays {i+1}", min_value=1, step=1, key=f"mandays_{site}_{i}")
            selected_activities = {activity: st.checkbox(activity, key=f"{activity}_{site}_{i}") for activity in site_activity_data[site].keys()}
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
        st.success("Data saved! Proceed to the Schedule Generator.")

def schedule_generator():
    st.header("📆 Audit Schedule Generator & Excel Export")

    if not st.session_state.audit_data:
        st.warning("No data available. Please use the Input Generator first.")
        return

    auditors = st.text_area("Enter Auditors' Names (One per line)").split('\n')
    auditors = [auditor.strip() for auditor in auditors if auditor.strip()]

    if not auditors:
        st.warning("Please enter at least one auditor.")
        return

    coded_auditors = st.multiselect("Select Coded Auditors", auditors)

    if st.button("Generate and Export Schedule to Excel"):
        sitewise_dfs = {}
        for site, audits in st.session_state.audit_data.items():
            schedule_data = []
            start_time = datetime.strptime('09:00', '%H:%M')

            for audit in audits:
                activities = [activity for activity, status in audit["Activities"].items() if status == "✔️"]
                for activity in activities:
                    core_status = audit["Core Status"].get(activity, "Non-Core")
                    allowed_auditors = coded_auditors if core_status == "Core" else auditors
                    assigned_auditor = allowed_auditors[0] if allowed_auditors else ""

                    schedule_data.append({
                        "Site": site,
                        "Activity": activity,
                        "Core Status": core_status,
                        "Proposed Date": audit["Proposed Date"],
                        "Start Time": start_time.strftime('%H:%M'),
                        "End Time": (start_time + timedelta(minutes=90)).strftime('%H:%M'),
                        "Assigned Auditor": assigned_auditor,
                        "Allowed Auditors": ", ".join(allowed_auditors)
                    })

                    start_time += timedelta(minutes=90)
                    if start_time.strftime('%H:%M') == '13:00':
                        start_time += timedelta(minutes=30)

            sitewise_dfs[site] = pd.DataFrame(schedule_data)

        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for site, df in sitewise_dfs.items():
                df.to_excel(writer, index=False, sheet_name=site[:31])

        st.download_button(
            label="📥 Download Schedule Excel File",
            data=output.getvalue(),
            file_name="Audit_Schedule.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

initialize_session_state()
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a section:", ["Input Generator", "Schedule Generator"])

if app_mode == "Input Generator":
    input_generator()
else:
    schedule_generator()











