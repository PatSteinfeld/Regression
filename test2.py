import streamlit as st
import pandas as pd
import datetime
import io

def load_excel(file):
    """Load the Excel file and return a dictionary of sheets."""
    df_dict = pd.read_excel(file, sheet_name=None, header=None)  # Read without headers
    return df_dict

def process_data(df):
    """Extracts data after 'Process/Activities per shift and/or site (when applicable)'."""
    sheet_name = "Sheet1"  # Change if needed
    if sheet_name in df:
        df_sheet = df[sheet_name]
        
        # Locate the row containing the keyword
        keyword = "Process/Activities per shift and/or site (when applicable)"
        row_idx = df_sheet[df_sheet.iloc[:, 0].astype(str).str.contains(keyword, na=False)].index

        if not row_idx.empty:
            start_row = row_idx[0] + 1  # Get the row below the keyword
            planned_audits = df_sheet.iloc[start_row:].dropna(how="all")  # Drop empty rows
            planned_audits.columns = ["Activity"] + [f"Col_{i}" for i in range(1, len(planned_audits.columns))]
            return planned_audits[["Activity"]].reset_index(drop=True)  # Keep only 'Activity' column
        else:
            st.error(f"Keyword '{keyword}' not found in the uploaded file.")
            return None
    else:
        st.error(f"'{sheet_name}' not found in the uploaded file.")
        return None

def generate_schedule(data, auditors, start_time, end_time):
    """Generate an audit schedule with time allocation and lunch break."""
    schedule = []
    time_slot = start_time
    lunch_start = datetime.time(13, 0)
    lunch_end = datetime.time(13, 30)

    for index, row in data.iterrows():
        if time_slot >= end_time:
            break  # Stop if the end time is reached
        
        # Handle lunch break
        if lunch_start <= time_slot < lunch_end:
            time_slot = lunch_end  # Resume after lunch

        schedule.append({
            "Time": time_slot.strftime("%H:%M"),
            "Activity": row["Activity"],  
            "Auditor": auditors[index % len(auditors)]
        })
        
        # Move to the next time slot (1-hour slots)
        time_slot = (datetime.datetime.combine(datetime.date.today(), time_slot) + datetime.timedelta(hours=1)).time()

    return pd.DataFrame(schedule)

def main():
    """Streamlit app main function."""
    st.title("📋 Auditors Planning Schedule")

    # File Upload
    uploaded_file = st.file_uploader("Upload Audit Plan (Excel)", type=["xlsx"])
    
    if uploaded_file:
        df_dict = load_excel(uploaded_file)
        data = process_data(df_dict)
        
        if data is not None:
            st.write("### Extracted Activities")
            st.dataframe(data)

            auditors = st.text_area("Enter Auditors (comma-separated)").split(",")
            start_time = st.time_input("Start Time", datetime.time(9, 0))
            end_time = st.time_input("End Time", datetime.time(18, 0))

            if st.button("Generate Schedule"):
                schedule = generate_schedule(data, auditors, start_time, end_time)
                
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

















