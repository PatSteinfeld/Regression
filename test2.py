import streamlit as st
import pandas as pd
from io import BytesIO

# Streamlit App
st.title("Auditors Planning Schedule Input Generator")

# Step 1: Define Activities
st.subheader("Step 1: Define Activities")
activity_input = st.text_area("Enter all activities (comma-separated)", key="activity_list")
activity_list = [activity.strip() for activity in activity_input.split(",") if activity.strip()]

# Initialize a dictionary to store site-wise data
site_audit_data = {}

# Step 2: Define Sites and Add Audits
st.subheader("Step 2: Add Audits for Each Site")
num_sites = st.number_input("How many sites do you want to add?", min_value=1, step=1, value=1)

for s in range(num_sites):
    site = st.text_input(f"Enter Site Name {s+1}", key=f"site_{s}")
    
    if site:
        # Store audit details
        audit_data = []

        num_audits = st.number_input(f"How many audits for {site}?", min_value=1, step=1, value=1, key=f"num_audits_{s}")

        for i in range(num_audits):
            st.markdown(f"### Audit {i+1} for {site}")
            audit_type = st.text_input(f"Audit Type {i+1}", key=f"audit_type_{s}_{i}")
            proposed_date = st.date_input(f"Proposed Date {i+1}", key=f"date_{s}_{i}")
            mandays = st.number_input(f"Mandays {i+1}", min_value=1, step=1, key=f"mandays_{s}_{i}")

            # Activity selection checkboxes
            st.write(f"Select Activities for Audit {i+1}")
            selected_activities = {activity: st.checkbox(activity, key=f"{activity}_{s}_{i}") for activity in activity_list}

            # Store audit details
            audit_entry = {
                "Audit Type": audit_type,
                "Proposed Date": proposed_date.strftime("%Y-%m-%d"),
                "Mandays": mandays
            }

            # Mark selected activities
            for activity, selected in selected_activities.items():
                audit_entry[activity] = "✔️" if selected else "✖️"

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






















