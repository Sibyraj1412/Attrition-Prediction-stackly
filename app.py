from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


st.set_page_config(
    page_title="Stackly Workforce Analytics",
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
MODEL_FEATURES = ["Tenure Years", "Department", "Location", "Employment Status"]
WORKBOOK_COLUMN_ALIASES = {
    "Date of Joining": "Joining Date",
    "Designation": "Job Title",
    "Phone Number": "Phone",
    "Status": "Employment Status",
    "Work Location": "Location",
}

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink: #161616; --muted: #5f5a4f; --gold: #c5962e; --gold-bright: #e4b84c; --cream: #f7f2e7; --line: #dfd3b9; --charcoal: #171717; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: var(--ink); }
    h1, h2, h3, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 { font-family: 'Space Grotesk', sans-serif; color: var(--ink) !important; }
    [data-testid="stMarkdownContainer"] p, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
    .stApp { background: linear-gradient(135deg, #f7f2e7 0%, #fffdf8 52%, #f1eadb 100%); }
    [data-testid="stSidebar"] { background: var(--charcoal) !important; border-right: 1px solid #332b1d; }
    [data-testid="stSidebar"] * { color: #f6f0e3 !important; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #c8bfae !important; }
    [data-testid="stSidebar"] [data-baseweb="select"] > div { background: #262626 !important; border: 1px solid #6b5525; }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] { background: #242424; border: 1px solid #6b5525; border-radius: 12px; padding: .35rem; }
    [data-testid="stSidebar"] button { background: #2a2a2a; border: 1px solid #80672c; }
    [data-testid="stSidebar"] button:hover { border-color: var(--gold-bright); color: var(--gold-bright) !important; }
    .block-container { padding-top: 2.2rem; padding-bottom: 3rem; }
    .hero { padding: 1.5rem 0 1rem; border-bottom: 1px solid var(--line); margin-bottom: 1.25rem; animation: rise-in .65s ease-out both; }
    .eyebrow { color: var(--gold); font-size: .78rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
    .hero h1 { font-size: clamp(2.1rem, 4vw, 4rem); line-height: 1; margin: .35rem 0 .6rem; }
    .hero p { color: var(--muted) !important; max-width: 700px; font-size: 1rem; }
    .metric { background: rgba(255,255,255,.86); border: 1px solid var(--line); box-shadow: 0 8px 24px rgba(31, 25, 12, .08); padding: 1rem 1.1rem; border-radius: 12px; min-height: 105px; animation: rise-in .65s ease-out both; }
    .metric:nth-child(2) { animation-delay: .08s; }
    .metric:nth-child(3) { animation-delay: .16s; }
    .metric:nth-child(4) { animation-delay: .24s; }
    .metric-label { color: var(--muted) !important; font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; }
    .metric-value { color: var(--ink) !important; font: 700 2rem 'Space Grotesk'; margin-top: .35rem; }
    .risk-high { color: #b23a2b; font-weight: 700; }
    .risk-medium { color: #b86b00; font-weight: 700; }
    .risk-low { color: #18715d; font-weight: 700; }
    .note { background: #fff8e8; border: 1px solid #e7c978; border-left: 4px solid var(--gold); padding: .8rem 1rem; color: #5a4517; border-radius: 8px; animation: rise-in .7s .28s ease-out both; }
    [data-testid="stDataFrame"], [data-testid="stArrowVegaLiteChart"] { animation: rise-in .7s .36s ease-out both; }
    @keyframes rise-in { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; } }
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
    workbook = workbook.rename(columns=WORKBOOK_COLUMN_ALIASES)
    if "Full Name" not in workbook.columns and {"First Name", "Last Name"}.issubset(workbook.columns):
        workbook["Full Name"] = (
            workbook["First Name"].fillna("").astype(str).str.strip()
            + " "
            + workbook["Last Name"].fillna("").astype(str).str.strip()
        ).str.strip()
    workbook["Employee ID"] = workbook["Employee ID"].fillna("").astype(str).str.strip()
    missing_ids = workbook["Employee ID"].eq("")
    workbook.loc[missing_ids, "Employee ID"] = [
        f"EMP-{index + 1:03d}" for index in workbook.index[missing_ids]
    ]
    workbook["Full Name"] = workbook["Full Name"].where(
        workbook["Full Name"].ne(""), workbook["Employee ID"]
    )
    missing = REQUIRED_COLUMNS.difference(workbook.columns)
    if missing:
        st.error("Missing required columns: " + ", ".join(sorted(missing)))
        st.stop()
    workbook["Joining Date"] = pd.to_datetime(workbook["Joining Date"], errors="coerce")
    if "Attrition" not in workbook.columns:
        workbook["Attrition"] = workbook["Employment Status"].astype(str).str.strip().str.lower().eq("resigned").map({True: "Yes", False: "No"})
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


def add_features(workbook):
    workbook = workbook.copy()
    workbook["Tenure Years"] = ((pd.Timestamp(date.today()) - workbook["Joining Date"]).dt.days / 365.25).clip(lower=0).fillna(0)
    return workbook


def train_logistic_model(workbook):
    model_data = add_features(workbook)
    target_source = "historical Attrition column"
    if "Attrition" in model_data.columns:
        target = model_data["Attrition"].astype(str).str.strip().str.lower().isin({"yes", "y", "true", "1", "left"}).astype(int)
    else:
        target_source = "demo labels generated from the existing screening rules"
        target = model_data.apply(lambda row: int(score_employee(row).iloc[0] >= 30), axis=1)

    if target.nunique() < 2:
        st.error("Logistic Regression needs both attrition and non-attrition examples in the uploaded data.")
        st.stop()

    numeric_features = ["Tenure Years"]
    categorical_features = ["Department", "Location", "Employment Status"]
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), numeric_features),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    model.fit(model_data[MODEL_FEATURES], target)
    model_data["Attrition Probability"] = model.predict_proba(model_data[MODEL_FEATURES])[:, 1]
    model_data["Risk Score"] = (model_data["Attrition Probability"] * 100).round().astype(int)
    model_data["Risk Level"] = pd.cut(
        model_data["Attrition Probability"],
        bins=[-0.01, 0.30, 0.60, 1.01],
        labels=["Low", "Medium", "High"],
    ).astype(str)
    model_data["Risk Signals"] = model_data.apply(lambda row: score_employee(row).iloc[2], axis=1)
    return model_data, target_source


def enrich_data(workbook):
    workbook, _ = train_logistic_model(workbook)
    return workbook


st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Stackly people analytics</div>
      <h1>Workforce analytics</h1>
    <p>A focused workforce workspace for understanding your people, prioritizing retention conversations, and keeping the reasoning visible.</p>
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

employees, target_source = train_logistic_model(load_employee_data(uploaded_file))

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

if True:
    active_count = int(filtered["Employment Status"].astype(str).str.lower().eq("active").sum())
    average_tenure = filtered["Tenure Years"].mean() if not filtered.empty else 0
    department_count = filtered["Department"].nunique()

    st.markdown("### Workforce overview")
    st.caption("A population-level view of the employees currently included by your filters.")
    overview_metrics = st.columns(4)
    overview_values = [
        ("Employees shown", len(filtered)),
        ("Active employees", active_count),
        ("Average tenure", f"{average_tenure:.1f} years"),
        ("Departments", department_count),
    ]
    for column, (label, value) in zip(overview_metrics, overview_values):
        with column:
            st.metric(label, value, border=True)

    if filtered.empty:
        st.info("No employees match the selected filters.")
        st.stop()

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("#### Headcount by department")
            department_counts = filtered["Department"].value_counts().rename("Employees")
            st.bar_chart(department_counts, color="#087f8c")
    with right:
        with st.container(border=True):
            st.markdown("#### Employment status")
            status_counts = filtered["Employment Status"].value_counts().rename("Employees")
            st.bar_chart(status_counts, color="#e76f51")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("#### Workforce by location")
            location_counts = filtered["Location"].value_counts().rename("Employees")
            st.bar_chart(location_counts, color="#c5962e")
    with right:
        with st.container(border=True):
            st.markdown("#### Tenure profile")
            tenure_bins = pd.cut(
                filtered["Tenure Years"],
                bins=[-0.01, 1, 2, 5, float("inf")],
                labels=["Under 1 year", "1-2 years", "2-5 years", "5+ years"],
            )
            tenure_counts = tenure_bins.value_counts().reindex(
                ["Under 1 year", "1-2 years", "2-5 years", "5+ years"],
                fill_value=0,
            ).rename("Employees")
            st.bar_chart(tenure_counts, color="#6b5b95")

    st.markdown("### Employee roster")
    st.dataframe(
        filtered[
            [
                "Employee ID",
                "Full Name",
                "Department",
                "Job Title",
                "Location",
                "Employment Status",
                "Tenure Years",
            ]
        ].sort_values(["Department", "Full Name"]),
        hide_index=True,
        column_config={
            "Tenure Years": st.column_config.NumberColumn("Tenure", format="%.1f years"),
        },
    )
metrics = st.columns(4)
metric_values = [("Employees shown", len(filtered)), ("High risk", high_count), ("Medium risk", medium_count), ("Average score", f"{avg_score:.0f}/100")]
for column, (label, value) in zip(metrics, metric_values):
    with column:
        st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

st.write("")
if "historical" in target_source:
    model_note = '<strong>Logistic Regression:</strong> probabilities are trained from the uploaded historical Attrition column. Risk signals remain visible as supporting context.'
else:
    model_note = '<strong>Demo Logistic Regression:</strong> this workbook has no historical Attrition column, so demo labels are generated from the original screening rules. Replace the demo workbook with historical Attrition Yes/No data for a validated model.'
st.markdown(f'<div class="note">{model_note}</div>', unsafe_allow_html=True)

st.markdown("### Likely to leave")
if priority_employees.empty:
    st.success("No elevated attrition signals found in the current filtered employee list.")
else:
    st.caption("Employees below have elevated predicted probability. The reason column shows the supporting signals contributing to the screening result.")
    priority_view = priority_employees[["Employee ID", "Full Name", "Department", "Job Title", "Risk Score", "Risk Level", "Risk Signals"]]
    st.dataframe(
        priority_view,
        width="stretch",
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
st.dataframe(display, width="stretch", hide_index=True, column_config={"Risk Score": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=100, format="%d")})

st.markdown("### Inspect one employee")
if not filtered.empty:
    selected_id = st.selectbox("Employee", filtered["Employee ID"].tolist(), format_func=lambda value: f"{value} - {filtered.loc[filtered['Employee ID'].eq(value), 'Full Name'].iloc[0]}")
    selected = filtered[filtered["Employee ID"] == selected_id].iloc[0]
    detail_columns = st.columns(4)
    detail_columns[0].metric("Attrition probability", f"{selected['Attrition Probability']:.0%}")
    detail_columns[1].metric("Risk level", selected["Risk Level"])
    detail_columns[2].metric("Status", selected["Employment Status"])
    detail_columns[3].metric("Location", selected["Location"])
    st.caption(f"Signals: {selected['Risk Signals']}")
else:
    st.info("No employee is available for inspection with the current filters.")
