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
if "auditor_info" not in st.session_state:
    st.session_state.auditor_info = {}

# ---------------- INPUT GENERATOR ----------------
if app_mode == "Input Generator":
    st.header("Auditors Planning Schedule Input Generator")

    # Step 1: Define Auditors
    st.subheader("Step 1: Define Auditors")
    num_auditors = st.number_input("Number of Auditors", min_value=1, step=1, value=1)
    auditors = {}
    for i in range(num_auditors):
        name = st.text_input(f"Auditor {i+1} Name", key=f"auditor_{i}")
        coded = st.checkbox(f"Is {name} a Coded Auditor?", key=f"coded_{i}")
        auditors[name] = {"coded": coded}
    st.session_state.auditor_info = auditors

    # Step 2: Define Audits
    st.subheader("Step 2: Define Audits")
    num_audits = st.number_input("How many audits to plan?", min_value=1, step=1, value=1)
    audit_data = []
    for i in range(num_audits):
        audit_type = st.text_input(f"Audit Type {i+1}", key=f"audit_type_{i}")
        site = st.text_input(f"Site Name for Audit {i+1}", key=f"site_{i}")
        proposed_date = st.date_input(f"Proposed Date for Audit {i+1}", key=f"date_{i}")
        mandays = st.number_input(f"Mandays for Audit {i+1}", min_value=1, step=1, key=f"mandays_{i}")
        
        st.markdown("### Select Activities to be Audited")
        activity_data = {}
        num_activities = st.number_input(f"Number of Activities for {audit_type}", min_value=1, step=1, key=f"activities_{i}")
        for j in range(num_activities):
            activity = st.text_input(f"Activity {j+1}", key=f"activity_{i}_{j}")
            is_core = st.checkbox(f"Mark '{activity}' as Core", key=f"core_{i}_{j}")
            activity_data[activity] = "Core" if is_core else "Non-Core"
        
        audit_data.append({
            "Audit Type": audit_type,
            "Site": site,
            "Proposed Date": proposed_date.strftime("%Y-%m-%d"),
            "Mandays": mandays,
            "Activities": activity_data
        })
    
    if st.button("Save Audits"):
        st.session_state.audit_data = audit_data
        st.success("Audit Data Saved! Proceed to Schedule Generator.")

# ---------------- SCHEDULE GENERATOR ----------------
elif app_mode == "Schedule Generator":
    st.header("Schedule Generator")
    
    if not st.session_state.audit_data:
        st.warning("No audit data found! Please enter data in the 'Input Generator' section.")
    else:
        audit_data = st.session_state.audit_data
        auditors = st.session_state.auditor_info
        
        selected_audit = st.selectbox("Select an Audit to Plan", [f"{a['Audit Type']} - {a['Site']}" for a in audit_data])
        audit_info = next(a for a in audit_data if f"{a['Audit Type']} - {a['Site']}" == selected_audit)
        
        total_hours = audit_info["Mandays"] * 8
        activities = list(audit_info["Activities"].keys())
        hours_per_activity = total_hours // len(activities) if activities else 0
        
        schedule_data = []
        start_time = datetime.strptime("09:00", "%H:%M")
        lunch_start = datetime.strptime("13:00", "%H:%M")
        lunch_end = datetime.strptime("13:30", "%H:%M")
        current_date = datetime.today().date()
        work_hours = 0
        
        def assign_auditors(activity):
            is_core = audit_info["Activities"][activity] == "Core"
            return [a for a in auditors if not is_core or auditors[a]["coded"]]
        
        for activity in activities:
            available_auditors = assign_auditors(activity)
            
            duration = st.number_input(f"Enter hours for {activity}", min_value=1, max_value=8, step=1, key=f"duration_{activity}")
            assigned_auditors = st.multiselect(f"Select auditors for {activity}", list(auditors.keys()), default=available_auditors, key=f"auditors_{activity}")
            
            if not assigned_auditors:
                st.warning(f"No auditors assigned for {activity}. Please select at least one.")
                continue
            
            end_time = start_time + timedelta(hours=duration)
            if start_time < lunch_start and end_time > lunch_start:
                schedule_data.append([current_date, "13:00 - 13:30", "Lunch Break", ""])
                start_time = lunch_end
                end_time = start_time + timedelta(hours=duration)
            
            if work_hours + duration > 8:
                current_date += timedelta(days=1)
                start_time = datetime.strptime("09:00", "%H:%M")
                work_hours = 0
            
            schedule_data.append([
                current_date,
                f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                activity,
                ", ".join(assigned_auditors)
            ])
            
            start_time = end_time
            work_hours += duration
        
        schedule_df = pd.DataFrame(schedule_data, columns=["Date", "Time", "Activity", "Auditor Assigned"])
        edited_schedule = st.data_editor(schedule_df, num_rows="dynamic")
        
        if st.button("Generate Schedule"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                edited_schedule.to_excel(writer, sheet_name="Schedule", index=False)
            output.seek(0)
            st.download_button("Download Schedule File", output.getvalue(), "Audit_Schedule.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")



















