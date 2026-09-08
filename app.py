from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Stackly Attrition Radar",
    page_icon="S",
    layout="wide",
)

DATA_PATH = Path(__file__).parent / "data" / "stackly_employee_details.xlsx"
REQUIRED_COLUMNS = {
    "Employee ID",
    "Full Name",
    "Department",
    "Job Title",
    "Email",
    "Phone",
    "Location",
    "Joining Date",
    "Employment Status",
}

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink: #18212b; --muted: #65717d; --teal: #087f8c; --coral: #e76f51; --cream: #f7f4ee; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: var(--ink); }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; }
    .stApp { background: linear-gradient(135deg, #f7f4ee 0%, #f4f8f5 50%, #edf5f3 100%); }
    .hero { padding: 1.5rem 0 1rem; border-bottom: 1px solid #dce6e2; margin-bottom: 1.25rem; }
    .eyebrow { color: var(--coral); font-size: .78rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
    .hero h1 { font-size: clamp(2.1rem, 4vw, 4rem); line-height: 1; margin: .35rem 0 .6rem; }
    .hero p { color: var(--muted); max-width: 700px; font-size: 1rem; }
    .metric { background: rgba(255,255,255,.7); border: 1px solid #dce6e2; padding: 1rem 1.1rem; border-radius: 10px; min-height: 105px; }
    .metric-label { color: var(--muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; }
    .metric-value { font: 700 2rem 'Space Grotesk'; margin-top: .35rem; }
    .risk-high { color: #b23a2b; font-weight: 700; }
    .risk-medium { color: #b86b00; font-weight: 700; }
    .risk-low { color: #18715d; font-weight: 700; }
    .note { background: #fff8e8; border-left: 4px solid #e0a23a; padding: .8rem 1rem; color: #644d1d; border-radius: 4px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_employee_data(uploaded_file):
    source = uploaded_file if uploaded_file is not None else DATA_PATH
    try:
        workbook = pd.read_excel(source, sheet_name="Employee Details")
    except Exception as exc:
        st.error(f"Could not read the workbook: {exc}")
        st.stop()
    missing = REQUIRED_COLUMNS.difference(workbook.columns)
    if missing:
        st.error("Missing required columns: " + ", ".join(sorted(missing)))
        st.stop()
    workbook["Joining Date"] = pd.to_datetime(workbook["Joining Date"], errors="coerce")
    return workbook


def score_employee(row):
    score = 0
    reasons = []
    joining_date = row["Joining Date"]
    if pd.notna(joining_date):
        tenure_years = max((pd.Timestamp(date.today()) - joining_date).days / 365.25, 0)
        if tenure_years < 1:
            score += 35
            reasons.append("under 1 year tenure")
        elif tenure_years < 2:
            score += 20
            reasons.append("under 2 years tenure")
    status = str(row["Employment Status"]).lower()
    if status == "on leave":
        score += 30
        reasons.append("currently on leave")
    elif status == "probation":
        score += 25
        reasons.append("in probation")
    if str(row["Location"]).lower() == "remote":
        score += 10
        reasons.append("remote location")
    if str(row["Department"]).lower() in {"sales", "customer success"}:
        score += 10
        reasons.append("customer-facing team")
    if score >= 55:
        level = "High"
    elif score >= 30:
        level = "Medium"
    else:
        level = "Low"
    return pd.Series([min(score, 100), level, ", ".join(reasons) or "no elevated signals"])


def enrich_data(workbook):
    workbook = workbook.copy()
    workbook[["Risk Score", "Risk Level", "Risk Signals"]] = workbook.apply(score_employee, axis=1)
    return workbook


st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Stackly people analytics</div>
      <h1>Attrition Radar</h1>
      <p>A clear first pass over employee records: spot elevated risk signals, inspect the people behind the number, and keep the reasoning visible.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Data source")
    uploaded_file = st.file_uploader("Upload an employee workbook", type=["xlsx"])
    st.caption("The included sample workbook is used when no file is uploaded.")
    st.markdown("### Filters")
    st.caption("Use the controls below to narrow the employee view.")

employees = enrich_data(load_employee_data(uploaded_file))

with st.sidebar:
    departments = st.multiselect("Department", sorted(employees["Department"].dropna().unique()), default=[])
    risk_levels = st.multiselect("Risk level", ["High", "Medium", "Low"], default=[])
    locations = st.multiselect("Location", sorted(employees["Location"].dropna().unique()), default=[])

filtered = employees.copy()
if departments:
    filtered = filtered[filtered["Department"].isin(departments)]
if risk_levels:
    filtered = filtered[filtered["Risk Level"].isin(risk_levels)]
if locations:
    filtered = filtered[filtered["Location"].isin(locations)]

high_count = int((filtered["Risk Level"] == "High").sum())
medium_count = int((filtered["Risk Level"] == "Medium").sum())
avg_score = filtered["Risk Score"].mean() if not filtered.empty else 0
priority_employees = filtered[filtered["Risk Level"].isin(["High", "Medium"])].sort_values("Risk Score", ascending=False)

metrics = st.columns(4)
metric_values = [("Employees shown", len(filtered)), ("High risk", high_count), ("Medium risk", medium_count), ("Average score", f"{avg_score:.0f}/100")]
for column, (label, value) in zip(metrics, metric_values):
    with column:
        st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

st.write("")
st.markdown('<div class="note"><strong>Demo model:</strong> this workbook has no historical attrition outcome. Scores are an explainable screening heuristic based on tenure, employment status, location, and team type.</div>', unsafe_allow_html=True)

st.markdown("### Likely to leave")
if priority_employees.empty:
    st.success("No elevated attrition signals found in the current filtered employee list.")
else:
    st.caption("Employees below have elevated screening scores. The reason column shows the signals contributing to each score.")
    priority_view = priority_employees[["Employee ID", "Full Name", "Department", "Job Title", "Risk Score", "Risk Level", "Risk Signals"]]
    st.dataframe(
        priority_view,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Risk Score": st.column_config.ProgressColumn("Risk score", min_value=0, max_value=100, format="%d"),
            "Risk Level": st.column_config.TextColumn("Risk level"),
            "Risk Signals": st.column_config.TextColumn("Why this employee is flagged", width="large"),
        },
    )

left, right = st.columns([1.15, 1])
with left:
    st.markdown("### Risk distribution")
    distribution = filtered["Risk Level"].value_counts().reindex(["High", "Medium", "Low"], fill_value=0)
    st.bar_chart(distribution, color="#087f8c", height=250)
with right:
    st.markdown("### Risk by department")
    if filtered.empty:
        st.info("No employees match the selected filters.")
    else:
        department_view = filtered.groupby("Department")["Risk Score"].mean().sort_values(ascending=False)
        st.bar_chart(department_view, color="#e76f51", height=250)

st.markdown("### Employee risk list")
display = filtered[["Employee ID", "Full Name", "Department", "Job Title", "Location", "Risk Score", "Risk Level", "Risk Signals"]].sort_values("Risk Score", ascending=False)
st.dataframe(display, use_container_width=True, hide_index=True, column_config={"Risk Score": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=100, format="%d")})

st.markdown("### Inspect one employee")
if not filtered.empty:
    selected_id = st.selectbox("Employee", filtered["Employee ID"].tolist(), format_func=lambda value: f"{value} - {filtered.loc[filtered['Employee ID'].eq(value), 'Full Name'].iloc[0]}")
    selected = filtered[filtered["Employee ID"] == selected_id].iloc[0]
    detail_columns = st.columns(4)
    detail_columns[0].metric("Risk score", f"{selected['Risk Score']}/100")
    detail_columns[1].metric("Risk level", selected["Risk Level"])
    detail_columns[2].metric("Status", selected["Employment Status"])
    detail_columns[3].metric("Location", selected["Location"])
    st.caption(f"Signals: {selected['Risk Signals']}")
else:
    st.info("No employee is available for inspection with the current filters.")
