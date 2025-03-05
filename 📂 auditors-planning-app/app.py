import streamlit as st
import pandas as pd
import datetime

# App Title
st.title("Auditors Planning Schedule")

# Sidebar Navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a section:", ["Input Generator", "Schedule Generator"])

# ---------------- INPUT GENERATOR ----------------
if app_mode == "Input Generator":
    st.header("Input Generator")
    
    # Get site names
    site_names = st.text_area("Enter Site Names (comma-separated):").split(',')

    # Dictionary to store site data
    site_data = {}

    for site in site_names:
        site = site.strip()
        if site:
            st.subheader(f"Site: {site}")

            # Get activity names
            activities = st.text_area(f"Enter Activities for {site} (comma-separated):").split(',')
            
            # Mark core activities
            core_activities = st.multiselect(f"Select Core Activities for {site}", activities)

            # Store site data
            site_data[site] = {"activities": activities, "core_activities": core_activities}

    # Save to Excel
    if st.button("Generate Input File"):
        with pd.ExcelWriter("Audit_Input.xlsx") as writer:
            for site, data in site_data.items():
                df = pd.DataFrame({"Activity": data["activities"], "Core": [act in data["core_activities"] for act in data["activities"]]})
                df.to_excel(writer, sheet_name=site, index=False)

        st.success("Excel File Created: Audit_Input.xlsx")

# ---------------- SCHEDULE GENERATOR ----------------
elif app_mode == "Schedule Generator":
    st.header("Schedule Generator")

    # Upload input file
    uploaded_file = st.file_uploader("Upload Audit Input Excel File", type=["xlsx"])

    if uploaded_file:
        # Load Excel file
        xls = pd.ExcelFile(uploaded_file)
        site_names = xls.sheet_names

        # Define auditor availability
        num_auditors = st.number_input("Number of Auditors", min_value=1, step=1)
        auditors = {}
        for i in range(num_auditors):
            name = st.text_input(f"Auditor {i+1} Name")
            coded = st.checkbox(f"Is {name} a Coded Auditor?")
            mandays = st.number_input(f"{name}'s Availability (Mandays)", min_value=1, step=1)
            auditors[name] = {"coded": coded, "mandays": mandays}

        # Process each site
        schedule = {}
        for site in site_names:
            df = pd.read_excel(xls, sheet_name=site)
            df["Hours"] = 8  # Default each activity to 8 hours

            # Assign auditors
            df["Assigned Auditor"] = [None] * len(df)
            for i, row in df.iterrows():
                available_auditors = [a for a in auditors if (not row["Core"]) or auditors[a]["coded"]]
                if available_auditors:
                    df.at[i, "Assigned Auditor"] = available_auditors[i % len(available_auditors)]

            schedule[site] = df

        # Display schedule
        for site, df in schedule.items():
            st.subheader(f"Schedule for {site}")
            st.dataframe(df)

        # Save Schedule
        if st.button("Generate Schedule"):
            with pd.ExcelWriter("Audit_Schedule.xlsx") as writer:
                for site, df in schedule.items():
                    df.to_excel(writer, sheet_name=site, index=False)

            st.success("Schedule File Created: Audit_Schedule.xlsx")
