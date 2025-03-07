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

# ---------------- INPUT GENERATOR ----------------
if app_mode == "Input Generator":
    st.header("Auditors Planning Schedule Input Generator")

    # Step 1: Define Sites and Activities
    st.subheader("Step 1: Define Sites and Activities")
    num_sites = st.number_input("How many sites do you want to add?", min_value=1, step=1, value=1)

    site_activity_data = {}  # Store activities and core status for each site

    for s in range(num_sites):
        site = st.text_input(f"Enter Site Name {s+1}", key=f"site_{s}")
        if site:
            activity_input = st.text_area(f"Enter activities for {site} (comma-separated)", key=f"activity_list_{s}")
            activity_list = [activity.strip() for activity in activity_input.split(",") if activity.strip()]

            activity_core_status = {}
            for activity in activity_list:
                is_core = st.checkbox(f"Mark '{activity}' as Core for {site}", key=f"core_{site}_{activity}")
                activity_core_status[activity] = "Core" if is_core else "Non-Core"

            site_activity_data[site] = activity_core_status

    # Initialize dictionary to store site-wise audit data
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
                audit_entry[f"{activity} (Core Status)"] = activity_details[activity]

            audit_data.append(audit_entry)

        # Store data for this site
        site_audit_data[site] = pd.DataFrame(audit_data)

    # Store the input data in session state for direct use in schedule generator
    if st.button("Save Data for Scheduling"):
        st.session_state.audit_data = site_audit_data
        st.success("Data saved! You can now proceed to the Schedule Generator.")



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

        # Define auditor availability
        num_auditors = st.number_input("Number of Auditors", min_value=1, step=1)
        auditors = {}
        for i in range(num_auditors):
            name = st.text_input(f"Auditor {i+1} Name")
            coded = st.checkbox(f"Is {name} a Coded Auditor?")
            mandays = st.number_input(f"{name}'s Availability (Mandays)", min_value=1, step=1)
            auditors[name] = {"coded": coded, "mandays": mandays}

        # Define schedule structure
        schedule_data = []

        # Time slots
        start_time = datetime.strptime("09:00", "%H:%M")
        lunch_start = datetime.strptime("13:00", "%H:%M")
        lunch_end = datetime.strptime("13:30", "%H:%M")
        current_date = datetime.today().date()

        for site in site_names:
            df = site_audit_data[site].copy()

            for _, row in df.iterrows():
                for activity in df.columns:
                    if "(Core Status)" in activity or row[activity] != "✔️":
                        continue  # Skip non-selected activities

                    is_core = row[f"{activity} (Core Status)"] == "Core"
                    available_auditors = [a for a in auditors if (not is_core) or auditors[a]["coded"]]

                    if not available_auditors:
                        continue  # Skip if no auditors are available

                    assigned_auditor = available_auditors[0]  # Assign first available
                    end_time = start_time + timedelta(hours=3)

                    # Ensure lunch break
                    if start_time < lunch_start and end_time > lunch_start:
                        schedule_data.append([current_date, "13:00 - 13:30", "Lunch Break", ""])
                        start_time = lunch_end
                        end_time = start_time + timedelta(hours=3)

                    # Store schedule data in tabular format
                    schedule_data.append([current_date, f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}", activity, assigned_auditor])
                    
                    # Move time forward
                    start_time = end_time

                    # Move to next day if required
                    if start_time.hour >= 17:
                        current_date += timedelta(days=1)
                        start_time = datetime.strptime("09:00", "%H:%M")

        # Convert schedule data to DataFrame
        schedule_df = pd.DataFrame(schedule_data, columns=["Date", "Time of the Activity", "Name of the Activity", "Auditor Assigned"])

        # Display schedule with edit option
        st.subheader("Generated Schedule")
        edited_schedule = st.data_editor(schedule_df, num_rows="dynamic")

        # Save to Excel
        if st.button("Generate Schedule"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                edited_schedule.to_excel(writer, sheet_name="Schedule", index=False)

            st.success("Schedule file created successfully!")
            st.download_button(
                label="Download Schedule File",
                data=output.getvalue(),
                file_name="Audit_Schedule.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
