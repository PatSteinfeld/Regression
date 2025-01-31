import pandas as pd
import streamlit as st
import plotly.express as px
from io import BytesIO

# Streamlit Page Config with Dark Mode Support
st.set_page_config(page_title="RC Analysis", layout="wide")

# Define required columns
REQUIRED_COLUMNS = ["Project Number", "Service Code", "Project Status", "Split MD Date Year-Month Label", "Split Man-Days", "Validity End Date"]

# Sidebar UI
st.sidebar.header("Upload Your File 📂")
uploaded_file = st.sidebar.file_uploader("Upload an Excel file", type=["xlsx"])

# Main Title
st.title("📊 RC Analysis")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name='Sheet1')

        # Check if required columns are present
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            st.error(f"🚨 Missing columns: {', '.join(missing_columns)}. Please upload a valid file.")
        else:
            # Selecting the required columns
            df = df[REQUIRED_COLUMNS]

            # Convert date columns to datetime format
            df["Split MD Date Year-Month Label"] = pd.to_datetime(df["Split MD Date Year-Month Label"], errors='coerce')
            df["Validity End Date"] = pd.to_datetime(df["Validity End Date"], errors='coerce')

            # Calculate the difference in days
            df["Date Difference"] = (df["Validity End Date"] - df["Split MD Date Year-Month Label"]).dt.days

            # Categorizing the difference
            def categorize_days(diff):
                if pd.isna(diff):
                    return "NA"
                elif 0 <= diff <= 30:
                    return "0-30 days"
                elif 31 <= diff <= 60:
                    return "30-60 days"
                elif 61 <= diff <= 90:
                    return "60-90 days"
                elif diff > 90:
                    return "90+ days"
                else:
                    return "NA"

            df["Category"] = df["Date Difference"].apply(categorize_days)

            # Adding RC Type column
            df["RC Type"] = df.apply(lambda row: "RC Not Received" if row["Project Status"] in ["Quote Revision", "Final PA Review"] else "RC Received", axis=1)

            # Grouping data for visualization
            rcc = df.groupby(['Category', 'RC Type']) \
                    .agg({
                        'Split Man-Days': 'sum',  # Sum of Man-Days
                        'Service Code': 'count'   # Count occurrences of Service Code
                    }) \
                    .reset_index()

            rcc.columns = ['Category', 'RC Type', 'Man-Days', 'Service Code Count']

            # Sidebar filter
            selected_category = st.sidebar.selectbox("🔍 Select a Category", ["All"] + list(rcc["Category"].unique()))

            # Filter data based on selection
            filtered_df = rcc if selected_category == "All" else rcc[rcc['Category'] == selected_category]

            # Metrics at the top
            total_man_days = filtered_df["Man-Days"].sum()
            total_service_codes = filtered_df["Service Code Count"].sum()
            
            col1, col2 = st.columns(2)
            col1.metric("📅 Total Man-Days", f"{total_man_days:,.0f}")
            col2.metric("📌 Total Service Codes", f"{total_service_codes:,.0f}")

            # Create bar chart with Service Code Count as text labels
            fig = px.bar(
                filtered_df,
                x='Category',
                y='Man-Days',
                color='RC Type',
                text='Service Code Count',  # Show count of Service Codes in each category
                barmode='stack',
                title="📊 Sum of Man-Days & Service Code Count Category-wise",
                color_discrete_map={"RC Received": "#636EFA", "RC Not Received": "#EF553B"}  # Custom colors
            )

            fig.update_traces(texttemplate='%{text}', textposition='outside')

            # Display plot
            st.plotly_chart(fig, use_container_width=True)

            # **Drill-down Feature: Click a Bar to See Service Code Details**
            if selected_category != "All":
                st.subheader(f"📜 Detailed Service Code Breakdown for {selected_category}")
                service_code_counts = df[df['Category'] == selected_category]['Service Code'].value_counts()
                st.dataframe(service_code_counts.to_frame().reset_index().rename(columns={'index': 'Service Code', 'Service Code': 'Count'}), use_container_width=True)

            # Function to export data to Excel
            def convert_df_to_excel(dataframe):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    dataframe.to_excel(writer, index=False, sheet_name="Processed Data")
                return output.getvalue()

            # Function to export data to CSV
            def convert_df_to_csv(dataframe):
                return dataframe.to_csv(index=False).encode('utf-8')

            # Sidebar Download Options
            st.sidebar.subheader("📥 Download Processed Data")
            st.sidebar.download_button(
                label="⬇️ Download Excel",
                data=convert_df_to_excel(df),
                file_name="processed_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.sidebar.download_button(
                label="⬇️ Download CSV",
                data=convert_df_to_csv(df),
                file_name="processed_data.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")












