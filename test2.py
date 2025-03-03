import streamlit as st
import pandas as pd
import datetime
from io import BytesIO

def preprocess_excel(file):
    """
    Loads the Excel file without a header and attempts to detect the header row
    by looking for expected keywords.
    """
    # Load the entire file without headers
    df_raw = pd.read_excel(file, header=None)
    
    st.write("### Raw Data Preview")
    st.write(df_raw.head(15))
    
    # Define keywords that should appear in the header row
    expected_keywords = ["Site", "Activity", "Audit", "Date", "Man-Days"]
    header_row_index = None

    # Try to find a row that contains any of the expected keywords
    for i, row in df_raw.iterrows():
        # Convert row values to strings in lower-case
        row_str = row.astype(str).str.lower()
        if any(any(keyword.lower() in cell for cell in row_str if isinstance(cell, str)) 
               for keyword in expected_keywords):
            header_row_index = i
            st.write(f"**Detected header row at index {i}:**")
            st.write(row)
            break

    if header_row_index is None:
        st.error("Could not automatically detect a header row. Please check the file format.")
        return None

    # Reload the file using the detected header row
    df_table = pd.read_excel(file, header=header_row_index)
    st.write("### Data After Applying Detected Header")
    st.write(df_table.head(10))
    return df_table

def extract_audit_data(df):
    """
    Extracts audit data from the DataFrame.
    Expected columns (or close variants) include:
    "Audit Type", "Proposed Audit Date", "Man-Days", "Site", "Activity".
    Core activities are indicated by a '*' in the Activity.
    """
    # Optionally, rename columns if they don't exactly match
    # For example, you might want to standardize column names:
    expected_columns = {
        "Audit programme": "Audit Type",
        "Proposed Audit Date": "Proposed Audit Date",
        "Man-Days": "Man-Days",
        "Site": "Site",
        "Activity": "Activity"
    }
    # Check if any of the expected columns are missing and try to rename if possible
    for col in expected_columns:
        if col in df.columns:
            df = df.rename(columns={col: expected_columns[col]})
    
    # Extract audit types from "Audit Type" column if present
    audit_types = df["Audit Type"].dropna().unique().tolist() if "Audit Type" in df.columns else []
    proposed_audit_date = df["Proposed Audit Date"].iloc[0] if "Proposed Audit Date" in df.columns else None
    man_days = df["Man-Days"].iloc[0] if "Man-Days" in df.columns else 1  # default to 1 if missing
    
    # Build a dictionary mapping each site to its list of activities
    sites = {}
    if "Site" in df.columns and "Activity" in df.columns:
        for _, row in df.iterrows():
            site = row["Site"]
            activity = row["Activity"]
            if pd.isna(site) or pd.isna(activity):
                continue
            # Determine if the activity is core (marked with '*')
            is_core = "*" in str(activity)
            # Clean the activity name (remove the '*' symbol)
            activity_clean = str(activity).replace("*", "").strip()
            if site not in sites:
                sites[site] = []
            sites[site].append({
                "activity": activity_clean,
                "is_core": is_core
            })
    
    return {
        "audit_types": audit_types,
        "proposed_audit_date": proposed_audit_date,
        "man_days": man_days,
        "sites": sites
    }

def main():
    st.title("Auditors Planning Schedule")
    
    uploaded_file = st.file_uploader("Upload Audit Plan (Excel)", type=["xlsx"])
    
    if uploaded_file:
        # Preprocess the file to get a structured DataFrame
        df = preprocess_excel(uploaded_file)
        if df is None:
            return
        
        # Extract audit data from the processed DataFrame
        extracted_data = extract_audit_data(df)
        
        st.write("### Extracted Data Overview")
        st.write("**Audit Types:**", extracted_data["audit_types"])
        st.write("**Proposed Audit Date:**", extracted_data["proposed_audit_date"])
        st.write("**Man-Days:**", extracted_data["man_days"])
        st.write("**Sites Available:**", list(extracted_data["sites"].keys()))
        
        st.write("---")
        st.subheader("User Inputs")
        # Number of Auditors
        num_auditors = st.selectbox("Select number of auditors", list(range(1, 11)))
        # Auditor names (comma-separated)
        auditors_input = st.text_input("Enter Auditor Names (comma-separated)")
        auditors = [name.strip() for name in auditors_input.split(",") if name.strip()]
        if len(auditors) != num_auditors:
            st.warning("Please ensure the number of auditor names matches the selected number of auditors.")
        
        # Coded auditors (for core activities only)
        coded_auditors_input = st.text_input("Enter Coded Auditor Names (comma-separated)")
        coded_auditors = [name.strip() for name in coded_auditors_input.split(",") if name.strip()]
        
        # Audit Type selection from extracted data
        if extracted_data["audit_types"]:
            selected_audit_type = st.selectbox("Select Audit Type", extracted_data["audit_types"])
        else:
            selected_audit_type = st.text_input("Enter Audit Type")
        
        # Site selection from extracted data
        if extracted_data["sites"]:
            selected_site = st.selectbox("Select Site", list(extracted_data["sites"].keys()))
        else:
            selected_site = st.text_input("Enter Site")
        
        # Based on selected site, get available activities
        available_activities = []
        activity_details = {}
        if selected_site in extracted_data["sites"]:
            for item in extracted_data["sites"][selected_site]:
                available_activities.append(item["activity"])
                activity_details[item["activity"]] = item["is_core"]
        
        # User selects which activities to audit
        selected_activities = st.multiselect("Select Activities to be Audited", available_activities)
        
        # Audit Date input (user-specified)
        audit_date = st.date_input("Select Audit Date", datetime.date.today())
        
        st.write("---")
        if st.button("Generate Audit Plan"):
            if not auditors or len(auditors) != num_auditors:
                st.error("Please provide the correct number of auditor names.")
            elif not selected_activities:
                st.error("Please select at least one activity to audit.")
            else:
                # Calculate total available hours (1 Man-Day = 8 hours)
                total_hours = extracted_data["man_days"] * 8
                per_activity_hours = total_hours / len(selected_activities)
                
                st.write("### Assign Auditors to Activities")
                schedule_rows = []
                assignments = {}
                
                # For each selected activity, provide a dropdown for auditor assignment.
                for act in selected_activities:
                    is_core = activity_details.get(act, False)
                    if is_core:
                        # Only allow selection from coded auditors for core activities
                        options = [aud for aud in auditors if aud in coded_auditors]
                        if not options:
                            st.error(f"No coded auditors available for the core activity '{act}'.")
                            return
                    else:
                        options = auditors
                    assigned_auditor = st.selectbox(f"Assign auditor for activity **{act}**", options, key=f"assign_{act}")
                    assignments[act] = assigned_auditor
                    
                    schedule_rows.append({
                        "Audit Name": selected_audit_type,
                        "Site": selected_site,
                        "Audit Date": audit_date,
                        "Activity": act,
                        "Core Activity": "Yes" if is_core else "No",
                        "Time Allocation (hours)": round(per_activity_hours, 2),
                        "Assigned Auditor": assigned_auditor
                    })
                
                schedule_df = pd.DataFrame(schedule_rows)
                st.write("### Generated Audit Plan")
                st.dataframe(schedule_df)
                
                # Save the schedule to an Excel file using an in-memory buffer
                output = BytesIO()
                schedule_df.to_excel(output, index=False)
                output.seek(0)
                st.download_button("Download Audit Plan", output, file_name="Auditors_Audit_Plan.xlsx")

if __name__ == "__main__":
    main()




















