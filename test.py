import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import hmac

# Login Authentication
def check_password():
    """Returns `True` if the user had a correct password."""
    def login_form():
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        if (
            st.session_state["username"] in st.secrets["passwords"]
            and hmac.compare_digest(
                st.session_state["password"],
                st.secrets.passwords[st.session_state["username"]],
            )
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    login_form()
    if "password_correct" in st.session_state:
        st.error("\ud83d\ude15 User not known or password incorrect")
    return False

# Main Application
def main():
    if not check_password():
        st.stop()

    st.title("Planner Performance Insights and Man-Days Category Analysis")

    # Planner Performance Insights Section
    st.header("Upload Excel Files for Planner Performance Insights")
    old_file = st.file_uploader("Upload the old data Excel file", type=["xlsx"], key="old_data")
    new_file = st.file_uploader("Upload the new data Excel file", type=["xlsx"], key="new_data")

    if old_file and new_file:
        old_data = pd.read_excel(old_file)
        new_data = pd.read_excel(new_file)

        required_columns = [
            "Split Man-Days",
            "Activity Sub Status",
            "Split MD Date Year-Month Label",
            "Project Planner",
            "Activity Name",
            "Project Status",
        ]
        if not all(col in old_data.columns for col in required_columns):
            st.error(f"The old file is missing one or more required columns: {required_columns}")
            return
        if not all(col in new_data.columns for col in required_columns):
            st.error(f"The new file is missing one or more required columns: {required_columns}")
            return

        # Processing for Planner Performance Insights (similar to your code)
        od = old_data[required_columns]
        nw = new_data[required_columns]

        # Creating new column to categorize man-days
        od["Type"] = od["Activity Sub Status"].apply(
            lambda x: "Secured" if x == "Customer accepted" else "Unsecured"
        )
        od["RC_Status"] = od.apply(
            lambda row: "RC Not available"
            if row["Activity Name"] == "RC"
            and row["Project Status"] in ["Quote Revision", "Final PA Review"]
            else (
                "RC available"
                if row["Activity Name"] == "RC"
                and row["Project Status"] in ["Reviewed", "Review In Progress"]
                else "Not An RC"
            ),
            axis=1,
        )

        od["RC_Substatus"] = od.apply(
            lambda row: "Secured" if row["RC_Status"] == "RC available" and row["Type"] == "Secured"
            else "Unsecured" if row["RC_Status"] == "RC available" and row["Type"] == "Unsecured"
            else "NA",
            axis=1
        )
        
        nw["Type"] = nw["Activity Sub Status"].apply(
            lambda x: "Secured" if x == "Customer accepted" else "Unsecured"
        )
        nw["RC_Status"] = nw.apply(
            lambda row: "RC Not available"
            if row["Activity Name"] == "RC"
            and row["Project Status"] in ["Quote Revision", "Final PA Review"]
            else (
                "RC available"
                if row["Activity Name"] == "RC"
                and row["Project Status"] in ["Reviewed", "Review In Progress"]
                else "Not An RC"
            ),
            axis=1,
        )

        nw["RC_Substatus"] = nw.apply(
            lambda row: "Secured" if row["RC_Status"] == "RC available" and row["Type"] == "Secured" 
            else "Unsecured" if row["RC_Status"] == "RC available" and row["Type"] == "Unsecured" 
            else "NA",
            axis=1
        )

        # Aggregating results
        old_res = od.groupby(["Project Planner", "Split MD Date Year-Month Label", "Type"])["Split Man-Days"].sum().reset_index()
        old_res.columns = ["Planner", "Month", "Type", "Man-Days"]
        old_res_1 = od.groupby(['Project Planner', 'Split MD Date Year-Month Label', 'RC_Status','RC_Substatus'])['Split Man-Days'].sum().reset_index()
        old_res_1.columns = ['Planner', 'Month', 'RC_Status','RC_Substatus', 'RC_Man-Days']
        new_res = nw.groupby(["Project Planner", "Split MD Date Year-Month Label", "Type"])["Split Man-Days"].sum().reset_index()
        new_res.columns = ["Planner", "Month", "Type", "Man-Days"]
        new_res_1 = nw.groupby(['Project Planner', 'Split MD Date Year-Month Label', 'RC_Status','RC_Substatus'])['Split Man-Days'].sum().reset_index()
        new_res_1.columns = ['Planner', 'Month', 'RC_Status','RC_Substatus', 'RC_Man-Days']

        # Merging results
        comparison_df = pd.merge(
            old_res,
            new_res,
            on=["Planner", "Month", "Type"],
            suffixes=("_old", "_new"),
            how="outer",
        )
        comparison_df_1 = pd.merge(
            old_res_1,
            new_res_1,
            on=["Planner", "Month", "RC_Status", "RC_Substatus"],
            suffixes=("_old", "_new"),
            how="outer",
        ).fillna(0) 

        # Calculating differences
        comparison_df["Man-Days_Diff"] = (
            comparison_df["Man-Days_new"] - comparison_df["Man-Days_old"]
        )
        comparison_df_1["RC_Man-Days_Diff"] = (
            comparison_df_1["RC_Man-Days_new"] - comparison_df_1["RC_Man-Days_old"]
        )

        # Creating pivot tables
        pivot_df = comparison_df.pivot_table(
            index=["Planner", "Month"],
            columns="Type",
            values=["Man-Days_old", "Man-Days_new", "Man-Days_Diff"],
            aggfunc="sum",
            fill_value=0,
        ).reset_index()

        pivot_df_1 = comparison_df_1.pivot_table(
            index=['Planner', 'Month'],
            columns=['RC_Status','RC_Substatus'],  
            values=['RC_Man-Days_old', 'RC_Man-Days_new', 'RC_Man-Days_Diff'],  
            aggfunc='sum',  
            fill_value=0  
        ).reset_index()

        # Flattening column names
        pivot_df.columns = ["_".join(col).strip("_") for col in pivot_df.columns]
        pivot_df_1.columns = [f'{col[0]}_{col[1]}_{col[2]}' for col in pivot_df_1.columns]

        # Output to Streamlit
        st.header("Planner Performance Comparison Results")
        st.dataframe(pivot_df)
        st.dataframe(pivot_df_1)

        # Optional: Save and download results as Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            pivot_df.to_excel(writer, index=False, sheet_name="Comparison Results")
            pivot_df_1.to_excel(writer, index=False, sheet_name="RC Comparison Results")
        st.download_button(
            label="Download Results",
            data=output.getvalue(),
            file_name="comparison_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # Man-Days Category-wise Analysis Section
    st.header("Upload Excel File for Man-Days Category-wise Analysis")
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"], key="man_days")

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, sheet_name="Sheet1")

            REQUIRED_COLUMNS = ["Project Number", "Project Status", "Split MD Date Year-Month Label", "Split Man-Days", "Validity End Date"]

            # Check if required columns are present
            missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing_columns:
                st.error(f"Missing columns: {', '.join(missing_columns)}. Please upload a valid file.")
            else:
                df = df[REQUIRED_COLUMNS]

                # Convert date columns to datetime format
                df["Split MD Date Year-Month Label"] = pd.to_datetime(df["Split MD Date Year-Month Label"], errors='coerce')
                df["Validity End Date"] = pd.to_datetime(df["Validity End Date"], errors='coerce')

                # Calculate the difference in days
                df["Date Difference"] = (df["Validity End Date"] - df["Split MD Date Year-Month Label"]).dt.days
                df = df[df["Date Difference"] >= 0]  # Filter out invalid dates

                # Categorize based on Date Difference
                def categorize_date_diff(days):
                    if days <= 30:
                        return '0-30 days'
                    elif 30 < days <= 60:
                        return '31-60 days'
                    elif 60 < days <= 90:
                        return '61-90 days'
                    else:
                        return 'Over 90 days'

                df["Date Category"] = df["Date Difference"].apply(categorize_date_diff)

                # Group by Date Category for analysis
                df_category_group = df.groupby("Date Category")["Split Man-Days"].sum().reset_index()

                # Visualize category-wise analysis
                fig = px.bar(df_category_group, x="Date Category", y="Split Man-Days", title="Man-Days Category-wise Analysis Based on Date Difference")
                st.plotly_chart(fig)

        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()




