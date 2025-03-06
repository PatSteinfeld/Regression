import streamlit as st
import pandas as pd
from datetime import datetime


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

    if not st.session_state.audit_data:
        st.warning("No input data found! Please first enter data in the 'Input Generator' section.")
    else:
        site_audit_data = st.session_state.audit_data
        site_names = list(site_audit_data.keys())

        st.subheader("Step 1: Select Site and Define Auditors")
        selected_site = st.selectbox("Select a site:", site_names)

        if selected_site:
            df = site_audit_data[selected_site]

            # Step 2: Define Available Auditors
            num_auditors = st.number_input("Enter number of auditors:", min_value=1, step=1, value=1)
            auditors = {}
            for i in range(num_auditors):
                name = st.text_input(f"Auditor {i+1} Name:", key=f"auditor_{i}")
                mandays = st.number_input(f"Mandays available for {name}:", min_value=1, step=1, key=f"mandays_{i}")
                if name:
                    auditors[name] = mandays * 8  # Convert mandays to hours

            # Step 3: Generate Schedule
            if st.button("Generate Schedule"):
                schedule = []
                start_time = datetime.strptime("09:00", "%H:%M")
                lunch_start = datetime.strptime("13:00", "%H:%M")
                lunch_end = datetime.strptime("13:30", "%H:%M")

                for _, row in df.iterrows():
                    audit_type = row["Audit Type"]
                    mandays = row["Mandays"]
                    total_hours = mandays * 8
                    activities = [col for col in df.columns if row[col] == "✔️"]

                    if activities:
                        activity_hours = min(total_hours / len(activities), 3)

                        for activity in activities:
                            if start_time >= lunch_start and start_time < lunch_end:
                                schedule.append(["Lunch Break", lunch_start.strftime("%I:%M %p"), lunch_end.strftime("%I:%M %p"), "—"])
                                start_time = lunch_end

                            end_time = start_time + timedelta(hours=activity_hours)
                            available_auditors = list(auditors.keys())

                            selected_auditors = st.multiselect(
                                f"Select auditor(s) for {audit_type} - {activity}",
                                available_auditors,
                                key=f"{audit_type}_{activity}"
                            )

                            schedule.append([audit_type, activity, start_time.strftime("%I:%M %p"), end_time.strftime("%I:%M %p"), ", ".join(selected_auditors)])
                            start_time = end_time

                # Display & Download Schedule
                st.subheader("Generated Audit Schedule")
                schedule_df = pd.DataFrame(schedule, columns=["Audit Type", "Activity", "Start Time", "End Time", "Auditor(s)"])
                st.write(schedule_df)

                st.download_button(
                    label="Download Schedule as Excel",
                    data=schedule_df.to_csv(index=False).encode(),
                    file_name="Audit_Schedule.csv",
                    mime="text/csv"
                )
