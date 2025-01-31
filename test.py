import pandas as pd
import streamlit as st
import plotly.express as px

# Load the Excel file
file_path = "test1234.xlsx"  # Update with the correct path
df = pd.read_excel(file_path, sheet_name='Sheet1')

# Selecting the required columns
columns_needed = ["Project Number", "Project Status", "Split MD Date Year-Month Label", "Split Man-Days", "Validity End Date"]
df = df[columns_needed]

# Converting date columns to datetime format
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
        .agg({'Split Man-Days': 'sum', 'Project Number': lambda x: list(set(x))}) \
        .reset_index()

rcc.columns = ['Category', 'RC Type', 'Man-Days', 'Project Numbers']

# Streamlit UI
st.title("Sum of Man-Days Category-wise")

# Dropdown for selecting category
selected_category = st.selectbox("Select a Category", ["All"] + list(rcc["Category"].unique()))

# Filter data based on selection
filtered_df = rcc if selected_category == "All" else rcc[rcc['Category'] == selected_category]

# Create bar chart
fig = px.bar(
    filtered_df,
    x='Category',
    y='Man-Days',
    color='RC Type',
    text='Man-Days',
    barmode='stack',
    title="Sum of Man-Days Category-wise"
)

fig.update_traces(texttemplate='%{text}', textposition='outside')

# Display plot
st.plotly_chart(fig)

# Display project numbers when a category is selected
if selected_category != "All":
    projects = df[df['Category'] == selected_category]['Project Number'].unique()
    st.write(f"**Projects in {selected_category}:**")
    st.write(", ".join(projects) if projects.size > 0 else "No projects found.")












