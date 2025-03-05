import streamlit as st
import pandas as pd
from io import BytesIO

st.title("🔹 Audit Input Generator")

# Step 1: Define Sites and Activities
st.subheader("Step 1: Define Sites and Activities")
num_sites = st.number_input("Number of sites:", min_value=1, step=1, value=1)

site_activity_data = {}

for s in range(num_sites):
    site = st.text_input(f"Enter Site Name {s+1}", key=f"site_{s}")
    if site:
        activities_input = st.text_area(f"Enter activities for {site} (comma-separated)", key=f"activities_{s}")
        activities_list = [a.strip() for a in activities_input.split(",") if a.strip()]

        activity_core_status = {}
        for activity in activities_list:
            is_core = st.checkbox(f"Mark '{activity}' as Core for {site}", key=f"core_{site}_{activity}")
            activity_core_status[activity] = "Core" if is_core else "Non-Core"

        site_activity_data[site] = activity_core_status

site_audit_data = {}

# Step 2: Add Audits for Each Site
st.subheader("Step 2: Define Audits")

for site, activity_details in site_activity_data.items():
    st.markdown(f"## Site: {site}")

    audit_data = []
    num_audits = st.number_input(f"Number of audits for {site}:", min_value=1, step=1, value=1, key=f"num_audits_{site}")

    for i in range(num_audits):
        st.markdown(f"### Audit {i+1} for {site}")
        audit_type = st.text_input(f"Audit Type {i+1}", key=f"audit_type_{site}_{i}")
        proposed_date = st.date_input(f"Proposed Date {i+1}", key=f"date_{site}_{i}")
        mandays = st.number_input(f"Mandays {i+1}", min_value=1, step=1, key=f"mandays_{site}_{i}")

        # Activity selection checkboxes
        selected_activities = {activity: st.checkbox(activity, key=f"{activity}_{site}_{i}") for activity in activity_details.keys()}

        audit_entry = {
            "Audit Type": audit_type,
            "Proposed Date": proposed_date.strftime("%Y-%m-%d"),
            "Mandays": mandays
        }

        for activity, selected in selected_activities.items():
            audit_entry[activity] = "✔️" if selected else "✖️"
            audit_entry[f"{activity} (Core Status)"] = activity_details[activity]

        audit_data.append(audit_entry)

    site_audit_data[site] = pd.DataFrame(audit_data)

# Step 3: Generate Excel File
if st.button("Generate Input File"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for site, df in site_audit_data.items():
            df.to_excel(writer, sheet_name=site[:31], index=False)

    st.success("Input file created successfully!")
    st.download_button(
        label="Download Input File",
        data=output.getvalue(),
        file_name="Audit_Input_File.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
