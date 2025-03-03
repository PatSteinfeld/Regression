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
        filtered_data = filtered_data[filtered_data.iloc[:, 0].notna()]  # Remove "None" activities
    else:
        filtered_data = pd.DataFrame()  # Return empty if no match found

    return mandays, filtered_data

def generate_schedule(data, auditors, mandays, start_date):
    """Generate a schedule ensuring 8 hours per auditor per day and shifting excess to the next day."""
    if data.empty:
        return pd.DataFrame()

    total_mandays_needed = mandays  # Total required mandays
    hours_per_day_per_auditor = 8  # Each auditor works 8 hours per day
    total_hours_needed = total_mandays_needed * hours_per_day_per_auditor
    num_auditors = len(auditors)

    # Calculate available working hours per day considering all auditors
    total_hours_per_day = num_auditors * hours_per_day_per_auditor

    # Initialize scheduling
    schedule = []
    current_day = 1
    current_date = start_date
    start_time = datetime.time(9, 0)
    end_time = datetime.time(18, 0)
    time_slot = start_time
    daily_hours_used = 0
    current_auditor_index = 0

    for index, row in data.iterrows():
        activity_name = row.iloc[0]  # Get activity name
        allocated_hours = min(8, total_hours_needed / len(data))  # Distribute hours

        if time_slot >= end_time or daily_hours_used + allocated_hours > hours_per_day_per_auditor:
            # Move to next day
            current_day += 1
            current_date += datetime.timedelta(days=1)
            time_slot = start_time
            daily_hours_used = 0

        # Assign auditor in round-robin fashion
        assigned_auditor = auditors[current_auditor_index % num_auditors]
        schedule.append({
            "Date": current_date.strftime("%Y-%m-%d"),
            "Day": current_day,
            "Time": time_slot.strftime("%H:%M"),
            "Activity": activity_name,
            "Auditor": assigned_auditor,
            "Allocated Hours": allocated_hours
        })

        # Update total hours left
        total_hours_needed -= allocated_hours
        daily_hours_used += allocated_hours

        # Move to next time slot
        time_slot = (datetime.datetime.combine(current_date, time_slot) + datetime.timedelta(hours=allocated_hours)).time()
        current_auditor_index += 1

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
        start_date = st.date_input("Select Start Date", datetime.date.today())

        if st.button("Generate Schedule"):
            if not auditors or len(auditors[0]) == 0:
                st.warning("Please enter at least one auditor.")
                return

            schedule = generate_schedule(data, auditors, mandays, start_date)
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












