import streamlit as st
import pandas as pd
from io import BytesIO

# Streamlit App
st.title("Auditors Planning Schedule Input Generator")

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

# Step 3: Generate Excel File
if st.button("Generate Excel"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for site, df in site_audit_data.items():
            df.to_excel(writer, sheet_name=site[:31], index=False)  # Sheet names max 31 characters

    st.success("Excel file created successfully!")

    # Provide download button
    st.download_button(
        label="Download Excel File",
        data=output.getvalue(),
        file_name="Auditors_Planning_Schedule.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
























