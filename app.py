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
    if "calendar_events" not in st.session_state:
        st.session_state.calendar_events = []

def sync_calendar_to_grid(events):
    updated_rows = []
    for event in events:
        start = datetime.fromisoformat(event["start"])
        end = datetime.fromisoformat(event["end"])
        title_parts = event["title"].split(" - ")
        if len(title_parts) == 2:
            activity, auditor = title_parts
        else:
            activity = title_parts[0]
            auditor = ""

        updated_rows.append({
            "Activity": activity,
            "Assigned Auditor": auditor,
            "Proposed Date": start.strftime("%Y-%m-%d"),
            "Start Time": start.strftime("%H:%M"),
            "End Time": end.strftime("%H:%M")
        })

    df = st.session_state.schedule_data.copy()
    for update in updated_rows:
        mask = df["Activity"] == update["Activity"]
        df.loc[mask, ["Proposed Date", "Start Time", "End Time", "Assigned Auditor"]] = (
            update["Proposed Date"], update["Start Time"], update["End Time"], update["Assigned Auditor"]
        )

    st.session_state.schedule_data = df

# ---------- Scheduler Page ----------
def schedule_generator():
    st.header("🗖️ Audit Schedule - Interactive Calendar (Drag to Reschedule)")

    if not st.session_state.get("audit_data") or not st.session_state.get("site_auditor_info"):
        st.warning("No data available. Please use the Input Generator first.")
        return

    selected_site = st.selectbox("🏢 Select Site", list(st.session_state.audit_data.keys()))
    selected_audit_type = st.selectbox("Select Audit Type", ["IA", "P1", "P2", "P3", "P4", "P5", "RC"])

    auditors = st.session_state.site_auditor_info[selected_site]["auditors"]
    coded_auditors = st.session_state.site_auditor_info[selected_site]["coded_auditors"]
    availability = st.session_state.site_auditor_info[selected_site]["availability"]
    used_mandays = {auditor: 0.0 for auditor in auditors}

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
        st.subheader("📅 Interactive Calendar")
        st.info("Drag or drop events to update times")

        st.session_state.calendar_events = [
            {
                "title": f'{row["Activity"]} - {row["Assigned Auditor"]}',
                "start": f'{row["Proposed Date"]}T{row["Start Time"]}',
                "end": f'{row["Proposed Date"]}T{row["End Time"]}',
                "color": "#1f77b4" if row["Core Status"] == "Core" else "#ff7f0e",
            }
            for _, row in st.session_state.schedule_data.iterrows()
        ]

        updated_events = calendar(
            events=st.session_state.calendar_events,
            options={"editable": True, "selectable": True, "droppable": True},
            key="calendar"
        )

        if st.button("🔄 Sync Calendar with Grid"):
            sync_calendar_to_grid(updated_events)
            st.success("Grid updated with calendar changes!")

        st.subheader("📝 Editable Grid")
        gb = GridOptionsBuilder.from_dataframe(st.session_state.schedule_data)
        editable_columns = ["Activity", "Proposed Date", "Start Time", "End Time", "Assigned Auditor"]
        for col in editable_columns:
            gb.configure_column(col, editable=True)

        gb.configure_column("Assigned Auditor", editable=True, cellEditor="agSelectCellEditor",
                            cellEditorParams={"values": auditors})

        grid_options = gb.build()

        grid_response = AgGrid(
            st.session_state.schedule_data,
            gridOptions=grid_options,
            height=400,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            key="grid"
        )

        st.session_state.schedule_data = grid_response["data"]

# ---------- App Navigation ----------
initialize_session_state()
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a section:", ["Schedule Generator"])

if app_mode == "Schedule Generator":
    schedule_generator()












