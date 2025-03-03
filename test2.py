import streamlit as st
import pandas as pd
import datetime

def load_excel(file):
    df = pd.read_excel(file, sheet_name=None)
    return df

def process_data(df):
    # Extract relevant data
    planned_audits = df["Sheet1"].iloc[:, :10]  # Adjust as per sheet structure
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
            "Activity": row["ACTIVITY"],
            "Auditor": auditors[index % len(auditors)]
        })
        
        time_slot = (datetime.datetime.combine(datetime.date.today(), time_slot) + datetime.timedelta(hours=1)).time()
    
    return pd.DataFrame(schedule)

def main():
    st.title("Auditors Planning Schedule")
    
    uploaded_file = st.file_uploader("Upload Audit Plan (Excel)", type=["xlsx"])
    
    if uploaded_file:
        df_dict = load_excel(uploaded_file)
        data = process_data(df_dict)
        
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







