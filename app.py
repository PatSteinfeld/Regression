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

# ---------------- INPUT GENERATOR ----------------
if app_mode == "Input Generator":
    st.header("Auditors Planning Schedule Input Generator")

    # Step 1: Define Sites and Activities
    st.subheader("Step 1: Define Sites and Activities")
    num_sites = st.number_input("How many sites do you want to add?", min_value=1, step=1, value=1)

    site_activity_data = {}

    for s in range(num_sites):
        site = st.text_input(f"Enter Site Name {s+1}", key=f"site_{s}")
        if site:
            # Custom activities input
            activity_input = st.text_area(f"Enter activities for {site} (comma-separated)", key=f"activity_list_{s}")
            activities = [activity.strip() for activity in activity_input.split(",") if activity.strip()]

            # Mark core activities
            activity_core_status = {}
            for activity in activities:
                is_core = st.checkbox(f"Mark '{activity}' as Core for {site}", key=f"core_{site}_{activity}")
                activity_core_status[activity] = "Core" if is_core else "Non-Core"

            site_activity_data[site] = activity_core_status

    site_audit_data = {}

    # Step 2: Add Audits for Each Site
    st.subheader("Step 2: Add Audits for Each Site")

    for site, activity_details in site_activity_data.items():
        st.markdown(f"## Site: {site}")

        audit_data = []
        num_audits = st.number_input(f"How many audits for {site}?", min_value=1, step=1, value=1, key=f"num_audits_{site}")

        for i in range(num_audits):
            st.markdown(f"### Audit {i+1} for {site}")
            audit_type = st.text_input(f"Audit Type {i+1}", key=f"audit_type_{site}_{i}")
            proposed_date = st.date_input(f"Proposed Date {i+1}", key=f"date_{site}_{i}")
            mandays = st.number_input(f"Mandays {i+1}", min_value=1, step=1, key=f"mandays_{site}_{i}")

            # Activity selection checkboxes
            st.write(f"Select Activities for Audit {i+1}")
            selected_activities = {activity: st.checkbox(activity, key=f"{activity}_{site}_{i}") for activity in activity_details.keys()}

            # Store audit details
            audit_entry = {
                "Audit Type": audit_type,
                "Proposed Date": proposed_date.strftime("%Y-%m-%d"),
                "Mandays": mandays,
                "Activities": {activity: "✔️" if selected else "✖️" for activity, selected in selected_activities.items()},
                "Core Status": {activity: activity_details[activity] for activity in selected_activities}
            }

            audit_data.append(audit_entry)

        # Store data for this site
        site_audit_data[site] = audit_data

    # Store input data in session state
    if st.button("Save Data for Scheduling"):
        st.session_state.audit_data = site_audit_data
        st.success("Data saved! You can now proceed to the Schedule Generator.")

# ---------------- SCHEDULE GENERATOR ----------------
elif app_mode == "Schedule Generator":
    st.header("Schedule Generator")

    # Check if data is available
    if not st.session_state.audit_data:
        st.warning("No input data found! Please first enter data in the 'Input Generator' section.")
    else:
        site_audit_data = st.session_state.audit_data
        site_names = list(site_audit_data.keys())
        selected_site = st.selectbox("Select Site for Scheduling", site_names)

        # Define auditor availability
        num_auditors = st.number_input("Number of Auditors", min_value=1, step=1)
        auditors = {}
        auditor_names = []
        for i in range(num_auditors):
            name = st.text_input(f"Auditor {i+1} Name", key=f"auditor_{i}")
            coded = st.checkbox(f"Is {name} a Coded Auditor?", key=f"coded_{i}")
            auditors[name] = {"coded": coded}
            auditor_names.append(name)

        # Select audit for scheduling
        audits = site_audit_data[selected_site]
        audit_options = [f"{audit['Audit Type']} ({audit['Proposed Date']})" for audit in audits]
        selected_audit_index = st.selectbox("Select Audit to Schedule", range(len(audit_options)), format_func=lambda x: audit_options[x])
        selected_audit = audits[selected_audit_index]

        # Get selected activities
        available_activities = [act for act, val in selected_audit["Activities"].items() if val == "✔️"]
        st.write("Available Activities:", available_activities)

        # Define Mandays & Work Hours
        mandays = selected_audit["Mandays"]
        total_hours = mandays * 8
        num_activities = len(available_activities)
        hours_per_activity = total_hours // num_activities if num_activities else 0

        # Schedule Initialization
        schedule_data = []
        start_time = datetime.strptime("09:00", "%H:%M")
        lunch_start = datetime.strptime("13:00", "%H:%M")
        lunch_end = datetime.strptime("13:30", "%H:%M")
        current_date = datetime.today().date()
        work_hours = 0

        def assign_auditors(activity):
            is_core = selected_audit["Core Status"].get(activity, "Non-Core") == "Core"
            return [a for a in auditors if not is_core or auditors[a]["coded"]]

        # Auto-Schedule Activities
        for activity in available_activities:
            available_auditors = assign_auditors(activity)
            if not available_auditors:
                continue

            duration = st.number_input(f"Enter hours for {activity}", min_value=1, max_value=8, step=1, key=f"duration_{activity}")
            assigned_auditors = st.multiselect(f"Select auditors for {activity}", auditor_names, default=available_auditors, key=f"auditors_{activity}")

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

            schedule_data.append([current_date, f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}", activity, ", ".join(assigned_auditors)])
            start_time = end_time
            work_hours += duration

        # Convert to DataFrame
        schedule_df = pd.DataFrame(schedule_data, columns=["Date", "Time", "Activity", "Auditor Assigned"])

        # Editable Table
        edited_schedule = st.data_editor(schedule_df, num_rows="dynamic")

        # Export to Excel
        if st.button("Generate Schedule"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                edited_schedule.to_excel(writer, sheet_name="Schedule", index=False)
            st.download_button("Download Schedule File", output.getvalue(), "Audit_Schedule.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")




















