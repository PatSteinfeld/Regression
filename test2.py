import streamlit as st
import pandas as pd
import datetime

def load_excel(file):
    df = pd.read_excel(file, sheet_name=None)
    return df

def process_data(df, selected_sheet):
    # Standardize column names to avoid KeyError
    df[selected_sheet].columns = df[selected_sheet].columns.str.strip().str.lower()
    selected_column = "process/activities per shift and/or site (when applicable)".lower()
    
    if selected_column in df[selected_sheet].columns:
        planned_audits = df[selected_sheet][selected_column]
    else:
        planned_audits = pd.Series([])  # Empty series if column not found
    
    return planned_audits

def generate_schedule(data, auditors, start_time, end_time):
    schedule = []
    time_slot = start_time
    lunch_break = datetime.time(13, 0)
    
    for index, activity in data.items():
        if time_slot >= end_time:
            break  # Stop if end time is reached
        
        if time_slot == lunch_break:
            time_slot = (datetime.datetime.combine(datetime.date.today(), time_slot) + datetime.timedelta(minutes=30)).time()
        
        schedule.append({
            "Time": time_slot,
            "Activity": activity,  # Updated column selection
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





