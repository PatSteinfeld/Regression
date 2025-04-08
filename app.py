import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import io

# ----------- Initialization -----------
if "events_df" not in st.session_state:
    st.session_state.events_df = pd.DataFrame(columns=["ID", "Title", "Start", "End", "Auditor", "Color"])

# ----------- Event Color Map -----------
auditor_colors = {
    "Auditor A": "#1f77b4",
    "Auditor B": "#ff7f0e",
    "Auditor C": "#2ca02c",
    "Auditor D": "#d62728"
}

# ----------- Calendar Section -----------
st.title("📅 Audit Schedule Calendar + Grid")

st.markdown("#### 👉 Drag-select to create new event")

calendar_options = {
    "editable": True,
    "selectable": True,
    "eventStartEditable": True,
    "eventDurationEditable": True,
    "initialView": "timeGridWeek",
    "slotMinTime": "08:00:00",
    "slotMaxTime": "18:00:00",
    "height": 450
}

events = []
for _, row in st.session_state.events_df.iterrows():
    events.append({
        "id": row["ID"],
        "title": row["Title"],
        "start": row["Start"],
        "end": row["End"],
        "color": row["Color"]
    })

cal_response = calendar(
    events=events,
    options=calendar_options,
    key="small_calendar"
)

# ----------- Add New Event -----------
if cal_response.get("select"):
    sel = cal_response["select"]
    with st.form("add_event"):
        st.success("New event selected. Fill below to add.")
        title = st.text_input("Activity Title")
        auditor = st.selectbox("Assign Auditor", list(auditor_colors.keys()))
        add_btn = st.form_submit_button("Add")

        if add_btn:
            new_id = str(datetime.now().timestamp())
            new_row = {
                "ID": new_id,
                "Title": f"{title} - {auditor}",
                "Start": sel["start"],
                "End": sel["end"],
                "Auditor": auditor,
                "Color": auditor_colors[auditor]
            }
            st.session_state.events_df = pd.concat([st.session_state.events_df, pd.DataFrame([new_row])], ignore_index=True)
            st.success("✅ Event added!")

# ----------- Update Events -----------
if cal_response.get("event"):
    for evt in cal_response["event"]:
        idx = st.session_state.events_df["ID"] == evt["id"]
        if idx.any():
            st.session_state.events_df.loc[idx, "Start"] = evt["start"]
            st.session_state.events_df.loc[idx, "End"] = evt["end"]

# ----------- Editable Grid -----------
st.markdown("### 📝 Editable Event Grid")

gb = GridOptionsBuilder.from_dataframe(st.session_state.events_df)
for col in ["Title", "Start", "End", "Auditor"]:
    gb.configure_column(col, editable=True)
gb.configure_column("Auditor", cellEditor="agSelectCellEditor", cellEditorParams={"values": list(auditor_colors.keys())})
gb.configure_column("Delete", headerName="🗑️ Delete", cellRenderer='''(params) => {
    return '<button class="delete-btn">Delete</button>';
}''', editable=False)

grid_response = AgGrid(
    st.session_state.events_df,
    gridOptions=gb.build(),
    update_mode=GridUpdateMode.VALUE_CHANGED,
    fit_columns_on_grid_load=True,
    height=350,
    allow_unsafe_jscode=True,
    reload_data=False
)

# Sync updates
if st.button("🔄 Update from Grid"):
    st.session_state.events_df = grid_response["data"]
    st.success("Grid synced with calendar.")

# Delete button handling
delete_ids = st.multiselect("Select events to delete", st.session_state.events_df["ID"])
if st.button("🗑️ Delete Selected"):
    st.session_state.events_df = st.session_state.events_df[~st.session_state.events_df["ID"].isin(delete_ids)]
    st.success("Deleted selected events!")

# ----------- Export -----------
if st.button("📤 Export to Excel"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        st.session_state.events_df.to_excel(writer, sheet_name="Schedule", index=False)
        workbook = writer.book
        worksheet = writer.sheets["Schedule"]
        format1 = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
        worksheet.set_column("A:F", 20)
    st.download_button("Download Excel", output.getvalue(), file_name="AuditSchedule.xlsx")
















