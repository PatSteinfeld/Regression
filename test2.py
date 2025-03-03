import pandas as pd
import datetime

# Load Excel with multiple header rows (adjust sheet_name if needed)
file_path = "Periodical Audit Programme_2024.xlsx"  # Update with the actual file path
df = pd.read_excel(file_path, header=[0, 1])  # Read first two rows as headers

# Flatten the multi-index columns
df.columns = [' '.join(map(str, col)).strip() for col in df.columns]

# Extract relevant section (ignoring "None" values)
activities_df = df.iloc[5:9].dropna()  # Rows 5-8 (Adjust if needed)

# User inputs
auditors = ["Auditor 1", "Auditor 2"]  # Example auditor names
mandays = 2  # Total mandays available
start_date = datetime.date(2025, 3, 3)  # Example start date
start_time = datetime.time(9, 0)  # 9:00 AM start
end_time = datetime.time(18, 0)  # 6:00 PM end

def generate_schedule(data, auditors, mandays, start_date, start_time, end_time):
    """Generate the audit schedule while distributing mandays and skipping lunch break."""
    schedule = []
    total_hours = mandays * 8  # Total available hours (1 manday = 8 hours)
    hours_per_activity = total_hours / len(data)  # Distribute equally

    lunch_start = datetime.time(13, 0)   # 1:00 PM
    lunch_end = datetime.time(13, 30)    # 1:30 PM

    current_time = start_time
    current_date = start_date
    auditor_count = len(auditors)

    for i, activity in enumerate(data.iloc[:, 0]):  # Select first column dynamically
        if total_hours <= 0:
            break  # Stop scheduling when all mandays are used

        if current_time >= end_time:  # Shift to next day
            current_date += datetime.timedelta(days=1)
            current_time = start_time

        # Ensure lunch break is exactly 30 minutes
        if lunch_start <= current_time < lunch_end:
            current_time = lunch_end  # Resume right after 1:30 PM

        # Calculate end time based on available hours per activity
        end_activity_time = (datetime.datetime.combine(datetime.date.today(), current_time) + datetime.timedelta(hours=hours_per_activity)).time()

        # If activity ends after 6 PM, move to next day
        if end_activity_time > end_time:
            current_date += datetime.timedelta(days=1)
            current_time = start_time
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

# Generate schedule
schedule_df = generate_schedule(activities_df, auditors, mandays, start_date, start_time, end_time)

# Save to Excel
output_file = "Audit_Schedule.xlsx"
schedule_df.to_excel(output_file, index=False)
print(f"Schedule saved to {output_file}")

# Display output
print(schedule_df)














