import streamlit as st
import pandas as pd
from io import BytesIO

# Streamlit App
st.title("Auditors Planning Schedule Input Generator")

# Step 1: Define Activities
st.subheader("Step 1: Define Activities for the Site")
activity_input = st.text_area("Enter all activities (comma-separated)", key="activity_list")
activity_list = [activity.strip() for activity in activity_input.split(",") if activity.strip()]

# Step 2: Select Site
st.subheader("Step 2: Select Site")
site = st.selectbox("Select Site", ["Site A", "Site B", "Site C", "Site D"])

# Store audit details
audit_data = []

# Step 3: Add Audit Details
st.subheader("Step 3: Add Audit Details")
num_audits = st.number_input("How many audits do you want to add?", min_value=1, step=1, value=1)

for i in range(num_audits):
    st.markdown(f"### Audit {i+1}")
    audit_type = st.text_input(f"Audit Type {i+1}", key=f"audit_type_{i}")
    proposed_date = st.date_input(f"Proposed Date {i+1}", key=f"date_{i}")
    mandays = st.number_input(f"Mandays {i+1}", min_value=1, step=1, key=f"mandays_{i}")

    # Activity selection checkboxes
    st.write(f"Select Activities for Audit {i+1}")
    selected_activities = {activity: st.checkbox(activity, key=f"{activity}_{i}") for activity in activity_list}

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

# Convert data to DataFrame
df = pd.DataFrame(audit_data)

# Step 4: Generate Excel File
if st.button("Generate Excel"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name=site, index=False)

    st.success("Excel file created successfully!")

    # Provide download button
    st.download_button(
        label="Download Excel File",
        data=output.getvalue(),
        file_name="Auditors_Planning_Schedule.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )






















