import pandas as pd
import streamlit as st

# Function to load and process the Excel file
def load_audit_data(file):
    df = pd.read_excel(file, sheet_name=None)  # Load all sheets
    sheet_name = list(df.keys())[0]  # Assuming the first sheet contains PAP data
    data = df[sheet_name]
    
    # Identify header row (assumption: headers are in first few rows)
    header_row = data[data.iloc[:, 0].astype(str).str.contains('Audit Type', na=False)].index[0]
    data.columns = data.iloc[header_row]
    data = data[header_row + 1:].reset_index(drop=True)
    
    # Drop empty columns
    data = data.dropna(axis=1, how='all')
    data = data.dropna(how='all')
    
    return data

# Streamlit UI
def main():
    st.title("Auditors' Planning Schedule")
    uploaded_file = st.file_uploader("Upload PAP Excel file", type=["xlsx"])
    
    if uploaded_file:
        audit_data = load_audit_data(uploaded_file)
        st.write("### Extracted Audit Data:")
        st.dataframe(audit_data)
        
        # Extract necessary columns (adjust based on actual column names in file)
        audit_types = audit_data['Audit Type'].dropna().unique()
        selected_audit = st.selectbox("Select Audit Type", audit_types)
        
        site_names = [col for col in audit_data.columns if "Site" in str(col)]
        selected_site = st.selectbox("Select Site", site_names)
        
        # Filter activities marked with '*'
        activities = audit_data[selected_site].dropna()
        activities = activities[activities.str.contains('\*')]
        activities = activities.index.tolist()
        
        st.write("### Activities to be Audited:")
        selected_activities = st.multiselect("Select Activities", activities)
        
        # Calculate total audit time
        man_days = audit_data.loc[audit_data['Audit Type'] == selected_audit, 'Number of Man-Days'].values
        total_hours = (man_days[0] * 8) if len(man_days) > 0 else 0
        
        st.write(f"### Total Audit Time: {total_hours} hours")
        
        # Assign auditors
        num_auditors = st.number_input("Number of Auditors", min_value=1, max_value=5, step=1)
        auditors = [st.text_input(f"Auditor {i+1} Name") for i in range(num_auditors)]
        coded_status = [st.checkbox(f"Coded Auditor {i+1}") for i in range(num_auditors)]
        
        # Display Final Schedule
        if st.button("Generate Schedule"):
            schedule_df = pd.DataFrame({
                "Audit Name": [selected_audit] * len(selected_activities),
                "Site": [selected_site] * len(selected_activities),
                "Activity": selected_activities,
                "Assigned Auditor": auditors[:len(selected_activities)],
                "Coded Auditor": coded_status[:len(selected_activities)]
            })
            st.write("### Final Audit Schedule")
            st.dataframe(schedule_df)
            
            # Option to download schedule
            csv = schedule_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Schedule as CSV", data=csv, file_name="audit_schedule.csv", mime='text/csv')
            
if __name__ == "__main__":
    main()







