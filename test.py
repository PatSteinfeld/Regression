import streamlit as st
import pandas as pd
import plotly.express as px
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
            "Project Number"  # Added Project Number
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
        old_res = od.groupby(["Project Planner", "Split MD Date Year-Month Label", "Type", "Project Number"])["Split Man-Days"].sum().reset_index()
        old_res.columns = ["Planner", "Month", "Type", "Project Number", "Man-Days"]
        old_res_1 = od.groupby(['Project Planner', 'Split MD Date Year-Month Label', 'RC_Status', 'RC_Substatus', 'Project Number'])['Split Man-Days'].sum().reset_index()
        old_res_1.columns = ['Planner', 'Month', 'RC_Status', 'RC_Substatus', 'Project Number', 'Man-Days']

        # Displaying the results with categories, hiding Project Number initially
        st.subheader("Performance Insights")

        # Category selection (e.g., by RC Status or Type)
        category = st.selectbox("Select Category to View Details", ['RC_Status', 'Type'])

        if category == 'RC_Status':
            result = old_res_1
            category_column = 'RC_Status'
        else:
            result = old_res
            category_column = 'Type'

        # Displaying the category data
        grouped_data = result.groupby([category_column, "Planner", "Month"]).agg({"Man-Days": "sum"}).reset_index()

        for _, row in grouped_data.iterrows():
            with st.expander(f"{row[category_column]} - {row['Planner']} - {row['Month']}"):
                st.write(f"Man-Days: {row['Man-Days']}")
                st.write(f"Project Number: {row['Project Number']}")  # Showing Project Number when clicked





