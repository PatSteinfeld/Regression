import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_calendar import calendar as streamlit_calendar_component
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ----------- Initialize Session State -----------
def initialize_session_state():
    if "audit_data" not in st.session_state:
        st.session_state.audit_data = {}
    if "schedule_data" not in st.session_state:
        st.session_state.schedule_data = pd.DataFrame()
    if "site_auditor_info" not in st.session_state:
        st.session_state.site_auditor_info = {}
    if "calendar_events" not in st.session_state:
        st.session_state.calendar_events = []

# ----------- Input Generator Page -----------
def input_generator():
    st.header("📋 Auditors Planning Schedule Input Generator")

    num_sites = st.number_input("Number of Sites", min_value=1, step=1, value=1)
    site_activity_data = {}
    site_list = []

    for i in range(num_sites):
        site = st.text_input(f"Enter Site Name {i+1}", key=f"site_{i}")
        if site:
            site_list.append(site)
            st.markdown(f"### Activities for {site}")
            activities = st.text_area(f"Enter Activities for {site} (comma-separated)", key=f"activities_{site}")
            activity_list = [a.strip() for a in activities.split(",") if a.strip()]
            site_activity_data[site] = {}
            for activity in activity_list:
                is_core = st.checkbox(f"Mark '{activity}' as Core", key=f"core_{site}_{activity}")
                site_activity_data[site][activity] = "Core" if is_core else "Non-Core"

    site_auditor_info = {}
    for site in site_list:
        st.markdown(f"### Auditors for {site}")
        auditors = st.text_area(f"Enter auditors for {site} (one per line)", key=f"auditors_{site}").split("\n")
        auditors = [a.strip() for a in auditors if a.strip()]
        coded = st.multiselect(f"Select coded auditors for {site}", auditors, key=f"coded_{site}")
        availability = {}
        for auditor in auditors:
            available = st.number_input(f"Mandays for {auditor}", min_value=0.0, value=1.0, step=0.5, key=f"avail_{site}_{auditor}")
            availability[auditor] = available
        site_auditor_info[site] = {
            "auditors": auditors,
            "coded_auditors": coded,
            "availability": availability
        }

    site_audit_data = {}
    for site in site_list:
        st.markdown(f"### Audits for {site}")
        num_audits = st.number_input(f"Number of audits for {site}", min_value=1, step=1, value=1, key=f"num_audits_{site}")
        site_audit_data[site] = []
        for i in range(num_audits):
            date = st.date_input(f"Proposed Date {i+1} ({site})", key=f"date_{site}_{i}")
            mandays = st.number_input(f"Mandays {i+1} ({site})", min_value=1, step=1, key=f"mandays_{site}_{i}")
            selected = st.multiselect(f"Select Activities {i+1} ({site})", list(site_activity_data[site].keys()), key=f"acts_{site}_{i}")
            audit = {
                "Proposed Date": date.strftime("%Y-%m-%d"),
                "Mandays": mandays,
                "Activities": {act: "✔️" if act in selected else "❌" for act in site_activity_data[site].keys()},
                "Core Status": {act: site_activity_data[site][act] for act in site_activity_data[site].keys()}
            }
            site_audit_data[site].append(audit)

    if st.button("Save Data"):
        st.session_state.audit_data = site_audit_data
        st.session_state.site_auditor_info = site_auditor_info
        st.success("Data saved!")

# ----------- Calendar Schedule Generator -----------
def schedule_generator():
    st.header("📆 Calendar-Based Audit Scheduler")

    if not st.session_state.audit_data:
        st.warning("Please complete the Input Generator first.")
        return

    site = st.selectbox("Select Site", list(st.session_state.audit_data.keys()))
    audits = st.session_state.audit_data[site]
    auditors = st.session_state.site_auditor_info[site]["auditors"]
    coded = st.session_state.site_auditor_info[site]["coded_auditors"]
    avail = st.session_state.site_auditor_info[site]["availability"]

    if st.button("Generate Calendar Schedule"):
        schedule_data = []
        start_time = datetime.now().replace(hour=9, minute=0)

        for audit in audits:
            activities = [a for a, v in audit["Activities"].items() if v == "✔️"]
            for act in activities:
                core = audit["Core Status"][act]
                eligible = coded if core == "Core" else auditors
                assigned = eligible[0] if eligible else ""
                row = {
                    "Site": site,
                    "Activity": act,
                    "Core Status": core,
                    "Proposed Date": audit["Proposed Date"],
                    "Start Time": start_time.strftime("%H:%M"),
                    "End Time": (start_time + timedelta(minutes=90)).strftime("%H:%M"),
                    "Assigned Auditor": assigned,
                    "Allowed Auditors": ", ".join(eligible)
                }
                schedule_data.append(row)
                start_time += timedelta(minutes=90)
                if start_time.strftime("%H:%M") == "13:00":
                    start_time += timedelta(minutes=30)

        st.session_state.schedule_data = pd.DataFrame(schedule_data)

    if not st.session_state.schedule_data.empty:
        # Show calendar
        events = []
        for i, row in st.session_state.schedule_data.iterrows():
            events.append({
                "id": str(i),
                "title": f"{row['Activity']} - {row['Assigned Auditor']}",
                "start": f"{row['Proposed Date']}T{row['Start Time']}",
                "end": f"{row['Proposed Date']}T{row['End Time']}",
                "color": "#2ecc71" if row["Core Status"] == "Core" else "#3498db"
            })

        calendar_options = {
            "editable": True,
            "selectable": True,
            "eventStartEditable": True,
            "eventDurationEditable": True,
            "initialView": "timeGridDay",
            "slotMinTime": "08:00:00",
            "slotMaxTime": "18:00:00",
        }

        st.subheader("📅 Interactive Calendar")
        calendar_response = streamlit_calendar_component(events=events, options=calendar_options, key="calendar")

        if "event" in calendar_response:
            for ev in calendar_response["event"]:
                idx = int(ev["id"])
                start = datetime.fromisoformat(ev["start"])
                end = datetime.fromisoformat(ev["end"])
                st.session_state.schedule_data.at[idx, "Proposed Date"] = start.date().strftime("%Y-%m-%d")
                st.session_state.schedule_data.at[idx, "Start Time"] = start.strftime("%H:%M")
                st.session_state.schedule_data.at[idx, "End Time"] = end.strftime("%H:%M")

        # Show Grid only after button click
        if st.button("📊 Generate Grid from Calendar"):
            st.subheader("📝 Editable Audit Grid")
            gb = GridOptionsBuilder.from_dataframe(st.session_state.schedule_data)
            gb.configure_column("Assigned Auditor", editable=True, cellEditor="agSelectCellEditor",
                                cellEditorParams={"values": auditors})
            for col in ["Activity", "Proposed Date", "Start Time", "End Time"]:
                gb.configure_column(col, editable=True)
            grid_options = gb.build()

            grid_res = AgGrid(
                st.session_state.schedule_data,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.VALUE_CHANGED,
                height=400,
                key="calendar_grid"
            )
            st.session_state.schedule_data = grid_res["data"]

# ----------- App Navigation -----------
initialize_session_state()
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Input Generator", "Schedule Generator"])

if page == "Input Generator":
    input_generator()
else:
    schedule_generator()




















