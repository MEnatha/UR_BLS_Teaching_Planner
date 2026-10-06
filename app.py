
import streamlit as st
import pandas as pd
from pathlib import Path
import re
from datetime import datetime

st.set_page_config(
    page_title="UR BLS Digital Teaching Planner",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE = Path(__file__).parent
DATA = BASE / "data"

@st.cache_data
def load_data():
    units = pd.read_csv(DATA/"teaching_units.csv")
    weeks = pd.read_csv(DATA/"academic_weeks.csv", parse_dates=["week_start","week_end"])
    events = pd.read_csv(DATA/"academic_events.csv", parse_dates=["start_date","end_date"])
    programmes = pd.read_csv(DATA/"programme_registry.csv")
    staff_master = pd.read_csv(DATA/"staff_master.csv")
    staff_aliases = pd.read_csv(DATA/"staff_alias_mapping.csv")
    workload = pd.read_csv(DATA/"academic_workload_sessions.csv", parse_dates=["teaching_date","timestamp"])
    return units, weeks, events, programmes, staff_master, staff_aliases, workload

units, weeks, events, programmes, staff_master, staff_aliases, workload = load_data()

# Clean numeric display
units["study_year"] = pd.to_numeric(units["study_year"], errors="coerce").astype("Int64")
units["credits"] = pd.to_numeric(units["credits"], errors="coerce")
units["unit_hours_num"] = pd.to_numeric(units["unit_hours"], errors="coerce")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
[data-testid="stMetricValue"] {font-size: 1.65rem;}
.small-note {font-size: 0.88rem; color: #555;}
.status-card {
    border: 1px solid #e5e7eb; border-radius: 10px; padding: 0.9rem 1rem;
    background: #fafafa; margin-bottom: .5rem;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("UR Teaching Planner")
st.sidebar.caption("Prototype V1 • BLS Department")
page = st.sidebar.radio(
    "Navigate",
    ["HoD Dashboard","Academic Calendar","Teaching Plan","Staff Calendar","Workload Monitoring & Reports","Workload & Gaps","Unit Assignment"]
)

st.sidebar.divider()
st.sidebar.markdown("**Prototype academic year:** 2026–2027")
st.sidebar.caption(
    "The imported BLS workbook itself is labelled 2025–2026 internally. "
    "V1 preserves that source note while using the signed 2026–2027 UR calendar for the calendar layer."
)

def parse_staff(team):
    if pd.isna(team) or not str(team).strip():
        return []
    text = str(team)
    # split conservatively; do not claim unit ownership
    parts = re.split(r",|;|&|\band\b", text, flags=re.I)
    clean=[]
    for p in parts:
        p=re.sub(r"\(.*?ML.*?\)","",p,flags=re.I).strip(" .")
        p=re.sub(r"\bmodule leader\b","",p,flags=re.I).strip(" .")
        if len(p) > 2 and p.lower() not in {"all bls staff","all staff"}:
            clean.append(p)
    return clean

# Authoritative staff identities come from the department-reviewed Staff Master.
all_staff = sorted(
    staff_master["verified_name"].fillna(staff_master["canonical_name"]).dropna().astype(str).unique().tolist()
)
staff_count_label = int(staff_master["staff_id"].nunique())

# Map every source spelling/variant in the teaching workbook to one verified identity.
alias_to_verified = {
    str(r["source_canonical_name"]).strip().lower(): str(r["verified_name"]).strip()
    for _, r in staff_aliases.dropna(subset=["source_canonical_name","verified_name"]).iterrows()
}

def verified_staff_for_team(team_text):
    """Return verified staff identities represented in one raw module-team cell."""
    verified = []
    for raw_name in parse_staff(team_text):
        key = str(raw_name).strip().lower()
        name = alias_to_verified.get(key)
        if name and name not in verified:
            verified.append(name)
    return verified

def period_for(row, intake):
    return row["intake1_period"] if intake == "Intake 1" else row["intake2_period"]

def weeks_from_period(text):
    if pd.isna(text) or not str(text).strip():
        return []
    s=str(text)
    nums=[]
    # ranges like week 1 to 5 / week12&13 / week 1-4
    m=re.search(r"week[s]?\s*(\d+)\s*(?:to|-|&)\s*(\d+)", s, flags=re.I)
    if m:
        a,b=int(m.group(1)),int(m.group(2))
        if re.search(r"\bto\b|-", m.group(0), flags=re.I):
            nums=list(range(min(a,b),max(a,b)+1))
        else:
            nums=[a,b]
    else:
        nums=[int(x) for x in re.findall(r"week[s]?\s*(\d+)",s,flags=re.I)]
    return sorted(set(nums))

def week_label(sem, n):
    hit=weeks[(weeks["semester"]==sem)&(weeks["week_number"]==n)]
    if hit.empty:
        return f"Week {n}"
    r=hit.iloc[0]
    return f"Week {n}: {r.week_start:%d %b}–{r.week_end:%d %b %Y}"

def filter_units(df, programme=None, year=None, semester=None):
    out=df.copy()
    if programme and programme!="All":
        out=out[out["programme"]==programme]
    if year and year!="All":
        out=out[out["study_year"]==int(year)]
    if semester and semester!="All":
        out=out[out["semester"]==semester]
    return out

if page == "HoD Dashboard":
    st.title("UR BLS Digital Teaching Planning System")
    st.caption("Academic Year 2026–2027 • Prototype V1")

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Programmes modelled", programmes["programme"].nunique())
    c2.metric("BLS modules imported", units["module_code"].nunique())
    c3.metric("Units imported", len(units))
    c4.metric("Verified department staff", staff_count_label)
    c5.metric("Teaching weeks", len(weeks))
    st.caption("Staff count is based on the department-reviewed Staff Master, not on repeated names in module-team text.")

    st.info(
        "MSc Medical Microbiology Year 1 and Year 2, Intake 1 and Intake 2 are already represented "
        "in the programme/cohort structure. Their module and unit data remain marked as pending until "
        "the MSc teaching plan is supplied."
    )

    left,right=st.columns([1.35,1])
    with left:
        st.subheader("Programme / cohort coverage")
        st.dataframe(programmes, use_container_width=True, hide_index=True)
    with right:
        st.subheader("Calendar profile")
        st.write("**Continuing UG & PG**")
        st.write("Semester 1 teaching: **14 Sep–24 Dec 2026**")
        st.write("Semester 2 teaching: **8 Feb–21 May 2027**")
        st.warning("CMHS Intake 2 uses a special academic calendar; V1 flags it as a separate profile pending the official Intake 2 communiqué.")

    st.subheader("Verified Staff Master")
    st.caption("Department-reviewed identities. Duplicate name variants from the source teaching plan are consolidated under one verified staff record.")
    st.dataframe(
        staff_master[["staff_id","verified_name","title","email","department/unit","active_status"]],
        use_container_width=True, hide_index=True, height=320
    )

    st.subheader("BLS module coverage by study year")
    cov=(units.groupby("study_year")
         .agg(Modules=("module_code","nunique"),Units=("unit_name","count"))
         .reset_index())
    st.bar_chart(cov.set_index("study_year")[["Modules","Units"]])


    st.subheader("Integrated workload planning status")
    w1,w2,w3,w4 = st.columns(4)
    w1.metric("Planning records", len(workload))
    w2.metric("Lecturers represented", workload["lecturer"].nunique())
    w3.metric("Planned contact hours", f'{workload["planned_contact_hours"].sum():.0f}')
    w4.metric("Modules represented", workload["module"].nunique())

    st.subheader("Planning gaps requiring HoD action")
    gaps = pd.DataFrame([
        ["Unit-level staff allocation","Pending","The source workbook lists module teams, but does not map individual staff to each unit."],
        ["Exact session date/time","Pending","Many source cells contain week ranges rather than exact session dates/times."],
        ["CMHS Intake 2 calendar","Pending official source","The signed calendar states that Intake 2 has a special calendar."],
        ["MSc Medical Microbiology teaching plan","Pending source","Programme structure exists; module/unit data not yet provided."],
    ], columns=["Item","Status","Why it matters"])
    st.dataframe(gaps,use_container_width=True,hide_index=True)

elif page == "Academic Calendar":
    st.title("Academic Calendar & Teaching Weeks")
    st.caption("Official UR 2026–2027 calendar layer for Continuing UG & PG")

    st.subheader("Official academic activities")
    show=events.copy()
    show["Start"]=show["start_date"].dt.strftime("%d %b %Y")
    show["End"]=show["end_date"].dt.strftime("%d %b %Y")
    st.dataframe(show[["activity","Start","End","activity_type"]],use_container_width=True,hide_index=True)

    sem=st.selectbox("Semester",["Semester 1","Semester 2"])
    w=weeks[weeks["semester"]==sem].copy()
    w["Teaching week"]=w["week_number"].map(lambda x:f"Week {x}")
    w["Dates"]=w.apply(lambda r:f"{r.week_start:%d %b %Y} – {r.week_end:%d %b %Y}",axis=1)
    st.subheader(f"{sem} teaching weeks")
    st.dataframe(w[["Teaching week","Dates","activity_type"]],use_container_width=True,hide_index=True)

    st.caption(
        "Teaching-week dates are generated from the official semester teaching windows. "
        "They are a system-derived weekly layer, not week-by-week dates printed in the communiqué."
    )

elif page == "Teaching Plan":
    st.title("Teaching Plan Explorer")
    c1,c2,c3,c4 = st.columns(4)
    progs=["All"]+sorted(units["programme"].dropna().unique().tolist())
    programme=c1.selectbox("Programme",progs)
    years=["All"]+[str(x) for x in sorted(units["study_year"].dropna().unique())]
    year=c2.selectbox("Study year",years)
    sem=c3.selectbox("Semester",["All","Semester 1","Semester 2"])
    intake=c4.selectbox("Intake",["Intake 1","Intake 2"])

    f=filter_units(units,programme,year,sem).copy()
    f["Teaching period"]=f.apply(lambda r:period_for(r,intake),axis=1)
    st.metric("Visible units",len(f))
    st.dataframe(
        f[["study_year","module_code","module_name","semester","unit_name","unit_hours",
           "module_team","Teaching period","students"]],
        use_container_width=True,hide_index=True,height=560
    )
    st.warning(
        "The workbook identifies module teams but does not identify which individual staff member owns each unit. "
        "V1 therefore keeps unit staff assignment blank rather than inferring it."
    )

elif page == "Staff Calendar":
    st.title("Personal Staff Teaching Calendar")
    st.caption("Whole-year calendar view filtered to a selected member of a module team")

    if not all_staff:
        st.warning("No staff names were detected.")
    else:
        staff=st.selectbox("Select staff member",all_staff)
        intake=st.selectbox("Intake calendar view",["Intake 1","Intake 2"])
        staff_rows=units[
            units["module_team"].fillna("").apply(lambda x: staff in verified_staff_for_team(x))
        ].copy()

        if staff_rows.empty:
            st.info("No module-team entries found for this staff member.")
        else:
            st.warning(
                "Important: this is a module-team teaching-window view, not yet a confirmed unit assignment calendar. "
                "Unit-level ownership must be entered in the Unit Assignment page."
            )
            entries=[]
            for _,r in staff_rows.iterrows():
                p=period_for(r,intake)
                for n in weeks_from_period(p):
                    hit=weeks[(weeks["semester"]==r["semester"])&(weeks["week_number"]==n)]
                    if not hit.empty:
                        wr=hit.iloc[0]
                        entries.append({
                            "Semester":r["semester"],
                            "Week":int(n),
                            "Dates":f"{wr.week_start:%d %b %Y} – {wr.week_end:%d %b %Y}",
                            "Module":r["module_name"],
                            "Unit":r["unit_name"],
                            "Study Year":r["study_year"],
                            "Source teaching window":p
                        })
            cal=pd.DataFrame(entries)
            if cal.empty:
                st.info("The source teaching periods for this staff member could not yet be converted reliably into teaching-week numbers.")
                st.dataframe(staff_rows[["study_year","module_name","unit_name","intake1_period","intake2_period"]],use_container_width=True,hide_index=True)
            else:
                cal=cal.sort_values(["Semester","Week","Module","Unit"])
                st.dataframe(cal,use_container_width=True,hide_index=True,height=560)


elif page == "Workload Monitoring & Reports":
    st.title("Workload Monitoring & Reports")
    st.caption("Automated reports generated directly from lecturer planning records")

    wf = workload.copy()

    f1,f2,f3,f4 = st.columns(4)
    lecturer_opts = ["All"] + sorted([x for x in wf["lecturer"].dropna().unique().tolist() if str(x).strip()])
    programme_opts = ["All"] + sorted([x for x in wf["programme"].dropna().unique().tolist() if str(x).strip()])
    semester_opts = ["All"] + sorted([x for x in wf["semester"].dropna().unique().tolist() if str(x).strip()])
    intake_opts = ["All"] + sorted([x for x in wf["intake"].dropna().unique().tolist() if str(x).strip()])

    selected_lecturer = f1.selectbox("Lecturer", lecturer_opts)
    selected_programme = f2.selectbox("Programme", programme_opts)
    selected_semester = f3.selectbox("Semester", semester_opts)
    selected_intake = f4.selectbox("Intake", intake_opts)

    if selected_lecturer != "All":
        wf = wf[wf["lecturer"] == selected_lecturer]
    if selected_programme != "All":
        wf = wf[wf["programme"] == selected_programme]
    if selected_semester != "All":
        wf = wf[wf["semester"] == selected_semester]
    if selected_intake != "All":
        wf = wf[wf["intake"] == selected_intake]

    report_type = st.selectbox(
        "Select report",
        [
            "Lecturer workload summary",
            "Module workload summary",
            "Weekly teaching schedule",
            "Upcoming teaching",
            "Sessions due for verification",
            "Progress monitoring",
            "Reminder follow-up"
        ]
    )

    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Sessions", len(wf))
    k2.metric("Planned hours", f'{wf["planned_contact_hours"].sum():.0f}')
    k3.metric("Lecturers", wf["lecturer"].nunique())
    k4.metric("Modules", wf["module"].nunique())
    k5.metric("Upcoming", int((wf["plan_timing"]=="Upcoming").sum()))

    if report_type == "Lecturer workload summary":
        report = (
            wf.groupby(["lecturer","email","rank"], dropna=False)
              .agg(
                  planned_sessions=("record_id","count"),
                  planned_contact_hours=("planned_contact_hours","sum"),
                  modules=("module","nunique"),
                  due_for_verification=("plan_timing", lambda s: (s=="Planned date passed").sum()),
                  upcoming_sessions=("plan_timing", lambda s: (s=="Upcoming").sum()),
              )
              .reset_index()
              .sort_values(["planned_contact_hours","planned_sessions"], ascending=False)
        )
        st.dataframe(report, use_container_width=True, hide_index=True)

    elif report_type == "Module workload summary":
        report = (
            wf.groupby(["module","programme","study_year","semester"], dropna=False)
              .agg(
                  planned_sessions=("record_id","count"),
                  planned_contact_hours=("planned_contact_hours","sum"),
                  lecturers=("lecturer","nunique"),
                  activities=("activity","nunique")
              )
              .reset_index()
              .sort_values(["planned_contact_hours","planned_sessions"], ascending=False)
        )
        st.dataframe(report, use_container_width=True, hide_index=True)

    elif report_type == "Weekly teaching schedule":
        report = wf[
            ["academic_week","teaching_date","start_time","end_time","lecturer",
             "module","unit","activity","planned_contact_hours","teaching_location"]
        ].sort_values(["teaching_date","start_time","lecturer"])
        st.dataframe(report, use_container_width=True, hide_index=True, height=560)

    elif report_type == "Upcoming teaching":
        report = wf[wf["plan_timing"]=="Upcoming"][
            ["teaching_date","start_time","end_time","lecturer","email","module","unit",
             "activity","planned_contact_hours","teaching_location"]
        ].sort_values(["teaching_date","start_time"])
        st.dataframe(report, use_container_width=True, hide_index=True, height=560)

    elif report_type == "Sessions due for verification":
        report = wf[wf["plan_timing"]=="Planned date passed"][
            ["teaching_date","lecturer","email","module","unit","activity",
             "planned_contact_hours","delivery_status","remarks"]
        ].sort_values(["teaching_date","lecturer"])
        st.warning("A past planned date is not automatically treated as completed. These sessions require verification.")
        st.dataframe(report, use_container_width=True, hide_index=True, height=560)

    elif report_type == "Progress monitoring":
        work = wf.copy()
        work["actual_hours_numeric"] = pd.to_numeric(work["actual_hours_delivered"], errors="coerce").fillna(0)
        report = (
            work.groupby(["lecturer","email"], dropna=False)
                .agg(
                    planned_hours=("planned_contact_hours","sum"),
                    actual_hours=("actual_hours_numeric","sum"),
                    planned_sessions=("record_id","count"),
                    completed_sessions=("delivery_status", lambda s: (s=="Completed").sum()),
                    ongoing_sessions=("delivery_status", lambda s: (s=="Ongoing").sum()),
                    not_verified=("delivery_status", lambda s: (s=="Not verified").sum()),
                )
                .reset_index()
        )
        report["progress_percent"] = (
            report["actual_hours"] / report["planned_hours"].replace(0, pd.NA) * 100
        ).fillna(0).round(1)
        report = report.sort_values(["progress_percent","planned_hours"], ascending=[True,False])
        st.dataframe(report, use_container_width=True, hide_index=True)
        st.caption("Progress is calculated only from confirmed actual hours. Current imported records remain Not verified until delivery is confirmed.")

    elif report_type == "Reminder follow-up":
        report = wf[
            ["lecturer","email","teaching_date","module","unit","delivery_status",
             "reminder_needed","reminder_status","last_reminder_date","remarks"]
        ].sort_values(["reminder_needed","teaching_date"], ascending=[False,True])
        st.dataframe(report, use_container_width=True, hide_index=True, height=560)

    st.download_button(
        "Download filtered planning records (CSV)",
        wf.to_csv(index=False).encode("utf-8-sig"),
        file_name="BLS_filtered_workload_report.csv",
        mime="text/csv"
    )

elif page == "Workload & Gaps":
    st.title("Workload & Planning Gaps")
    st.caption("V1 uses module-team membership as a proxy only; confirmed unit workload requires unit-level assignment.")

    proxy=[]
    for staff in all_staff:
        rs=units[
            units["module_team"].fillna("").apply(lambda x: staff in verified_staff_for_team(x))
        ]
        proxy.append([staff,rs["module_code"].nunique(),len(rs),rs["unit_hours_num"].sum(min_count=1)])
    p=pd.DataFrame(proxy,columns=["Staff","Modules in team","Units under those modules","Known unit hours in source"])
    p=p.sort_values(["Modules in team","Units under those modules"],ascending=False)
    st.dataframe(p,use_container_width=True,hide_index=True,height=500)

    st.subheader("Missing unit-hour data")
    missing=units[units["unit_hours_num"].isna()][["study_year","module_code","module_name","unit_name"]]
    st.metric("Units without numeric hours",len(missing))
    st.dataframe(missing,use_container_width=True,hide_index=True,height=320)

elif page == "Unit Assignment":
    st.title("Unit-level Teaching Assignment")
    st.caption("Prototype editor for converting module teams into explicit staff-to-unit assignments")

    cols=["programme","study_year","module_code","module_name","semester","unit_name",
          "unit_hours","assigned_unit_staff","assigned_unit_hours","assigned_teaching_week","assignment_status"]
    edit=units[cols].copy()
    edited=st.data_editor(
        edit,
        use_container_width=True,
        hide_index=True,
        height=560,
        column_config={
            "assignment_status": st.column_config.SelectboxColumn(
                "Assignment status",
                options=["Pending unit-level assignment","Assigned","Confirmed"]
            )
        }
    )
    st.download_button(
        "Download updated unit assignments (CSV)",
        edited.to_csv(index=False).encode("utf-8-sig"),
        file_name="BLS_unit_assignments_updated.csv",
        mime="text/csv"
    )
    st.info(
        "Prototype V1 does not persist edits on the public server. Download the updated CSV after editing. "
        "A later version can store assignments in PostgreSQL with login-based access."
    )

st.divider()
st.caption("UR BLS Digital Teaching Planning System • Prototype V1 • Built for departmental planning review")
