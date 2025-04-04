import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_calendar import calendar
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ----------- Utility Functions -----------
def initialize_session_state():
    if "audit_data" not in st.session_state:
        st.session_state.audit_data = {}
    if "schedule_data" not in st.session_state:
        st.session_state.schedule_data = pd.DataFrame()
    if "site_auditor_info" not in st.session_state:
        st.session_state.site_auditor_info = {}

def define_common_activities():
    st.markdown("### Define Common Activities")
    categories = {
        "Audit Planning": st.text_area("Audit Planning Activities (Comma-separated)", "Planning Meeting, Document Review"),
        "Opening Meeting": st.text_area("Opening Meeting Activities (Comma-separated)", "Opening Meeting"),
        "Process Audits": st.text_area("Process Audit Activities (Comma-separated)", "Production, Purchasing, Quality, Warehouse"),
        "Closing Meeting": st.text_area("Closing Meeting Activities (Comma-separated)", "Closing Meeting")
    }
    return {k: [a.strip() for a in v.split(',') if a.strip()] for k, v in categories.items()}

def define_site_auditors(site_list):
    site_auditor_info = {}
    for site in site_list:
        st.markdown(f"### 👥 Auditors for Site: {site}")
        auditors_input = st.text_area(f"Enter Auditors for {site} (One per line)", key=f"{site}_auditors")
        auditors = [a.strip() for a in auditors_input.split('\n') if a.strip()]
        coded_auditors = st.multiselect(f"Select Coded Auditors for {site}", auditors, key=f"{site}_coded")

        st.markdown(f"#### 🌟 Auditor Availability for {site}")
        availability = {}
        for auditor in auditors:
            mandays = st.number_input(f"Available Mandays for {auditor}", min_value=0.0, step=0.5, value=1.0, key=f"{site}_{auditor}_availability")
            availability[auditor] = mandays

        site_auditor_info[site] = {
            "auditors": auditors,
            "coded_auditors": coded_auditors,
            "availability": availability
        }

    return site_auditor_info

def input_generator():
    st.header("Auditors Planning Schedule Input Generator")
    common_activities = define_common_activities()
    num_sites = st.number_input("Number of sites to add", min_value=1, step=1, value=1)

    site_activity_data = {}
    site_list = []

    for s in range(num_sites):
        site = st.text_input(f"Enter Site Name {s+1}", key=f"site_{s}")
        if site:
            site_list.append(site)
            site_activity_data[site] = {}
            for category, activities in common_activities.items():
                st.markdown(f"### {category} for {site}")
                for activity in activities:
                    is_core = st.checkbox(f"Mark '{activity}' as Core", key=f"core_{site}_{activity}")
                    site_activity_data[site][activity] = "Core" if is_core else "Non-Core"

    site_audit_data = {}
    for site in site_list:
        st.markdown(f"## Site: {site}")
        num_audits = st.number_input(f"Number of audits for {site}", min_value=1, step=1, value=1, key=f"num_audits_{site}")
        audit_data = []
        for i in range(num_audits):
            audit_type = st.selectbox(f"Select Audit Type {i+1}", ["IA", "P1", "P2", "P3", "P4", "P5", "RC"], key=f"audit_type_{site}_{i}")
            proposed_date = st.date_input(f"Proposed Date {i+1}", key=f"date_{site}_{i}")
            mandays = st.number_input(f"Mandays {i+1}", min_value=1, step=1, key=f"mandays_{site}_{i}")
            selected_activities = {activity: st.checkbox(activity, key=f"{activity}_{site}_{i}") for activity in site_activity_data[site].keys()}
            audit_entry = {
                "Audit Type": audit_type,
                "Proposed Date": proposed_date.strftime("%Y-%m-%d"),
                "Mandays": mandays,
                "Total Hours": mandays * 8,
                "Activities": {activity: "✔️" if selected else "❌" for activity, selected in selected_activities.items()},
                "Core Status": {activity: site_activity_data[site][activity] for activity in selected_activities}
            }
            audit_data.append(audit_entry)
        site_audit_data[site] = audit_data

    site_auditor_info = define_site_auditors(site_list)

    if st.button("Save Data for Scheduling"):
        st.session_state.audit_data = site_audit_data
        st.session_state.site_auditor_info = site_auditor_info
        st.success("Data saved! Proceed to the Schedule Generator.")

def schedule_generator():
    st.header("🗖️ Audit Schedule - Interactive Calendar")

    if not st.session_state.get("audit_data") or not st.session_state.get("site_auditor_info"):
        st.warning("No data available. Please use the Input Generator first.")
        return

    selected_site = st.selectbox("🏢 Select Site", list(st.session_state.audit_data.keys()))
    selected_audit_type = st.selectbox("Select Audit Type", ["IA", "P1", "P2", "P3", "P4", "P5", "RC"])

    auditors = st.session_state.site_auditor_info[selected_site]["auditors"]
    coded_auditors = st.session_state.site_auditor_info[selected_site]["coded_auditors"]
    availability = st.session_state.site_auditor_info[selected_site]["availability"]
    used_mandays = {auditor: 0.0 for auditor in auditors}

    if not auditors:
        st.warning(f"Please enter auditors for site: {selected_site}")
        return

    if st.button("Generate Schedule"):
        schedule_data = []
        start_time = datetime.today().replace(hour=9, minute=0, second=0, microsecond=0)

        audits = st.session_state.audit_data[selected_site]
        for audit in audits:
            if audit["Audit Type"] == selected_audit_type:
                activities = [activity for activity, status in audit["Activities"].items() if status == "✔️"]
                for activity in activities:
                    core_status = audit["Core Status"].get(activity, "Non-Core")
                    allowed_auditors = coded_auditors if core_status == "Core" else auditors

                    assigned_auditor = ""
                    available_options = [a for a in allowed_auditors if used_mandays[a] < availability[a]]
                    if available_options:
                        assigned_auditor = min(available_options, key=lambda a: used_mandays[a])
                        used_mandays[assigned_auditor] += 0.1875

                    schedule_data.append({
                        "Site": selected_site,
                        "Activity": activity,
                        "Core Status": core_status,
                        "Proposed Date": audit["Proposed Date"],
                        "Start Time": start_time.strftime('%H:%M'),
                        "End Time": (start_time + timedelta(minutes=90)).strftime('%H:%M'),
                        "Assigned Auditor": assigned_auditor,
                        "Allowed Auditors": ", ".join(allowed_auditors)
                    })

                    start_time += timedelta(minutes=90)
                    if start_time.time() == datetime.strptime("13:00", "%H:%M").time():
                        start_time += timedelta(minutes=30)

        st.session_state.schedule_data = pd.DataFrame(schedule_data)

    if not st.session_state.schedule_data.empty:
        st.write("### 📝 Edit Schedule")

        gb = GridOptionsBuilder.from_dataframe(st.session_state.schedule_data)
        editable_columns = ["Activity", "Proposed Date", "Start Time", "End Time", "Assigned Auditor", "Allowed Auditors"]
        for col in editable_columns:
            gb.configure_column(col, editable=True)

        gb.configure_column("Assigned Auditor", editable=True, cellEditor="agSelectCellEditor",
                            cellEditorParams={"values": auditors})
        grid_options = gb.build()

        grid_response = AgGrid(
            st.session_state.schedule_data,
            gridOptions=grid_options,
            height=400,
            update_mode=GridUpdateMode.VALUE_CHANGED
        )

        st.session_state.schedule_data = grid_response["data"]

        events = [
            {
                "title": f'{row["Activity"]} - {row["Assigned Auditor"]}',
                "start": f'{row["Proposed Date"]}T{row["Start Time"]}',
                "end": f'{row["Proposed Date"]}T{row["End Time"]}',
                "color": "#1f77b4" if row["Core Status"] == "Core" else "#ff7f0e",
            }
            for _, row in st.session_state.schedule_data.iterrows()
        ]
        calendar(events, options={"editable": True, "selectable": True})

# ---------- App Navigation ----------
initialize_session_state()
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a section:", ["Input Generator", "Schedule Generator"])

if app_mode == "Input Generator":
    input_generator()
else:
    schedule_generator()











