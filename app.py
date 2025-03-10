import streamlit as st
import pandas as pd
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

import streamlit as st
import pandas as pd

# Predefined activities with descriptions
predefined_activities = {
    "Opening meeting": "With top management to explain the scope of the audit, audit methodology, and reporting.",
    "Top management": "Focus Area - Context of Organization.",
    "Management Representative": "Focus Area.",
    "HR / Training": "Roles, responsibility & authority (5).",
    "Purchase / Procurement / Supply chain": "Process (4.4), Roles, responsibility & authority.",
    "Stores including scrap yard": "Roles, responsibility & authority (5.3), Resource, competence, awareness.",
    "Mechanical Maintenance": "Determining process (4.4), Roles, responsibility.",
    "Electrical Maintenance": "Determining process (4.4), Roles.",
    "Instrumentation Maintenance": "Determining process (4.4), Roles.",
    "Civil Maintenance": "Determining process (4.4).",
    "Utilities": "Determining process (4.4), Roles, responsibility.",
    "Summarization of Day": "Discussion with management team / MR on the outcome of the day."
}

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
            # Predefined activities selection
            st.markdown("**Select predefined activities for this site:**")
            selected_predefined = {
                activity: st.checkbox(f"{activity} - {desc}", key=f"predef_{site}_{activity}")
                for activity, desc in predefined_activities.items()
            }
            
            # Custom activities input
            activity_input = st.text_area(f"Enter additional activities for {site} (comma-separated)", key=f"activity_list_{s}")
            custom_activities = [activity.strip() for activity in activity_input.split(",") if activity.strip()]
            
            # Merge selected predefined and custom activities
            activity_core_status = {}
            for activity, selected in selected_predefined.items():
                if selected:
                    activity_core_status[activity] = (predefined_activities[activity], "Core")
            for activity in custom_activities:
                is_core = st.checkbox(f"Mark '{activity}' as Core for {site}", key=f"core_{site}_{activity}")
                activity_core_status[activity] = ("Custom Activity", "Core" if is_core else "Non-Core")

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
                "Mandays": mandays
            }

            # Mark selected activities and include core status
            for activity, selected in selected_activities.items():
                audit_entry[activity] = "✔️" if selected else "✖️"
                audit_entry[f"{activity} (Description)"] = activity_details[activity][0]
                audit_entry[f"{activity} (Core Status)"] = activity_details[activity][1]

            audit_data.append(audit_entry)

        # Store data for this site
        site_audit_data[site] = pd.DataFrame(audit_data)

    # Store the input data in session state for direct use in schedule generator
    if st.button("Save Data for Scheduling"):
        st.session_state.audit_data = site_audit_data
        st.success("Data saved! You can now proceed to the Schedule Generator.")





# ---------------- SCHEDULE GENERATOR ----------------
# ---------------- SCHEDULE GENERATOR ----------------
elif app_mode == "Schedule Generator":
    st.header("Schedule Generator")

    # Check if data is available from Input Generator
    if not st.session_state.audit_data:
        st.warning("No input data found! Please first enter data in the 'Input Generator' section.")
    else:
        # Load stored data
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

        # Select Audit & Site
        selected_audit = st.selectbox("Select Audit to Plan", list(site_audit_data[selected_site].keys()))
        
        # Load Audit Data
        df = site_audit_data[selected_site][selected_audit].copy()
        available_activities = [activity for activity in df.columns if "(Core Status)" not in activity and df.iloc[0][activity] == "✔️"]
        
        # Define Mandays & Work Hours
        mandays = st.number_input("Enter Number of Mandays", min_value=1, step=1)
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
            is_core = df.loc[0, f"{activity} (Core Status)"] == "Core" if f"{activity} (Core Status)" in df else False
            return [a for a in auditors if not is_core or auditors[a]["coded"]]

        # Opening Meeting
        schedule_data.append([current_date, "09:00 - 10:00", "Opening Meeting", ", ".join(auditor_names)])
        start_time += timedelta(hours=1)
        work_hours += 1

        # Auto-Schedule Activities
        for activity in available_activities:
            available_auditors = assign_auditors(activity)
            if not available_auditors:
                continue
            
            end_time = start_time + timedelta(hours=hours_per_activity)
            
            if start_time < lunch_start and end_time > lunch_start:
                schedule_data.append([current_date, "13:00 - 13:30", "Lunch Break", ""])
                start_time = lunch_end
                end_time = start_time + timedelta(hours=hours_per_activity)
            
            if work_hours + hours_per_activity > 8:
                current_date += timedelta(days=1)
                start_time = datetime.strptime("09:00", "%H:%M")
                work_hours = 0
            
            schedule_data.append([
                current_date,
                f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                activity,
                ", ".join(available_auditors)
            ])
            
            start_time = end_time
            work_hours += hours_per_activity

        # Closing Meeting
        schedule_data.append([current_date, f"{start_time.strftime('%H:%M')} - {(start_time + timedelta(hours=1)).strftime('%H:%M')}", "Closing Meeting", ", ".join(auditor_names)])

        # Convert to DataFrame
        schedule_df = pd.DataFrame(schedule_data, columns=["Date", "Time", "Activity", "Auditor Assigned"])

        # Editable Schedule Table
        edited_schedule = st.data_editor(schedule_df, num_rows="dynamic")

        # Export to Excel
        if st.button("Generate Schedule"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                edited_schedule.to_excel(writer, sheet_name="Schedule", index=False)
            st.success("Schedule file created successfully!")
            st.download_button("Download Schedule File", output.getvalue(), "Audit_Schedule.xlsx", "app












