import streamlit as st
import pandas as pd
from datetime import datetime

@st.cache_data
def extract_data_from_pap(file):
    """
    Extracts data from the PAP sheet of the uploaded Excel file.
    
    Structure:
    - Row 7 (index 6): Audit Types (columns 1 onward)
    - Row 8 (index 7): Number of Man-Days (columns 1 onward; only numeric values are kept)
    - Row 9 (index 8): Proposed Audit Dates (columns 1 onward)
    - Row 12 onward (index 12): Sites are assumed to be in column index 10,
      and associated activities (if available) are in column index 12.
    """
    # Load the Excel file and read the PAP sheet without header inference
    xls = pd.ExcelFile(file)
    pap_df = pd.read_excel(xls, sheet_name="PAP", header=None)
    
    # Extract Audit Types from row 7 (index 6), starting at column 1
    audit_types_raw = pap_df.iloc[6, 1:].dropna().tolist()
    audit_types = [x for x in audit_types_raw if isinstance(x, str) and "insert" not in x]
    
    # Extract Man-Days from row 8 (index 7), starting at column 1; keep only numeric values
    man_days_raw = pap_df.iloc[7, 1:].dropna().tolist()
    man_days = [x for x in man_days_raw if isinstance(x, (int, float))]
    
    # Extract Proposed Audit Dates from row 9 (index 8), starting at column 1
    audit_dates_raw = pap_df.iloc[8, 1:].dropna().tolist()
    audit_dates = [x for x in audit_dates_raw if isinstance(x, str) and "Site" not in x]
    
    # Extract Sites from the PAPENDA section
    # Assuming sites are in column index 10 from row 12 onward
    sites_raw = pap_df.iloc[12:30, 10].dropna().tolist()
    sites = sites_raw  # List of site names
    
    # Extract activities: assume they are in column index 12 adjacent to the sites
    activities_dict = {}
    for idx, site in enumerate(sites_raw):
        try:
            activity = pap_df.iloc[12 + idx, 12]
            if pd.notna(activity):
                activities_dict[site] = activity
            else:
                activities_dict[site] = "No activity specified"
        except Exception:
            activities_dict[site] = "No activity specified"
    
    return {
        "audit_types": audit_types,
        "man_days": man_days,
        "audit_dates": audit_dates,
        "sites": sites,
        "activities": activities_dict
    }

def main():
    st.title("Audit Planner (PAP Sheet)")
    
    # File Upload
    uploaded_file = st.file_uploader("Upload the Excel File", type=["xlsm", "xlsx"])
    if uploaded_file:
        data = extract_data_from_pap(uploaded_file)
        
        st.subheader("Extracted Data")
        st.write("**Audit Types:**", data["audit_types"])
        st.write("**Number of Man-Days:**", data["man_days"])
        st.write("**Proposed Audit Dates:**", data["audit_dates"])
        st.write("**Sites:**", data["sites"])
        
        # User Inputs
        num_auditors = st.selectbox("Select Number of Auditors", list(range(1, 11)))
        
        auditor_names_input = st.text_input("Enter Auditor Names (comma separated)")
        auditor_names = [name.strip() for name in auditor_names_input.split(",") if name.strip()]
        
        selected_audit_type = st.selectbox("Select Audit Type", data["audit_types"])
        selected_site = st.selectbox("Select Site", data["sites"])
        selected_date = st.date_input("Select Audit Date", datetime.today())
        
        # Display activity for the selected site (if available)
        activity_for_site = data["activities"].get(selected_site, "No activity specified")
        st.write("**Activity for selected site:**", activity_for_site)
        
        # Generate Audit Plan
        if st.button("Generate Audit Plan"):
            try:
                index = data["audit_types"].index(selected_audit_type)
                total_man_days = data["man_days"][index] if index < len(data["man_days"]) else None
            except Exception:
                total_man_days = None
            
            total_hours = total_man_days * 8 if total_man_days is not None else 0
            
            # Create a simple schedule DataFrame
            plan_data = {
                "Audit Type": [selected_audit_type],
                "Site": [selected_site],
                "Activity": [activity_for_site],
                "Time Allocation (hours)": [total_hours],
                "Audit Date": [selected_date],
                "Assigned Auditor": [auditor_names[0] if auditor_names else "Not Assigned"]
            }
            plan_df = pd.DataFrame(plan_data)
            
            st.subheader("Audit Planning Schedule")
            st.dataframe(plan_df)
            st.success("Audit plan generated successfully!")
    else:
        st.info("Please upload an Excel file to get started.")

if __name__ == "__main__":
    main()



















