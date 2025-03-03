import streamlit as st
import pandas as pd
import datetime
from io import BytesIO

def load_excel(file):
    """Load Excel file, handling multi-row headers."""
    df = pd.read_excel(file, sheet_name=None, header=[0, 1])  # Read first two rows as headers

    # Flatten multi-index columns
    for sheet in df:
        df[sheet].columns = [' '.join(map(str, col)).strip() for col in df[sheet].columns]

    return df

def process_data(df):
    """Extract relevant data from the first sheet."""
    planned_audits = df[list(df.keys())[0]].iloc[:, :10]  # Adjust if needed
    return planned_audits

def generate_schedule(data, auditors, start_time, end_time):
    """Generate a schedule ensuring constraints like lunch break and end time."""
    schedule = []
    time_slot = start_time
    lunch_start = datetime.time(13, 0)
    lunch_end = datetime.time(13, 30)
    
    num_auditors = len(auditors)
    
    for index, row in data.iterrows():
        if time_slot >= end_time:
            break  # Stop if end time is reached
        
        # Handle lunch break
        if lunch_start <= time_slot < lunch_end:
            time_slot = lunch_end  # Resume after lunch
        
        if time_slot >= end_time:
            break  # Stop if resuming exceeds end time

        schedule.append({
            "Time": time_slot,
            "Activity": row["ACTIVITY"],
            "Auditor": auditors[index % num_auditors]  # Assign auditor in round-robin
        })

        # Move to the next slot
        new_time = (datetime.datetime.combine(datetime.date.today(), time_slot) + datetime.timedelta(hours=1)).time()
        
        # Ensure new_time doesn't exceed end time
        if new_time < end_time:
            time_slot = new_time
        else:
            break

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
            if not auditors or len(auditors[0]) == 0:
                st.warning("Please enter at least one auditor.")
                return

            schedule = generate_schedule(data, auditors, start_time, end_time)
            st.write("### Generated Schedule")
            st.dataframe(schedule)

            # Create Excel file in-memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                schedule.to_excel(writer, index=False, sheet_name="Schedule")
            output.seek(0)

            st.download_button("Download Schedule", output, file_name="Auditors_Schedule.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()








