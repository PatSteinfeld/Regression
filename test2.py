import streamlit as st
import pandas as pd
import datetime
import re

def load_excel(file):
    df = pd.read_excel(file, sheet_name=None)
    return df

def find_matching_column(columns, target):
    """Find a column that matches the target name case-insensitively and ignores spaces."""
    target_cleaned = re.sub(r'\s+', ' ', target.strip()).lower()  # Normalize target
    
    for col in columns:
        col_cleaned = re.sub(r'\s+', ' ', col.strip()).lower()  # Normalize column
        if target_cleaned in col_cleaned:  # Partial match
            return col  # Return actual column name
    
    return None  # No match found

def process_data(df, selected_sheet):
    df_sheet = df[selected_sheet]
    
    # Get all column names
    columns = list(df_sheet.columns)
    st.write("### Available Columns in Sheet")
    st.write(columns)  # Show columns for debugging
    
    # Find matching column
    target_column = "Process/Activities per shift and/or site (when applicable)"
    matched_column = find_matching_column(columns, target_column)
    
    if matched_column:
        planned_audits = df_sheet[[matched_column]].dropna().reset_index(drop=True)
    else:
        st.error(f"Column similar to '{target_column}' not found in the selected sheet.")
        planned_audits = pd.DataFrame()  # Return empty DataFrame if column is missing
    
    return planned_audits

def generate_schedule(data, auditors, start_time, end_time):
    schedule = []
    time_slot = start_time
    lunch_break = datetime.time(13, 0)
    
    for index, row in data.iterrows():
        if time_slot >= end_time:
            break  # Stop if end time is reached
        
        if time_slot == lunch_break:
            time_slot = (datetime.datetime.combine(datetime.date.today(), time_slot) + datetime.timedelta(minutes=30)).time()
        
        schedule.append({
            "Time": time_slot,
            "Activity": row.iloc[0],  # Extract activity from the first column
            "Auditor": auditors[index % len(auditors)]
        })
        
        time_slot = (datetime.datetime.combine(datetime.date.today(), time_slot) + datetime.timedelta(hours=1)).time()
    
    return pd.DataFrame(schedule)

def main():
    st.title("Auditors Planning Schedule")
    
    uploaded_file = st.file_uploader("Upload Audit Plan (Excel)", type=["xlsx"])
    
    if uploaded_file:
        df_dict = load_excel(uploaded_file)
        sheet_names = list(df_dict.keys())
        selected_sheet = st.selectbox("Select Sheet", sheet_names)
        
        if selected_sheet:
            data = process_data(df_dict, selected_sheet)
            
            if not data.empty:
                st.write("### Extracted Data")
                st.dataframe(data)
                
                auditors = st.text_area("Enter Auditors (comma-separated)").split(",")
                start_time = st.time_input("Start Time", datetime.time(9, 0))
                end_time = st.time_input("End Time", datetime.time(18, 0))
                
                if st.button("Generate Schedule"):
                    schedule = generate_schedule(data, auditors, start_time, end_time)
                    st.write("### Generated Schedule")
                    st.dataframe(schedule)
                    
                    schedule.to_excel("Auditors_Schedule.xlsx", index=False)
                    with open("Auditors_Schedule.xlsx", "rb") as file:
                        st.download_button("Download Schedule", file, file_name="Auditors_Schedule.xlsx")

if __name__ == "__main__":
    main()






