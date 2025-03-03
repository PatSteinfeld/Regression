import streamlit as st
import pandas as pd
import datetime
import io

def load_excel(file):
    """Load the Excel file and return a dictionary of sheets."""
    df_dict = pd.read_excel(file, sheet_name=None, header=None)
    return df_dict

def extract_relevant_data(df_dict):
    """Extracts audit types, sites, activities, man-days, and core activities."""
    sheet_name = list(df_dict.keys())[0]  # Assume first sheet
    df = df_dict[sheet_name]

    st.write(f"### 🔍 Debug: Sheet Name: {sheet_name}")  # Print sheet name
    st.write("### 🔍 Debug: First 10 rows of the sheet")
    st.dataframe(df.head(10))  # Preview data

    # Locate key sections
    audit_types = df.iloc[0, 1:].dropna().tolist()  # Audit types in the first row
    proposed_audit_date = df.iloc[1, 1:].dropna().tolist()  # Dates in the second row
    num_mandays = df.iloc[2, 1:].dropna().tolist()  # Man-days in the third row

    # Find "Process/Activities per shift and/or site (when applicable)"
    keyword = "Process/Activities per shift and/or site (when applicable)"
    row_idx = df[df.iloc[:, 0].astype(str).str.contains(keyword, na=False)].index

    if not row_idx.empty:
        start_row = row_idx[0] + 1  # Row below the keyword
        activities = df.iloc[start_row:].dropna(how="all")
        
        # Rename columns
        activities.columns = ["Activity"] + [f"Site_{i}" for i in range(1, len(activities.columns))]
        
        # Identify core activities (marked with "*")
        activities["Core"] = activities["Activity"].astype(str).str.contains(r"\*")
        activities["Activity"] = activities["Activity"].str.replace(r"\*", "", regex=True).str.strip()

        # Create structured data
        extracted_data = {
            "audit_types": audit_types,
            "proposed_dates": proposed_audit_date,
            "num_mandays": num_mandays,
            "activities": activities[["Activity", "Core"]].reset_index(drop=True)
        }

        return extracted_data
    else:
        st.error(f"❌ Keyword '{keyword}' not found in the uploaded file.")
        return None

def generate_schedule(activities, auditors, start_time, end_time, mandays):
    """Generate an audit schedule with time allocation and core activity restrictions."""
    schedule = []
    time_slot = start_time
    lunch_start = datetime.time(13, 0)
    lunch_end = datetime.time(13, 30)

    total_hours = mandays * 8  # 1 Manday = 8 hours
    hours_per_activity = total_hours / len(activities) if len(activities) > 0 else 1

    for index, row in activities.iterrows():
        if time_slot >= end_time:
            break  # Stop if the end time is reached

        # Handle lunch break
        if lunch_start <= time_slot < lunch_end:
            time_slot = lunch_end

        auditor = auditors[index % len(auditors)]

        # Assign only coded auditors to core activities
        if row["Core"] and "Coded" not in auditor:
            continue

        schedule.append({
            "Time": time_slot.strftime("%H:%M"),
            "Activity": row["Activity"],
            "Auditor": auditor
        })

        # Move to next time slot
        time_slot = (datetime.datetime.combine(datetime.date.today(), time_slot) +
                     datetime.timedelta(hours=hours_per_activity)).time()

    return pd.DataFrame(schedule)

def main():
    """Streamlit app main function."""
    st.title("📋 Auditors Planning Schedule")

    # File Upload
    uploaded_file = st.file_uploader("Upload Audit Plan (Excel)", type=["xlsx"])

    if uploaded_file:
        df_dict = load_excel(uploaded_file)
        extracted_data = extract_relevant_data(df_dict)

        if extracted_data:
            st.write("### Available Audit Types")
            audit_type = st.selectbox("Select Audit Type", extracted_data["audit_types"])

            st.write("### Available Activities")
            selected_activities = st.multiselect("Select Activities", extracted_data["activities"]["Activity"].tolist())

            num_auditors = st.number_input("Number of Auditors", min_value=1, max_value=10, value=2)
            auditor_names = [st.text_input(f"Auditor {i+1} Name") for i in range(num_auditors)]
            coded_auditors = st.multiselect("Select Coded Auditors", auditor_names)

            start_time = st.time_input("Start Time", datetime.time(9, 0))
            end_time = st.time_input("End Time", datetime.time(18, 0))
            selected_mandays = st.slider("Number of Man-Days", 1, max(extracted_data["num_mandays"]), 1)

            if st.button("Generate Schedule"):
                selected_df = extracted_data["activities"][extracted_data["activities"]["Activity"].isin(selected_activities)]
                schedule = generate_schedule(selected_df, auditor_names, start_time, end_time, selected_mandays)

                st.write("### Generated Schedule")
                st.dataframe(schedule)

                # Export to Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    schedule.to_excel(writer, index=False, sheet_name="Schedule")
                output.seek(0)

                st.download_button(
                    label="📥 Download Schedule",
                    data=output,
                    file_name="Auditors_Schedule.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    main()


















