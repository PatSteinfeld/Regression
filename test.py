import pandas as pd
import streamlit as st
import plotly.express as px
from io import BytesIO

# Define required columns
REQUIRED_COLUMNS = ["Project Number", "Project Planner", "Project Status", 
                    "Split MD Date Year-Month Label", "Split Man-Days", "End Date"]

# Streamlit UI
st.title("RC Analysis")

# File uploader
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name='Sheet1')

        # Check if required columns are present
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            st.error(f"Missing columns: {', '.join(missing_columns)}. Please upload a valid file.")
        else:
            # Selecting the required columns
            df = df[REQUIRED_COLUMNS]

            # Convert date columns to datetime format
            df["Split MD Date Year-Month Label"] = pd.to_datetime(df["Split MD Date Year-Month Label"], errors='coerce')
            df["End Date"] = pd.to_datetime(df["End Date"], errors='coerce')

            # Calculate the difference in days, weeks, and months
            df["Date Difference (Days)"] = (df["End Date"] - df["Split MD Date Year-Month Label"]).dt.days
            df["Date Difference (Weeks)"] = df["Date Difference (Days)"] // 7  # Convert days to weeks
            df["Date Difference (Months)"] = df["Date Difference (Days)"] // 30  # Approximate months

            # Categorizing the difference based on weeks and months
            def categorize_days(diff):
                if pd.isna(diff):
                    return "N/A"
                elif 0 <= diff <= 30:
                    return "0-30 days"
                elif 31 <= diff <= 60:
                    return "31-60 days"
                elif 61 <= diff <= 90:
                    return "61-90 days"
                elif 91 <= diff <= 180:
                    return "91-180 days"
                elif diff > 180:
                    return "180+ days"
                else:
                    return "NA"

            df["Category (Days)"] = df["Date Difference (Days)"].apply(categorize_days)

            # Categorization by weeks
            def categorize_weeks(diff):
                if pd.isna(diff):
                    return "N/A"
                elif diff <= 4:
                    return "0-4 weeks"
                elif diff <= 8:
                    return "5-8 weeks"
                elif diff <= 12:
                    return "9-12 weeks"
                elif diff <= 24:
                    return "13-24 weeks"
                else:
                    return "24+ weeks"

            df["Category (Weeks)"] = df["Date Difference (Weeks)"].apply(categorize_weeks)

            # Adding RC Type column
            df["RC Type"] = df.apply(lambda row: "RC Not Received" if row["Project Status"] in ["Quote Revision", "Final PA Review"] else "RC Received", axis=1)

            # Corrected RC Sub-status logic
            def assign_rc_sub_status(row):
                if row["RC Type"] == "RC Not Received":
                    return row["Project Status"]
                return "RC Received"

            df["RC Sub-status"] = df.apply(assign_rc_sub_status, axis=1)

            # Grouping data for visualization
            rcc = df.groupby(['Category (Days)', 'RC Type', "RC Sub-status"]) \
                .agg({'Split Man-Days': 'sum', 'Project Planner': lambda x: list(set(x))}) \
                .reset_index()

            rcc.columns = ['Category (Days)', 'RC Type', "RC Sub-status", 'Man-Days', 'Project Planner']

            # Dropdown for selecting category
            selected_category = st.selectbox("Select a Category (Days)", ["All"] + list(rcc["Category (Days)"].unique()))

            # Filter data based on selection
            filtered_df = rcc if selected_category == "All" else rcc[rcc['Category (Days)'] == selected_category]

            # Create bar chart
            fig = px.bar(
                filtered_df,
                x='Category (Days)',
                y='Man-Days',
                color='RC Type',
                text='Man-Days',
                barmode='stack',
                title="Sum of Man-Days Category-wise"
            )

            fig.update_traces(texttemplate='%{text}', textposition='outside')

            # Display plot
            st.plotly_chart(fig)

            # Display project planners when a category is selected
            if selected_category != "All":
                projects = df[df['Category (Days)'] == selected_category]['Project Planner'].unique()
                st.write(f"**Project Planners in {selected_category}:**")
                st.write(", ".join(map(str, projects)) if projects.size > 0 else "No planners found.")

            # Function to download processed data
            def convert_df_to_excel(dataframe):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    dataframe.to_excel(writer, index=False, sheet_name="Processed Data")
                processed_data = output.getvalue()
                return processed_data

            # Download button for processed file
            st.download_button(
                label="📥 Download Processed Data",
                data=convert_df_to_excel(df),
                file_name="processed_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")












