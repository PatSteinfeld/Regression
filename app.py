import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_calendar import calendar as streamlit_calendar_component
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ----------- Utility Functions ----------- #
def initialize_session_state():
    if "audit_data" not in st.session_state:
        st.session_state.audit_data = {}
    if "schedule_data" not in st.session_state:
        st.session_state.schedule_data = pd.DataFrame()
    if "site_auditor_info" not in st.session_state:
        st.session_state.site_auditor_info = {}
    if "site_list" not in st.session_state:
        st.session_state.site_list = []
    if "site_activity_data" not in st.session_state:
        st.session_state.site_activity_data = {}

def define_common_activities():
    with st.expander("Define Common Activities"):
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
        with st.expander(f"👥 Auditors for Site: {site}"):
            auditors_input = st.text_area(f"Enter Auditors for {site} (One per line)", key=f"{site}_auditors")
            auditors = [a.strip() for a in auditors_input.split('\n') if a.strip()]
            coded_auditors = st.multiselect(f"Select Coded Auditors for {site}", auditors, key=f"{site}_coded")

            st.markdown(f"#### Auditor Availability for {site}")
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

# ----------- Input Generator ----------- #
def input_generator():
    st.header("📋 Auditors Planning Schedule Input Generator")
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
                with st.expander(f"{category} for {site}"):
                    for activity in activities:
                        is_core = st.checkbox(f"Mark '{activity}' as Core", key=f"core_{site}_{activity}")
                        site_activity_data[site][activity] = "Core" if is_core else "Non-Core"

    site_audit_data = {}
    for site in site_list:
        with st.expander(f"🗂️ Audit Details for Site: {site}"):
            num_audits = st.number_input(f"Number of audits for {site}", min_value=1, step=1, value=1, key=f"num_audits_{site}")
            audit_data = []
            for i in range(num_audits):
                audit_type = st.selectbox(f"Select Audit Type {i+1}", ["IA", "P1", "P2", "P3", "P4", "P5", "RC"], key=f"audit_type_{site}_{i}")
                proposed_date = st.date_input(f"Proposed Date {i+1}", key=f"date_{site}_{i}")
                mandays = st.number_input(f"Mandays {i+1}", min_value=1, step=1, key=f"mandays_{site}_{i}")
                selected_activities = {}
                activity_durations = {}
                for activity in site_activity_data[site].keys():
                    is_selected = st.checkbox(activity, key=f"{activity}_{site}_{i}")
                    if is_selected:
                        duration = st.number_input(f"Duration (mins) for {activity}", min_value=30, max_value=240, value=90, step=15, key=f"dur_{activity}_{site}_{i}")
                        selected_activities[activity] = True
                        activity_durations[activity] = duration
                audit_entry = {
                    "Audit Type": audit_type,
                    "Proposed Date": proposed_date.strftime("%Y-%m-%d"),
                    "Mandays": mandays,
                    "Total Hours": mandays * 8,
                    "Activities": {activity: "✔️" if selected_activities.get(activity) else "❌" for activity in site_activity_data[site]},
                    "Core Status": {activity: site_activity_data[site][activity] for activity in selected_activities},
                    "Durations": activity_durations
                }
                audit_data.append(audit_entry)
            site_audit_data[site] = audit_data

    site_auditor_info = define_site_auditors(site_list)

    if st.button("💾 Save & Proceed to Scheduling"):
        st.session_state.audit_data = site_audit_data
        st.session_state.site_auditor_info = site_auditor_info
        st.session_state.site_list = site_list
        st.session_state.site_activity_data = site_activity_data
        st.success("✅ Data saved! Go to 'Schedule Generator' tab.")

# ----------- Calendar Display ----------- #
def render_calendar_and_get_updates(schedule_df):
    events = []
    for idx, row in schedule_df.iterrows():
        events.append({
            "id": str(idx),
            "title": f'{row["Activity"]} - {row["Assigned Auditor"]}',
            "start": f'{row["Proposed Date"]}T{row["Start Time"]}',
            "end": f'{row["Proposed Date"]}T{row["End Time"]}',
            "color": "#1f77b4" if row["Core Status"] == "Core" else "#ff7f0e",
        })

    calendar_options = {
        "initialView": "timeGridDay",  # Only show one day
        "slotMinTime": "08:00:00",
        "slotMaxTime": "18:00:00",
        "editable": True,
        "selectable": True,
        "eventStartEditable": True,
        "eventDurationEditable": True,
        "initialDate": schedule_df["Proposed Date"].iloc[0],  # Show only the date of audit
    }


    st.markdown("### 🗓️ Interactive Calendar")
    calendar_events = streamlit_calendar_component(
        events=events,
        options=calendar_options,
        key="sync_calendar"
    )
    return calendar_events

# ----------- Schedule Generator ----------- #
def schedule_generator():
    st.header("📆 Audit Schedule - Interactive Calendar")

    if not st.session_state.get("audit_data") or not st.session_state.get("site_auditor_info"):
        st.warning("⚠️ No data found. Please complete the Input Generator first.")
        return

    sites = list(st.session_state.audit_data.keys())
    selected_site = st.selectbox("🏢 Select Site", sites)
    selected_audit_type = st.selectbox("🔎 Select Audit Type", ["IA", "P1", "P2", "P3", "P4", "P5", "RC"])

    auditors = st.session_state.site_auditor_info[selected_site]["auditors"]
    coded_auditors = st.session_state.site_auditor_info[selected_site]["coded_auditors"]
    availability = st.session_state.site_auditor_info[selected_site]["availability"]
    used_mandays = {auditor: 0.0 for auditor in auditors}

    if st.button("⚙️ Generate Schedule"):
        schedule_data = []
        start_time = datetime.today().replace(hour=9, minute=0, second=0, microsecond=0)

        for audit in st.session_state.audit_data[selected_site]:
            if audit["Audit Type"] == selected_audit_type:
                activities = [act for act, val in audit["Activities"].items() if val == "✔️"]
                for activity in activities:
                    duration = audit["Durations"].get(activity, 90)
                    core_status = audit["Core Status"].get(activity, "Non-Core")
                    allowed = coded_auditors if core_status == "Core" else auditors

                    # Suggest auditors based on lowest used mandays and availability
                    sorted_auditors = sorted(
                        [a for a in allowed if used_mandays[a] < availability[a]],
                        key=lambda x: used_mandays[x]
                    )

                    # Assign 1 or 2 auditors (you can change this logic as needed)
                    assigned_auditors = sorted_auditors[:2] if len(sorted_auditors) >= 2 else sorted_auditors[:1]

                    # Update manday usage
                    for auditor in assigned_auditors:
                        hours = duration / 60
                        used_mandays[auditor] += round(hours / 8, 2)

                    schedule_data.append({
                        "Site": selected_site,
                        "Activity": activity,
                        "Core Status": core_status,
                        "Proposed Date": audit["Proposed Date"],
                        "Start Time": start_time.strftime('%H:%M'),
                        "End Time": (start_time + timedelta(minutes=duration)).strftime('%H:%M'),
                        "Assigned Auditor": ", ".join(assigned_auditors),
                        "Allowed Auditors": ", ".join(allowed)
                    })

                    start_time += timedelta(minutes=duration)
                    if start_time.time() == datetime.strptime("13:00", "%H:%M").time():
                        start_time += timedelta(minutes=30)

        st.session_state.schedule_data = pd.DataFrame(schedule_data)

    if not st.session_state.schedule_data.empty:
        calendar_events = render_calendar_and_get_updates(st.session_state.schedule_data)

        if "event" in calendar_events:
            for event in calendar_events["event"]:
                idx = int(event["id"])
                start_dt = datetime.fromisoformat(event["start"])
                end_dt = datetime.fromisoformat(event["end"])
                st.session_state.schedule_data.at[idx, "Proposed Date"] = start_dt.date().strftime("%Y-%m-%d")
                st.session_state.schedule_data.at[idx, "Start Time"] = start_dt.strftime("%H:%M")
                st.session_state.schedule_data.at[idx, "End Time"] = end_dt.strftime("%H:%M")

        st.markdown("### 📝 Editable Schedule Table")
        gb = GridOptionsBuilder.from_dataframe(st.session_state.schedule_data)
        editable_cols = ["Activity", "Proposed Date", "Start Time", "End Time", "Assigned Auditor"]
        for col in editable_cols:
            gb.configure_column(col, editable=True)
        gb.configure_column("Assigned Auditor", cellEditor="agSelectCellEditor",
                            cellEditorParams={"values": auditors, "multiple": True})
        grid_response = AgGrid(
            st.session_state.schedule_data,
            gridOptions=gb.build(),
            height=400,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            key="schedule_grid"
        )
        st.session_state.schedule_data = grid_response["data"]

        # Manday Summary
        st.markdown("### 📊 Mandays Used Summary")
        manday_summary = {auditor: round(used_mandays[auditor], 2) for auditor in auditors}
        st.dataframe(pd.DataFrame(list(manday_summary.items()), columns=["Auditor", "Mandays Used"]))
























