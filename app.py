import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from streamlit_calendar import calendar

# Initialize session state
def initialize_session_state():
    if "audit_data" not in st.session_state:
        st.session_state.audit_data = {}
    if "schedule_data" not in st.session_state:
        st.session_state.schedule_data = {}
    if "assigned_auditors" not in st.session_state:
        st.session_state.assigned_auditors = {}

# Define common activities
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

# Input generator
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

# Schedule generator with interactive calendar
def schedule_generator():
    st.header("Schedule Generator")
    if not st.session_state.audit_data:
        st.warning("No data available. Please use the Input Generator first.")
        return
    
    selected_site = st.selectbox("Select Site", list(st.session_state.audit_data.keys()))
    selected_audit_type = st.selectbox("Select Audit Type", ["IA", "P1", "P2", "P3", "P4", "P5", "RC"])
    
    auditors = st.multiselect("Select Available Auditors", ["Alice", "Bob", "Charlie", "David", "Eve"])
    if not auditors:
        st.warning("Please select at least one auditor.")
        return
    
    coded_auditors = st.multiselect("Select Coded Auditors (For Core Activities)", auditors)
    
    if st.button("Generate Schedule"):
        schedule_data = []
        start_time = datetime.strptime('09:00', '%H:%M')

        for audit in st.session_state.audit_data[selected_site]:
            if audit["Audit Type"] == selected_audit_type:
                activities = [activity for activity, status in audit["Activities"].items() if status == "✔️"]
                for activity in activities:
                    core_status = audit["Core Status"].get(activity, "Non-Core")
                    allowed_auditors = coded_auditors if core_status == "Core" else auditors
                    
                    assigned_auditor = st.session_state.assigned_auditors.get(activity, "")

                    schedule_data.append({
                        "Activity": activity,
                        "Core Status": core_status,
                        "Start Time": start_time.strftime('%H:%M'),
                        "End Time": (start_time + timedelta(minutes=90)).strftime('%H:%M'),
                        "Assigned Auditor": assigned_auditor,
                        "Allowed Auditors": json.dumps(allowed_auditors)
                    })

                    start_time += timedelta(minutes=90)
                    if start_time.strftime('%H:%M') == '13:00':
                        start_time += timedelta(minutes=30)

        st.session_state.schedule_data[selected_site] = pd.DataFrame(schedule_data)

    if selected_site in st.session_state.schedule_data and not st.session_state.schedule_data[selected_site].empty:
        st.write("### 📝 Modify Assigned Auditors")

        gb = GridOptionsBuilder.from_dataframe(st.session_state.schedule_data[selected_site])
        gb.configure_column("Assigned Auditor", editable=True, cellEditor="agSelectCellEditor", 
                            cellEditorParams={"values": auditors})
        grid_response = AgGrid(st.session_state.schedule_data[selected_site], gridOptions=gb.build(), height=400, update_mode=GridUpdateMode.VALUE_CHANGED)
        
        updated_data = grid_response["data"]
        for _, row in updated_data.iterrows():
            st.session_state.assigned_auditors[row["Activity"]] = row["Assigned Auditor"]

        # Convert schedule to calendar format
        events = []
        for _, row in st.session_state.schedule_data[selected_site].iterrows():
            events.append({
                "title": f"{row['Activity']} - {row['Assigned Auditor']}",
                "start": f"2025-04-10T{row['Start Time']}:00",
                "end": f"2025-04-10T{row['End Time']}:00"
            })

        st.write("### 📅 Audit Schedule Calendar")
        calendar(events=events, options={"editable": True, "selectable": True})

        # Download Excel button
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            st.session_state.schedule_data[selected_site].to_excel(writer, index=False, sheet_name="Schedule")
        output.seek(0)
        
        st.download_button("📥 Download Schedule", output, file_name=f"{selected_site}_audit_schedule.xlsx", mime="application/vnd.ms-excel")

# Run app
initialize_session_state()
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a section:", ["Input Generator", "Schedule Generator"])

if app_mode == "Input Generator":
    input_generator()
else:
    schedule_generator()









