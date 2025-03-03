import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def get_audit_options(file):
    df = pd.read_excel(file, sheet_name=0)
    df.columns = df.columns.str.strip()  # Remove extra spaces from column names
    audit_types = df[df.columns[0]].dropna().unique().tolist()
    sites = df[df.columns[1]].dropna().unique().tolist()
    return audit_types, sites

def generate_schedule(file, auditors, coded_auditors, audit, site, date):
    df = pd.read_excel(file, sheet_name=0)
    df.columns = df.columns.str.strip()
    activities = df[(df[df.columns[0]] == audit) & (df[df.columns[1]] == site)]
    
    if activities.empty:
        return pd.DataFrame([['No matching records found']], columns=['Error'])
    
    mandays = activities.iloc[0, 2]  # Assuming 'No of Mandays' is the third column
    total_hours = mandays * 8
    selected_activities = [col for col in activities.columns[3:] if activities.iloc[0][col] == '*']
    num_activities = len(selected_activities)
    hours_per_activity = total_hours // num_activities if num_activities else 0
    
    schedule = []
    auditors = auditors.split(",") if auditors else []
    coded_auditors = coded_auditors.split(",") if coded_auditors else []
    
    start_time = datetime.strptime(f"{date} 09:00", "%Y-%m-%d %H:%M")
    schedule.append(('Opening Meeting', 'All Auditors', start_time.time(), (start_time + timedelta(minutes=30)).time()))
    start_time += timedelta(minutes=30)
    
    for activity in selected_activities:
        assigned_auditor = coded_auditors.pop(0) if 'Core' in activity and coded_auditors else auditors.pop(0) if auditors else 'Unassigned'
        end_time = start_time + timedelta(hours=hours_per_activity)
        
        if start_time.hour == 13:
            schedule.append(('Lunch Break', 'All Auditors', start_time.time(), (start_time + timedelta(minutes=30)).time()))
            start_time += timedelta(minutes=30)
            end_time += timedelta(minutes=30)
        
        schedule.append((activity, assigned_auditor, start_time.time(), end_time.time()))
        start_time = end_time
        if end_time.hour >= 18:
            break
    
    schedule.append(('Closing Meeting', 'All Auditors', start_time.time(), (start_time + timedelta(minutes=30)).time()))
    return pd.DataFrame(schedule, columns=['Activity', 'Auditor', 'Start Time', 'End Time'])

def main():
    st.title("Auditors Planning Schedule")
    file = st.file_uploader("Upload Excel File", type=["xlsx"])
    
    if file:
        audit_types, sites = get_audit_options(file)
        audit = st.selectbox("Select Audit Type", audit_types)
        site = st.selectbox("Select Site", sites)
        date = st.date_input("Select Date")
        auditors = st.text_area("Auditors (comma-separated)")
        coded_auditors = st.text_area("Coded Auditors (comma-separated)")
        
        if st.button("Generate Schedule"):
            schedule = generate_schedule(file, auditors, coded_auditors, audit, site, date.strftime("%Y-%m-%d"))
            st.dataframe(schedule)
            
            # Provide option to download Excel
            excel_file = "Audit_Schedule.xlsx"
            schedule.to_excel(excel_file, index=False)
            with open(excel_file, "rb") as f:
                st.download_button("Download Excel", f, file_name="Audit_Schedule.xlsx")
            
            # Provide option to download CSV
            csv_file = "Audit_Schedule.csv"
            schedule.to_csv(csv_file, index=False)
            with open(csv_file, "rb") as f:
                st.download_button("Download CSV", f, file_name="Audit_Schedule.csv")

if __name__ == "__main__":
    main()

