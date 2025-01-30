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
                st.secrets.passwords[st.session_state["username"]]
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
        st.error("😕 User not known or password incorrect")
    return False

# Main Application
def main():
    if not check_password():
        st.stop()

    st.title("Planner Performance Insights & Man-Days Analysis")

    # Upload Excel Files for Planner Performance Insights
    st.header("Upload Excel Files for Planner Performance Insights")
    old_file = st.file_uploader("Upload Old Data File", type=["xlsx"], key="old_data")
    new_file = st.file_uploader("Upload New Data File", type=["xlsx"], key="new_data")

    if old_file and new_file:
        try:
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
            
            # Validate columns
            for file_name, df in [("Old File", old_data), ("New File", new_data)]:
                missing = [col for col in required_columns if col not in df.columns]
                if missing:
                    st.error(f"{file_name} is missing columns: {', '.join(missing)}")
                    return

            def process_data(df):
                df["Type"] = df["Activity Sub Status"].apply(
                    lambda x: "Secured" if x == "Customer accepted" else "Unsecured"
                )
                df["RC_Status"] = df.apply(
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
                df["RC_Substatus"] = df.apply(
                    lambda row: "Secured" if row["RC_Status"] == "RC available" and row["Type"] == "Secured"
                    else "Unsecured" if row["RC_Status"] == "RC available" and row["Type"] == "Unsecured"
                    else "NA",
                    axis=1
                )
                return df

            old_data = process_data(old_data)
            new_data = process_data(new_data)

            # Grouping and merging results
            def aggregate_results(df, columns, value_col, new_col_name):
                return df.groupby(columns)[value_col].sum().reset_index().rename(columns={value_col: new_col_name})

            old_res = aggregate_results(old_data, ["Project Planner", "Split MD Date Year-Month Label", "Type"], "Split Man-Days", "Man-Days_old")
            new_res = aggregate_results(new_data, ["Project Planner", "Split MD Date Year-Month Label", "Type"], "Split Man-Days", "Man-Days_new")

            comparison_df = pd.merge(old_res, new_res, on=["Project Planner", "Split MD Date Year-Month Label", "Type"], how="outer").fillna(0)
            comparison_df["Man-Days_Diff"] = comparison_df["Man-Days_new"] - comparison_df["Man-Days_old"]

            # Display results
            st.header("Planner Performance Comparison")
            st.data_editor(comparison_df, use_container_width=True, hide_index=True)

            # Download button
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                comparison_df.to_excel(writer, index=False, sheet_name="Comparison Results")
            st.download_button("Download Planner Comparison Data", output.getvalue(), "planner_comparison.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        except Exception as e:
            st.error(f"An error occurred: {e}")

    # Upload Excel File for Man-Days Category-wise Analysis
    st.header("Upload Excel File for Man-Days Category-wise Analysis")
    uploaded_file = st.file_uploader("Upload Man-Days Data", type=["xlsx"], key="man_days")

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, sheet_name="Sheet1")

            REQUIRED_COLUMNS = ["Project Number", "Project Status", "Split MD Date Year-Month Label", "Split Man-Days", "Validity End Date", "Activity Name"]

            missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing_columns:
                st.error(f"Missing columns: {', '.join(missing_columns)}. Please upload a valid file.")
            else:
                df = df[REQUIRED_COLUMNS]

                df["Split MD Date Year-Month Label"] = pd.to_datetime(df["Split MD Date Year-Month Label"], errors='coerce')
                df["Validity End Date"] = pd.to_datetime(df["Validity End Date"], errors='coerce')

                df["Date Difference"] = (df["Validity End Date"] - df["Split MD Date Year-Month Label"]).dt.days
                df = df[df["Date Difference"] >= 0]  

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

                df["RC_Type"] = df.apply(
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

                df_category_group = df.groupby(["Date Category", "RC_Type"])["Split Man-Days"].sum().reset_index()

                fig = px.bar(df_category_group, x="Date Category", y="Split Man-Days", color="RC_Type", title="Man-Days Category-wise Analysis")
                st.plotly_chart(fig)

                st.download_button("Download Category Analysis Data", df_category_group.to_csv(index=False), "man_days_analysis.csv", "text/csv")

        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()










