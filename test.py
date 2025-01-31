import pandas as pd
import streamlit as st
import plotly.express as px
from io import BytesIO

# Streamlit Page Config with Wide Layout
st.set_page_config(page_title="Man-Days Analysis", layout="wide")

# Define required columns
REQUIRED_COLUMNS = ["Project Number", "Service Code", "Project Status", "Split MD Date Year-Month Label", "Split Man-Days", "Validity End Date"]

# Sidebar UI
st.sidebar.header("Upload Your File 📂")
uploaded_file = st.sidebar.file_uploader("Upload an Excel file", type=["xlsx"])

# Main Title
st.title("📊 Man-Days Category-wise Analysis")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name='Sheet1')

        # Check if required columns are present
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            st.error(f"🚨 Missing columns: {', '.join(missing_columns)}. Please upload a valid file.")
        else:
            # Selecting required columns
            df = df[REQUIRED_COLUMNS]

            # Convert date columns to datetime format
            df["Split MD Date Year-Month Label"] = pd.to_datetime(df["Split MD Date Year-Month Label"], errors='coerce')
            df["Validity End Date"] = pd.to_datetime(df["Validity End Date"], errors='coerce')

            # Calculate the difference in days
            df["Date Difference"] = (df["Validity End Date"] - df["Split MD Date Year-Month Label"]).dt.days

            # Categorize the difference
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

            # RC Type categorization
            df["RC Type"] = df.apply(lambda row: "RC Not Received" if row["Project Status"] in ["Quote Revision", "Final PA Review"] else "RC Received", axis=1)

            # Grouping data
            rcc = df.groupby(['Category', 'RC Type']) \
                    .agg({'Split Man-Days': 'sum', 'Service Code': 'count', 'Project Number': lambda x: list(set(x))}) \
                    .reset_index()
            
            rcc.columns = ['Category', 'RC Type', 'Man-Days', 'Service Code Count', 'Project Numbers']

            # Sidebar filters
            selected_category = st.sidebar.selectbox("🔍 Select a Category", ["All"] + list(rcc["Category"].unique()))
            filtered_df = rcc if selected_category == "All" else rcc[rcc['Category'] == selected_category]

            # Metrics at the top
            total_man_days = filtered_df["Man-Days"].sum()
            total_service_codes = filtered_df["Service Code Count"].sum()
            
            col1, col2 = st.columns(2)
            col1.metric("📅 Total Man-Days", f"{total_man_days:,.0f}")
            col2.metric("📌 Total Service Codes", f"{total_service_codes:,.0f}")

            # Bar chart
            fig = px.bar(
                filtered_df,
                x='Category',
                y='Man-Days',
                color='RC Type',
                text='Service Code Count',
                barmode='stack',
                title="📊 Sum of Man-Days & Service Code Count Category-wise",
                color_discrete_map={"RC Received": "#636EFA", "RC Not Received": "#EF553B"}
            )
            fig.update_traces(texttemplate='%{text}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

            # Expandable Project Numbers Section
            if selected_category != "All":
                with st.expander(f"📜 View Project Numbers in {selected_category}"):
                    project_data = df[df['Category'] == selected_category][['Project Number', 'Service Code']].drop_duplicates()
                    st.dataframe(project_data, use_container_width=True)

                    # Download buttons
                    def convert_to_excel(dataframe):
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            dataframe.to_excel(writer, index=False, sheet_name="Project Numbers")
                        return output.getvalue()

                    def convert_to_csv(dataframe):
                        return dataframe.to_csv(index=False).encode('utf-8')
                    
                    st.download_button("⬇️ Download Project Numbers (Excel)", data=convert_to_excel(project_data), file_name=f"Project_Numbers_{selected_category}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    st.download_button("⬇️ Download Project Numbers (CSV)", data=convert_to_csv(project_data), file_name=f"Project_Numbers_{selected_category}.csv", mime="text/csv")

            # Sidebar Downloads
            st.sidebar.subheader("📥 Download Processed Data")
            st.sidebar.download_button("⬇️ Download Excel", data=convert_to_excel(df), file_name="processed_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            st.sidebar.download_button("⬇️ Download CSV", data=convert_to_csv(df), file_name="processed_data.csv", mime="text/csv")
    except Exception as e:
        st.error(f"❌ An error occurred: {e}")












