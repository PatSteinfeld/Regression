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
    """Extract number of mandays and relevant activities."""
    first_sheet = list(df.keys())[0]
    data = df[first_sheet]

    # Extract number of mandays
    mandays_row = data[data.iloc[:, 0].astype(str).str.contains("Number of man days", na=False)]
    mandays = int(mandays_row.iloc[0, 1]) if not mandays_row.empty else 1  # Default to 1 if not found

    # Find the row index where "Process/Activities per shift and/or site" appears
    activity_start_idx = data[data.iloc[:, 0].astype(str).str.contains("Process/Activities per shift", na=False)].index

    if not activity_start_idx.empty:
        start_index = activity_start_idx[0] + 1  # Activities start from the next row
        filtered_data = data.iloc[start_index:].reset_index(drop=True)  # Extract relevant activities
    else:
        filtered_data = pd.DataFrame()  # Return empty if no match found

    return mandays, filtered_data

def generate_schedule(data, auditors, start_time, end_time, mandays):
    """Generate a schedule ensuring equal distribution of mandays."""
    if data.empty:
        return pd.DataFrame()

    total_hours = mandays * 8  # Convert mandays to total available hours
    num_activities = len(data)
    hours_per_activity = total_hours / num_activities  # Distribute hours equally

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
            "Activity": row.iloc[0],  # Use the first column for activity names
            "Auditor": auditors[index % num_auditors],  # Assign auditor in round-robin
            "Allocated Hours": round(hours_per_activity, 2)  # Show allocated hours
        })

        # Move to the next slot
        new_time = (datetime.datetime.combine(datetime.date.today(), time_slot) + datetime.timedelta(hours=hours_per_activity)).time()
        
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
        mandays, data = process_data(df_dict)

        if data.empty:
            st.error("Could not find 'Process/Activities per shift and/or site' section. Please check the file format.")
            return

        st.write(f"### Extracted Activities (Mandays: {mandays})")
        st.dataframe(data)

        auditors = st.text_area("Enter Auditors (comma-separated)").split(",")
        start_time = st.time_input("Start Time", datetime.time(9, 0))
        end_time = st.time_input("End Time", datetime.time(18, 0))

        if st.button("Generate Schedule"):
            if not auditors or len(auditors[0]) == 0:
                st.warning("Please enter at least one auditor.")
                return

            schedule = generate_schedule(data, auditors, start_time, end_time, mandays)
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









