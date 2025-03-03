import streamlit as st
import pandas as pd
import datetime

def load_excel(file):
    """Load Excel file and preprocess multi-header columns."""
    df = pd.read_excel(file, header=[0, 1])  # Read first two rows as headers
    df.columns = [' '.join(map(str, col)).strip() for col in df.columns]  # Flatten headers
    return df

def extract_relevant_data(df):
    """Extract required scheduling data while excluding 'None' values."""
    start_index = df[df.iloc[:, 0] == "Process/Activities per shift and/or site (when applicable)"].index[0] + 1
    data = df.iloc[start_index:].dropna(subset=[df.columns[0]])  # Drop rows where first column is None
    return data

def generate_schedule(data, auditors, mandays, start_date, start_time, end_time):
    """Generate the audit schedule while distributing mandays and skipping lunch break."""
    schedule = []
    total_hours = mandays * 8  # Total available hours
    hours_per_activity = total_hours / len(data)  # Distribute equally
    lunch_start = datetime.time(13, 0)
    lunch_end = datetime.time(13, 30)
    
    current_time = start_time
    current_date = start_date
    auditor_count = len(auditors)

    for i, activity in enumerate(data.iloc[:, 0]):  # Select first column dynamically
        if total_hours <= 0:
            break  # Stop scheduling when all mandays are used
        
        if current_time >= end_time:  # Shift to next day
            current_date += datetime.timedelta(days=1)
            current_time = start_time

        # Skip lunch break if time overlaps
        if lunch_start <= current_time < lunch_end:
            current_time = lunch_end

        end_activity_time = (datetime.datetime.combine(datetime.date.today(), current_time) + datetime.timedelta(hours=hours_per_activity)).time()

        schedule.append({
            "Date": current_date,
            "Start Time": current_time.strftime("%H:%M"),
            "End Time": end_activity_time.strftime("%H:%M"),
            "Activity": activity,
            "Auditor": auditors[i % auditor_count]  # Cycle through auditors
        })

        current_time = end_activity_time
        total_hours -= hours_per_activity  # Reduce available hours

    return pd.DataFrame(schedule)

def main():
    st.title("Auditors Planning Schedule")
    
    uploaded_file = st.file_uploader("Upload Audit Plan (Excel)", type=["xlsx"])
    
    if uploaded_file:
        df = load_excel(uploaded_file)
        data = extract_relevant_data(df)
        
        st.write("### Extracted Data")
        st.dataframe(data)

        auditors = st.text_area("Enter Auditors (comma-separated)").split(",")
        mandays = st.number_input("Total Mandays", min_value=1, value=2)
        start_date = st.date_input("Start Date", datetime.date.today())
        start_time = st.time_input("Start Time", datetime.time(9, 0))
        end_time = st.time_input("End Time", datetime.time(18, 0))

        if st.button("Generate Schedule"):
            schedule = generate_schedule(data, auditors, mandays, start_date, start_time, end_time)
            st.write("### Generated Schedule")
            st.dataframe(schedule)
            
            schedule.to_excel("Auditors_Schedule.xlsx", index=False)
            with open("Auditors_Schedule.xlsx", "rb") as file:
                st.download_button("Download Schedule", file, file_name="Auditors_Schedule.xlsx")

if __name__ == "__main__":
    main()














