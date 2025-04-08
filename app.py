import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from streamlit_calendar import calendar

st.set_page_config(page_title="Audit Scheduler", layout="wide")

if "audit_data" not in st.session_state:
    st.session_state.audit_data = {}
if "site_auditor_info" not in st.session_state:
    st.session_state.site_auditor_info = {}
if "schedule_data" not in st.session_state:
    st.session_state.schedule_data = pd.DataFrame()


def input_generator():
    st.header("📝 Audit Input Generator")
    site_name = st.text_input("Enter Site Name")
    audit_date = st.date_input("Select Proposed Audit Date")
    audit_type = st.selectbox("Select Audit Type", ["IA", "P1", "P2", "P3", "P4", "P5", "RC"])

    st.markdown("#### Define Activities for this Audit")
    activities = st.text_area("Enter activities (one per line)").split("\n")
    core_activities = st.multiselect("Select Core Activities", activities)

    if st.button("Add Audit"):
        if site_name not in st.session_state.audit_data:
            st.session_state.audit_data[site_name] = []

        audit_entry = {
            "Proposed Date": audit_date.strftime("%Y-%m-%d"),
            "Audit Type": audit_type,
            "Activities": {activity: "✔️" for activity in activities if activity.strip()},
            "Core Status": {activity: ("Core" if activity in core_activities else "Non-Core") for activity in activities if activity.strip()}
        }
        st.session_state.audit_data[site_name].append(audit_entry)
        st.success("✅ Audit entry added!")


    st.markdown("#### Define Auditor Information for Site")
    if site_name:
        auditors = st.text_area("Enter auditor names (one per line)").split("\n")
        coded_auditors = st.multiselect("Select Coded Auditors", auditors)
        availability = {}
        for auditor in auditors:
            if auditor.strip():
                mandays = st.number_input(f"Availability for {auditor} (mandays)", min_value=0.0, step=0.5, key=f"{site_name}_{auditor}")
                availability[auditor] = mandays

        if st.button("Save Auditor Info"):
            st.session_state.site_auditor_info[site_name] = {
                "auditors": [a for a in auditors if a.strip()],
                "coded_auditors": coded_auditors,
                "availability": availability
            }
            st.success("✅ Auditor info saved!")


def render_calendar_and_get_updates(df):
    events = []
    for idx, row in df.iterrows():
        start_dt = f"{row['Proposed Date']}T{row['Start Time']}"
        end_dt = f"{row['Proposed Date']}T{row['End Time']}"
        events.append({
            "id": str(idx),
            "title": f"{row['Activity']} ({row['Assigned Auditor']})",
            "start": start_dt,
            "end": end_dt,
        })

    calendar_config = {
        "initialView": "timeGridWeek",
        "editable": True,
        "selectable": True,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "timeGridDay,timeGridWeek,dayGridMonth"
        }
    }

    return calendar(events=events, options=calendar_config)


def schedule_generator():
    st.header("🖖️ Audit Schedule - Interactive Calendar")

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
        calendar_events = render_calendar_and_get_updates(st.session_state.schedule_data)

        st.write("### 📝 Editable Grid")
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
            update_mode=GridUpdateMode.VALUE_CHANGED,
            key="schedule_grid"
        )

        st.session_state.schedule_data = grid_response["data"]

        if "event" in calendar_events and st.button("🔁 Sync Calendar Changes to Table"):
            for event in calendar_events["event"]:
                idx = int(event["id"])
                start_dt = datetime.fromisoformat(event["start"])
                end_dt = datetime.fromisoformat(event["end"])

                st.session_state.schedule_data.at[idx, "Proposed Date"] = start_dt.date().strftime("%Y-%m-%d")
                st.session_state.schedule_data.at[idx, "Start Time"] = start_dt.strftime("%H:%M")
                st.session_state.schedule_data.at[idx, "End Time"] = end_dt.strftime("%H:%M")

            st.success("✅ Synced calendar changes to table!")


# App Navigation
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio("Go to", ["📄 Input Generator", "📅 Schedule Generator"])

if page == "📄 Input Generator":
    input_generator()
elif page == "📅 Schedule Generator":
    schedule_generator()














