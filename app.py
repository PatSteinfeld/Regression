import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from streamlit_calendar import calendar
import io

st.set_page_config(page_title="Audit Scheduler", layout="wide")

# Initialize session state
if "audit_data" not in st.session_state:
    st.session_state.audit_data = {}
if "site_auditor_info" not in st.session_state:
    st.session_state.site_auditor_info = {}
if "schedule_data" not in st.session_state:
    st.session_state.schedule_data = pd.DataFrame()

# ---------- PAGE: INPUT GENERATOR ----------
def input_generator():
    st.title("📝 Audit Input Generator")
    site_name = st.text_input("Enter Site Name")
    audit_type = st.selectbox("Select Audit Type", ["IA", "P1", "P2", "P3", "P4", "P5", "RC"])
    activities = st.multiselect("Select Activities", ["Opening Meeting", "Document Review", "Process Walkthrough", "Closing Meeting", "Follow-up Review"])
    
    st.markdown("#### ⏱️ Define Duration & Core Activities")
    durations = {}
    core_status = {}
    for act in activities:
        with st.expander(f"⚙️ {act}"):
            durations[act] = st.number_input(f"Duration of {act} (mins)", min_value=30, value=90, step=15, key=act)
            core_status[act] = st.selectbox(f"Is {act} Core?", ["Core", "Non-Core"], key=act + "_core")

    proposed_date = st.date_input("📅 Proposed Audit Date", key="proposed_date")

    if st.button("✅ Add Audit"):
        new_entry = {
            "Audit Type": audit_type,
            "Activities": {act: "✔️" for act in activities},
            "Durations": durations,
            "Core Status": core_status,
            "Proposed Date": proposed_date.strftime("%Y-%m-%d")
        }
        if site_name not in st.session_state.audit_data:
            st.session_state.audit_data[site_name] = []
        st.session_state.audit_data[site_name].append(new_entry)
        st.success(f"Audit added for site: {site_name}")

    if site_name:
        st.markdown("### 👥 Define Auditors & Availability")
        auditors = st.text_area("List Auditors (comma-separated)").split(",")
        coded_auditors = st.multiselect("Select Coded Auditors", auditors)
        availability = {}
        for auditor in auditors:
            if auditor.strip():
                availability[auditor.strip()] = st.number_input(f"Mandays available for {auditor.strip()}", value=3.0, step=0.5, key=auditor)

        if st.button("💾 Save Auditor Info"):
            st.session_state.site_auditor_info[site_name] = {
                "auditors": [a.strip() for a in auditors if a.strip()],
                "coded_auditors": coded_auditors,
                "availability": availability
            }
            st.success("Auditor info saved.")

# ---------- CALENDAR DISPLAY ----------
def render_calendar_and_get_updates(schedule_df):
    events = []
    for idx, row in schedule_df.iterrows():
        start = datetime.strptime(f"{row['Proposed Date']} {row['Start Time']}", "%Y-%m-%d %H:%M")
        end = datetime.strptime(f"{row['Proposed Date']} {row['End Time']}", "%Y-%m-%d %H:%M")
        title = f"{row['Activity']} ({row['Auditor 1']}"
        if row['Auditor 2']:
            title += f" + {row['Auditor 2']}"
        title += ")"
        events.append({
            "id": str(idx),
            "title": title,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "color": "#6c5ce7" if row['Core Status'] == "Core" else "#00b894"
        })

    return calendar(events=events, options={"editable": True, "selectable": True}, key="calendar")

# ---------- PAGE: SCHEDULE GENERATOR ----------
def schedule_generator():
    st.title("📆 Schedule Generator")

    if not st.session_state.get("audit_data") or not st.session_state.get("site_auditor_info"):
        st.warning("Please complete the Input Generator first.")
        return

    sites = list(st.session_state.audit_data.keys())
    selected_site = st.selectbox("🏢 Select Site", sites)
    selected_audit_type = st.selectbox("🔍 Select Audit Type", ["IA", "P1", "P2", "P3", "P4", "P5", "RC"])

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

                    num_auditors = 2 if len(allowed) >= 2 else 1
                    sorted_auditors = sorted(
                        [a for a in allowed if used_mandays[a] < availability[a]],
                        key=lambda x: used_mandays[x]
                    )
                    assigned_auditors = sorted_auditors[:num_auditors]

                    hours = duration / 60
                    for auditor in assigned_auditors:
                        used_mandays[auditor] += round(hours / 8, 2)

                    schedule_data.append({
                        "Site": selected_site,
                        "Activity": activity,
                        "Core Status": core_status,
                        "Proposed Date": audit["Proposed Date"],
                        "Start Time": start_time.strftime('%H:%M'),
                        "End Time": (start_time + timedelta(minutes=duration)).strftime('%H:%M'),
                        "Auditor 1": assigned_auditors[0] if len(assigned_auditors) > 0 else "",
                        "Auditor 2": assigned_auditors[1] if len(assigned_auditors) > 1 else "",
                        "Allowed Auditors": ", ".join(allowed),
                        "Duration (mins)": duration
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
        for col in ["Activity", "Proposed Date", "Start Time", "End Time", "Auditor 1", "Auditor 2"]:
            gb.configure_column(col, editable=True)
        gb.configure_column("Auditor 1", cellEditor="agSelectCellEditor", cellEditorParams={"values": auditors})
        gb.configure_column("Auditor 2", cellEditor="agSelectCellEditor", cellEditorParams={"values": auditors})
        grid_response = AgGrid(
            st.session_state.schedule_data,
            gridOptions=gb.build(),
            height=400,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            key="schedule_grid"
        )
        st.session_state.schedule_data = grid_response["data"]

        st.markdown("### 📊 Mandays Summary")
        mandays = {auditor: 0.0 for auditor in auditors}
        for _, row in st.session_state.schedule_data.iterrows():
            duration = row["Duration (mins)"]
            for auditor in [row["Auditor 1"], row["Auditor 2"]]:
                if auditor:
                    mandays[auditor] += round((duration / 60) / 8, 2)
        manday_df = pd.DataFrame(list(mandays.items()), columns=["Auditor", "Mandays Used"])
        st.dataframe(manday_df)

        st.markdown("### 📥 Download Excel")
        with io.BytesIO() as buffer:
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                st.session_state.schedule_data.to_excel(writer, index=False, sheet_name="Schedule")
                manday_df.to_excel(writer, index=False, sheet_name="Manday Summary")
            st.download_button("📤 Download Full Schedule", buffer.getvalue(), file_name="audit_schedule.xlsx")

# ---------- NAVIGATION ----------
page = st.sidebar.selectbox("📚 Choose Page", ["Input Generator", "Schedule Generator"])
if page == "Input Generator":
    input_generator()
else:
    schedule_generator()


























