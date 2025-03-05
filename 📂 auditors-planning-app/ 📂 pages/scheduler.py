import streamlit as st
import pandas as pd

st.title("📅 Audit Schedule Generator")

# Upload Input File
uploaded_file = st.file_uploader("Upload the generated input file:", type=["xlsx"])

if uploaded_file:
    # Read the Excel file
    xls = pd.ExcelFile(uploaded_file)

    # User Inputs for Auditor Availability
    st.subheader("Step 1: Define Auditor Availability")
    num_auditors = st.number_input("Number of auditors:", min_value=1, step=1, value=1)

    auditors = {}
    for i in range(num_auditors):
        auditor_name = st.text_input(f"Auditor {i+1} Name", key=f"auditor_{i}")
        is_coded = st.checkbox(f"{auditor_name} is a coded auditor?", key=f"coded_{i}")
        available_mandays = st.number_input(f"{auditor_name}'s Available Mandays", min_value=1, step=1, key=f"days_{i}")
        auditors[auditor_name] = {"coded": is_coded, "available_mandays": available_mandays}

    # Step 2: Generate Schedule
    if st.button("Generate Schedule"):
        schedule_data = []

        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)

            for _, row in df.iterrows():
                audit_type = row["Audit Type"]
                proposed_date = row["Proposed Date"]
                mandays = row["Mandays"]

                assigned_auditors = []
                remaining_hours = mandays * 8  # Each manday = 8 hours

                for activity in row.keys():
                    if "(Core Status)" in activity:
                        continue

                    if row[activity] == "✔️":
                        core_status = row[f"{activity} (Core Status)"]
                        possible_auditors = [
                            name for name, details in auditors.items()
                            if (core_status == "Core" and details["coded"]) or core_status == "Non-Core"
                        ]

                        if possible_auditors:
                            assigned_auditor = possible_auditors[0]
                            assigned_auditors.append((activity, assigned_auditor))
                            auditors[assigned_auditor]["available_mandays"] -= 1
                            remaining_hours -= 8

                schedule_data.append({
                    "Site": sheet_name,
                    "Audit Type": audit_type,
                    "Date": proposed_date,
                    "Assigned Auditors": ", ".join(f"{a}: {aud}" for a, aud in assigned_auditors)
                })

        schedule_df = pd.DataFrame(schedule_data)

        st.write("### Generated Schedule")
        st.dataframe(schedule_df)

        # Download Schedule
        schedule_output = BytesIO()
        with pd.ExcelWriter(schedule_output, engine="xlsxwriter") as writer:
            schedule_df.to_excel(writer, sheet_name="Schedule", index=False)

        st.download_button(
            label="Download Schedule",
            data=schedule_output.getvalue(),
            file_name="Audit_Schedule.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
