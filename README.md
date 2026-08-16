# UR BLS Digital Teaching Planning System - Prototype V1

## What V1 includes
- HoD dashboard
- Official 2026-2027 academic calendar layer
- Generated Semester 1 and Semester 2 teaching-week dates
- BLS teaching plan imported at module/unit level
- Programme / study year / intake / semester filters
- Staff calendar based on module-team teaching windows
- Workload/gap view
- Unit-level assignment editor + CSV download
- MSc Medical Microbiology Y1/Y2 and Intake 1/2 represented structurally, with teaching data marked as pending

## Important source notes
1. The uploaded BLS workbook file is named `BLS TEACHING PLAN 2026 2027.xlsx`, but the title inside the BLS sheet says `TEACHING PLAN FOR THE ACADEMIC YEAR 2025-2026`. V1 preserves this discrepancy instead of silently changing the source.
2. The signed 2026-2027 UR calendar is used for the prototype calendar layer.
3. The signed calendar states that CMHS Intake 2 programmes have a special academic calendar. That separate calendar has not yet been supplied, so Intake 2 is flagged as pending rather than invented.
4. The BLS source workbook lists module teams but does not explicitly assign each individual unit to a specific staff member. V1 therefore does not infer unit ownership.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud
1. Create a GitHub repository.
2. Upload the contents of this project folder.
3. In Streamlit Community Cloud, create a new app from the repository.
4. Set the main file path to `app.py`.
5. Deploy and share the generated app URL with the HoD.

## Next inputs needed
- MSc Medical Microbiology teaching plan (Y1 and Y2)
- Official CMHS Intake 2 academic calendar
- Confirmed staff-to-unit assignments
- Exact daily teaching times / rooms if timetable conflict checking is required

## Staff Master
V1 includes `data/staff_master.csv` with canonical staff records. Titles are retained where explicitly present in source text; email and department/unit remain blank for validation; active status defaults to `Unverified`.
