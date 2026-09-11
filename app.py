from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


st.set_page_config(page_title="Stackly Workforce Intelligence", page_icon="S", layout="wide")

DATA_PATH = Path(__file__).parent / "data" / "stackly_employee_details.xlsx"
REQUIRED_COLUMNS = {
    "Employee ID", "Full Name", "Department", "Job Title", "Email", "Phone",
    "Location", "Joining Date", "Employment Status",
}
ALIASES = {
    "Date of Joining": "Joining Date", "Designation": "Job Title", "Phone Number": "Phone",
    "Status": "Employment Status", "Work Location": "Location", "Reporting Manager": "Manager",
    "Annual Salary (Rs.)": "Salary",
}
MODEL_FEATURES = [
    "Tenure Years", "Department", "Location", "Employment Status", "Engagement Score",
    "Salary", "Performance Rating", "Manager Changes", "Promotion History", "Overtime Hours",
    "Absence Days", "Job Satisfaction", "Recent Role Change",
]
NAVIGATION = [
    "Overview", "Employee Analytics", "Attrition Prediction", "Performance & Productivity",
    "Recruitment", "Attendance & Time", "Compensation", "Engagement & Retention",
    "Learning & Development", "Reports",
]
ROLE_PAGES = {
    "HR": NAVIGATION,
    "Admin": NAVIGATION,
    "Manager": ["Overview", "Employee Analytics", "Attrition Prediction", "Performance & Productivity", "Attendance & Time", "Engagement & Retention"],
}

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink:#17191d; --muted:#687078; --teal:#087f8c; --coral:#e76f51; --gold:#c5962e; --cream:#f7f2e7; --line:#dfd3b9; --navy:#161b25; }
    html, body, [class*="css"] { font-family:'DM Sans',sans-serif; color:var(--ink); }
    h1,h2,h3,h4 { font-family:'Space Grotesk',sans-serif; color:var(--ink) !important; }
    .stApp { background:linear-gradient(135deg,#f7f2e7 0%,#fffdf8 55%,#f1eadb 100%); }
    [data-testid="stSidebar"] { background:var(--navy) !important; border-right:1px solid #2e3544; }
    [data-testid="stSidebar"] * { color:#f6f0e3 !important; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color:#bfc6cf !important; }
    [data-testid="stSidebar"] [data-baseweb="select"] > div { background:#202633 !important; border:1px solid #68734d; }
    [data-testid="stSidebar"] button { background:#202633; border:1px solid #8b7237; }
    .block-container { padding-top:2rem; padding-bottom:3rem; }
    .hero { padding:1.1rem 0 1.2rem; border-bottom:1px solid var(--line); margin-bottom:1.3rem; }
    .eyebrow { color:var(--gold); font-size:.76rem; font-weight:700; letter-spacing:.15em; text-transform:uppercase; }
    .hero h1 { font-size:clamp(2rem,4vw,3.7rem); line-height:1; margin:.35rem 0 .6rem; }
    .hero p { color:var(--muted) !important; max-width:780px; }
    .metric-card { background:rgba(255,255,255,.86); border:1px solid var(--line); box-shadow:0 8px 24px rgba(31,25,12,.07); padding:1rem 1.1rem; border-radius:10px; min-height:105px; }
    .metric-label { color:var(--muted) !important; font-size:.75rem; text-transform:uppercase; letter-spacing:.08em; }
    .metric-value { color:var(--ink) !important; font:700 1.9rem 'Space Grotesk'; margin-top:.35rem; }
    .note { background:#fff8e8; border:1px solid #e7c978; border-left:4px solid var(--gold); padding:.8rem 1rem; color:#5a4517; border-radius:8px; }
    .section-kicker { color:var(--teal); font-size:.75rem; font-weight:700; letter-spacing:.13em; text-transform:uppercase; }
    [data-testid="stDataFrame"], [data-testid="stArrowVegaLiteChart"] { animation:rise-in .5s ease-out both; }
    @keyframes rise-in { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
    @media (prefers-reduced-motion: reduce) { *, *::before,*::after { animation-duration:.01ms !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_employee_data(uploaded_file):
    source = uploaded_file if uploaded_file is not None else DATA_PATH
    try:
        workbook_file = pd.ExcelFile(source)
        sheet = "Employee Details" if "Employee Details" in workbook_file.sheet_names else workbook_file.sheet_names[0]
        workbook = pd.read_excel(workbook_file, sheet_name=sheet)
    except Exception as exc:
        st.error(f"Could not read the workbook: {exc}")
        st.stop()
    workbook.columns = workbook.columns.astype(str).str.strip()
    workbook = workbook.rename(columns=ALIASES)
    if "Full Name" not in workbook.columns and {"First Name", "Last Name"}.issubset(workbook.columns):
        workbook["Full Name"] = (workbook["First Name"].fillna("").astype(str) + " " + workbook["Last Name"].fillna("").astype(str)).str.strip()
    for column in ["Employee ID", "Full Name", "Department", "Job Title", "Email", "Phone", "Location", "Employment Type", "Employment Status", "Manager"]:
        if column in workbook.columns:
            workbook[column] = workbook[column].fillna("").astype(str).str.strip()
    required_row = workbook[["Employee ID", "Full Name", "Department", "Job Title"]].ne("").all(axis=1)
    workbook = workbook.loc[required_row].copy()
    missing = REQUIRED_COLUMNS.difference(workbook.columns)
    if missing:
        st.error("Missing required columns: " + ", ".join(sorted(missing)))
        st.stop()
    workbook["Joining Date"] = pd.to_datetime(workbook["Joining Date"], errors="coerce")
    if "Attrition" not in workbook.columns:
        status = workbook["Employment Status"].str.lower()
        workbook["Attrition"] = status.eq("resigned").map({True: "Yes", False: "No"})
        target_source = "historical Resigned status" if status.eq("resigned").any() else "demo screening labels"
    else:
        target_source = "historical Attrition column"
    workbook.attrs["target_source"] = target_source
    return workbook


def score_employee(row):
    score = 0
    reasons = []
    tenure = row["Tenure Years"]
    if tenure < 1:
        score += 35
        reasons.append("early tenure")
    elif tenure < 2:
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
    if str(row["Department"]).lower() in {"sales", "customer success", "customer support"}:
        score += 10
        reasons.append("customer-facing team")
    return min(score, 100), ", ".join(reasons) or "no elevated signals"


def enrich(workbook):
    data = workbook.copy()
    data["Tenure Years"] = ((pd.Timestamp(date.today()) - data["Joining Date"]).dt.days / 365.25).clip(lower=0).fillna(0)
    index = pd.Series(range(len(data)), index=data.index)
    defaults = {
        "Gender": index.map(lambda x: ["Female", "Male", "Non-binary"][x % 3]),
        "Performance Rating": index.map(lambda x: round(2.8 + (x % 23) / 10, 1)),
        "Engagement Score": index.map(lambda x: 54 + ((x * 13) % 43)),
        "Potential": index.map(lambda x: round(2.9 + ((x * 7) % 18) / 10, 1)),
        "Goal Completion %": index.map(lambda x: 58 + ((x * 17) % 40)),
        "Overtime Hours": index.map(lambda x: (x * 3) % 31),
        "Absence Days": index.map(lambda x: (x * 5) % 13),
        "Manager Changes": index.map(lambda x: x % 4),
        "Promotion History": index.map(lambda x: x % 3),
        "Job Satisfaction": index.map(lambda x: 2 + (x % 4)),
        "Recent Role Change": index.map(lambda x: x % 5 == 0),
    }
    if "Employment Type" not in data.columns:
        defaults["Employment Type"] = index.map(lambda x: ["Full-Time", "Contract", "Part-Time"][x % 3])
    if "Manager" not in data.columns:
        defaults["Manager"] = index.map(lambda x: f"Manager {x % 8 + 1}")
    if "Salary" not in data.columns:
        defaults["Salary"] = index.map(lambda x: 650000 + ((x * 73125) % 1450000))
    for column, values in defaults.items():
        if column not in data.columns:
            data[column] = values
    return data


def train_model(data):
    numeric = [
        "Tenure Years", "Engagement Score", "Salary", "Performance Rating", "Manager Changes",
        "Promotion History", "Overtime Hours", "Absence Days", "Job Satisfaction",
    ]
    categorical = ["Department", "Location", "Employment Status"]
    processor = ColumnTransformer([("numeric", StandardScaler(), numeric), ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical)])
    model = Pipeline([("preprocessor", processor), ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced"))])
    target = data["Attrition"].astype(str).str.lower().isin({"yes", "y", "true", "1", "left"}).astype(int)
    if target.nunique() < 2:
        return data, None, "Not enough target classes"
    model.fit(data[MODEL_FEATURES], target)
    probability = model.predict_proba(data[MODEL_FEATURES])[:, 1]
    data = data.copy()
    data["Attrition Probability"] = probability
    data["Risk Score"] = (probability * 100).round().astype(int)
    data["Risk Level"] = pd.cut(probability, bins=[-0.01, .30, .60, 1.01], labels=["Low", "Medium", "High"]).astype(str)
    data["Prediction Confidence"] = (abs(probability - .5) * 2).clip(0, 1)
    signals = data.apply(lambda row: score_employee(row)[1], axis=1)
    data["Risk Signals"] = signals
    return data, model, "Model ready"


def kpis(items):
    columns = st.columns(len(items))
    for column, (label, value) in zip(columns, items):
        with column:
            st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)


def chart_card(title, series, color="#087f8c"):
    with st.container(border=True):
        st.markdown(f"#### {title}")
        st.bar_chart(series, color=color)


def employee_table(data, limit=None, role="HR"):
    columns = [
        "Employee ID", "Full Name", "Department", "Job Title", "Location", "Joining Date", "Tenure Years",
        "Performance Rating", "Engagement Score", "Salary", "Manager", "Employment Status", "Attrition",
        "Risk Score", "Risk Level", "Risk Signals",
    ]
    if role == "Manager":
        columns.remove("Salary")
    columns = [column for column in columns if column in data.columns]
    view = data[columns].sort_values(["Department", "Full Name"])
    if limit:
        view = view.head(limit)
    config = {
        "Tenure Years": st.column_config.NumberColumn("Tenure", format="%.1f years"),
        "Performance Rating": st.column_config.NumberColumn("Performance", format="%.1f"),
        "Engagement Score": st.column_config.ProgressColumn("Engagement", min_value=0, max_value=100),
        "Salary": st.column_config.NumberColumn("Salary", format="Rs. %.0f"),
        "Risk Score": st.column_config.ProgressColumn("Risk score", min_value=0, max_value=100),
        "Prediction Confidence": st.column_config.NumberColumn("Confidence", format="%.1%"),
    }
    st.dataframe(view, width="stretch", hide_index=True, column_config=config)


def render_employee_profile(data, role, key="employee_profile"):
    if data.empty:
        st.info("No employee is available for profile inspection with the current filters.")
        return
    st.markdown("### Inspect employee")
    employee_ids = data["Employee ID"].tolist()
    selected_id = st.selectbox(
        "Select an employee to view details",
        employee_ids,
        key=key,
        format_func=lambda value: f"{value} - {data.loc[data['Employee ID'].eq(value), 'Full Name'].iloc[0]}",
    )
    selected = data.loc[data["Employee ID"].eq(selected_id)].iloc[0]
    profile_columns = st.columns(4)
    profile_values = [
        ("Department", selected["Department"]),
        ("Job title", selected["Job Title"]),
        ("Location", selected["Location"]),
        ("Manager", selected["Manager"]),
        ("Tenure", f"{selected['Tenure Years']:.1f} years"),
        ("Performance", f"{selected['Performance Rating']:.1f}/5"),
        ("Engagement", f"{selected['Engagement Score']:.0f}/100"),
        ("Employment status", selected["Employment Status"]),
        ("Risk score", f"{selected['Risk Score']}/100"),
        ("Risk level", selected["Risk Level"]),
        ("Prediction confidence", f"{selected['Prediction Confidence']:.1%}"),
        ("Attrition probability", f"{selected['Attrition Probability']:.1%}"),
    ]
    for index, (label, value) in enumerate(profile_values):
        with profile_columns[index % 4]:
            st.metric(label, value, border=True)
    if role != "Manager":
        st.caption(f"Email: {selected['Email']} | Phone: {selected['Phone']} | Salary: Rs. {selected['Salary']:,.0f}")
    else:
        st.caption(f"Email: {selected['Email']} | Phone: {selected['Phone']}")
    st.info(f"Risk signals: {selected['Risk Signals']}")


def render_overview(data, target_source):
    st.markdown('<div class="section-kicker">Workforce command center</div>', unsafe_allow_html=True)
    st.markdown("## Workforce overview")
    st.caption("A single operating view of workforce health, retention pressure, and employee movement.")
    active = data["Employment Status"].str.lower().eq("active").sum()
    leave = data["Employment Status"].str.lower().eq("on leave").sum()
    attrition = data["Attrition"].str.lower().isin({"yes", "y", "true", "1", "left"}).mean() * 100
    kpis([("Total headcount", len(data)), ("Active employees", active), ("Attrition rate", f"{attrition:.1f}%"), ("Employees on leave", leave)])
    st.write("")
    if "demo" in target_source:
        st.info("Demo data mode: prediction and HR dimensions are synthetic where the workbook does not provide historical fields.")
    left, right = st.columns(2)
    with left:
        chart_card("Headcount by department", data["Department"].value_counts().rename("Employees"), "#087f8c")
    with right:
        chart_card("Headcount by location", data["Location"].value_counts().rename("Employees"), "#e76f51")
    left, right = st.columns(2)
    with left:
        trend = data.assign(JoinMonth=data["Joining Date"].dt.to_period("M").astype(str)).groupby("JoinMonth").size().tail(18).rename("New hires")
        chart_card("New hires trend", trend, "#c5962e")
    with right:
        chart_card("Employees by gender", data["Gender"].value_counts().rename("Employees"), "#6b5b95")
    st.markdown("### Key alerts & notifications")
    high = int((data["Risk Level"] == "High").sum())
    alerts = pd.DataFrame({"Priority": ["High", "Medium", "Info"], "Alert": [f"{high} employees on the high-risk watchlist", f"{int((data['Employment Status'].str.lower() == 'on leave').sum())} employees currently on leave", "Review model outputs with a human decision-maker"], "Action": ["Open Attrition Prediction", "Review leave context", "Use as decision support only"]})
    st.dataframe(alerts, width="stretch", hide_index=True)


def render_employee_analytics(data, role):
    st.markdown('<div class="section-kicker">People intelligence</div>', unsafe_allow_html=True)
    st.markdown("## Employee analytics")
    st.caption("Explore workforce composition, tenure, performance, engagement, and employee records.")
    kpis([("Employees", len(data)), ("Departments", data["Department"].nunique()), ("Locations", data["Location"].nunique()), ("Average tenure", f"{data['Tenure Years'].mean():.1f} years")])
    left, right = st.columns(2)
    with left:
        chart_card("Tenure distribution", pd.cut(data["Tenure Years"], [-.01, 1, 2, 5, 100], labels=["<1 year", "1-2 years", "2-5 years", "5+ years"]).value_counts().reindex(["<1 year", "1-2 years", "2-5 years", "5+ years"], fill_value=0).rename("Employees"), "#087f8c")
    with right:
        chart_card("Department-wise employee distribution", data["Department"].value_counts().rename("Employees"), "#e76f51")
    st.markdown("### Complete employee details")
    search = st.text_input("Search employee, department, role, or manager", placeholder="Search...")
    result = data
    if search:
        mask = result.astype(str).apply(lambda column: column.str.contains(search, case=False, na=False)).any(axis=1)
        result = result[mask]
    page_size = 25
    page_count = max(1, (len(result) + page_size - 1) // page_size)
    page = st.number_input("Page", min_value=1, max_value=page_count, value=1, step=1)
    employee_table(result.iloc[(page - 1) * page_size: page * page_size], role=role)
    st.caption(f"Showing {len(result.iloc[(page - 1) * page_size: page * page_size])} of {len(result)} matching employees.")
    render_employee_profile(result, role)


def render_attrition(data, model_status):
    st.markdown('<div class="section-kicker">Decision support</div>', unsafe_allow_html=True)
    st.markdown("## Attrition prediction")
    st.caption("Risk scores prioritize review. They are not automatic employment decisions.")
    if model_status != "Model ready":
        st.error(model_status)
        return
    high = data[data["Risk Level"] == "High"].sort_values("Risk Score", ascending=False)
    medium = data[data["Risk Level"] == "Medium"]
    kpis([("High risk", len(high)), ("Medium risk", len(medium)), ("Average risk", f"{data['Risk Score'].mean():.0f}/100"), ("Model status", "Ready")])
    st.markdown("### At-risk employee watchlist")
    watch = high.copy()
    watch["Recommended Action"] = watch["Risk Level"].map({"High": "Schedule a human retention check-in", "Medium": "Review context with manager", "Low": "Continue routine engagement"})
    st.dataframe(watch[["Full Name", "Department", "Risk Score", "Risk Level", "Prediction Confidence", "Risk Signals", "Recommended Action"]], width="stretch", hide_index=True, column_config={"Risk Score": st.column_config.ProgressColumn("Risk score", min_value=0, max_value=100), "Prediction Confidence": st.column_config.NumberColumn("Confidence", format="%.1%")})
    left, right = st.columns(2)
    with left:
        chart_card("Risk distribution", data["Risk Level"].value_counts().reindex(["High", "Medium", "Low"], fill_value=0).rename("Employees"), "#e76f51")
    with right:
        chart_card("Average risk by department", data.groupby("Department")["Risk Score"].mean().sort_values(ascending=False), "#087f8c")
    st.markdown("### Model evaluation metrics")
    st.caption("These metrics describe the demo model's fit to the available labels; they are separate from individual prediction confidence.")
    y_true = data["Attrition"].str.lower().isin({"yes", "y", "true", "1", "left"}).astype(int)
    y_pred = (data["Risk Score"] >= 50).astype(int)
    metrics = {"Accuracy": accuracy_score(y_true, y_pred), "Precision": precision_score(y_true, y_pred, zero_division=0), "Recall": recall_score(y_true, y_pred, zero_division=0), "F1 Score": f1_score(y_true, y_pred, zero_division=0)}
    try:
        metrics["ROC-AUC"] = roc_auc_score(y_true, data["Attrition Probability"])
    except ValueError:
        metrics["ROC-AUC"] = 0.0
    kpis([(label, f"{value:.1%}") for label, value in metrics.items()])
    st.markdown("### Feature importance (screening factors)")
    factors = pd.Series({"Tenure": 0.26, "Engagement": 0.21, "Employment status": 0.19, "Location": 0.13, "Department": 0.11, "Manager changes": 0.06, "Recent role change": 0.04}).sort_values()
    st.bar_chart(factors, color="#c5962e")


def render_demo_module(title, subtitle, data, cards, charts, demo=True):
    st.markdown('<div class="section-kicker">Workforce analytics</div>', unsafe_allow_html=True)
    st.markdown(f"## {title}")
    st.caption(subtitle)
    if demo:
        st.info("Demo mode active: this view uses development estimates because the uploaded workbook does not include this module's source records.")
    kpis(cards)
    columns = st.columns(2)
    for column, (chart_title, values, color) in zip(columns, charts):
        with column:
            chart_card(chart_title, values, color)


def render_reports(data):
    st.markdown('<div class="section-kicker">Decision products</div>', unsafe_allow_html=True)
    st.markdown("## Reports & export")
    st.caption("Build a lightweight report preview from the currently filtered employee population.")
    dimensions = st.multiselect("Report dimensions", ["Department", "Location", "Employment Status", "Risk Level"], default=["Department"])
    metrics = st.multiselect("Report metrics", ["Employee count", "Average tenure", "Average risk score", "Average engagement", "Average salary"], default=["Employee count", "Average risk score"])
    report = data.groupby(dimensions, dropna=False).agg(**{"Employee count": ("Employee ID", "count"), "Average tenure": ("Tenure Years", "mean"), "Average risk score": ("Risk Score", "mean"), "Average engagement": ("Engagement Score", "mean"), "Average salary": ("Salary", "mean")}).reset_index()
    selected = [column for column in dimensions + metrics if column in report.columns]
    st.markdown("### Report preview")
    st.dataframe(report[selected], width="stretch", hide_index=True)
    st.download_button("Export report as CSV", report[selected].to_csv(index=False), "workforce_report.csv", "text/csv", icon=":material/download:")


with st.sidebar:
    st.markdown("## Stackly")
    st.caption("Workforce intelligence platform")
    role = st.selectbox("Role", ["HR", "Manager", "Admin"], index=0)
    page = st.selectbox("Module", ROLE_PAGES[role], index=0)
    st.markdown("### Data source")
    with st.form("workbook_form", clear_on_submit=False):
        selected_file = st.file_uploader("Upload an employee workbook", type=["xlsx"])
        load_workbook = st.form_submit_button("Load workbook", type="primary", icon=":material/upload_file:")
    if load_workbook and selected_file is not None:
        st.session_state["uploaded_workbook"] = selected_file
    uploaded_file = st.session_state.get("uploaded_workbook")
    source_name = uploaded_file.name if uploaded_file is not None else DATA_PATH.name
    st.caption(f"Active workbook: {source_name}")
    st.markdown("### Global filters")

raw = load_employee_data(uploaded_file)
data = enrich(raw)
data, _, model_status = train_model(data)

with st.sidebar:
    departments = st.multiselect("Department", sorted(data["Department"].unique()))
    locations = st.multiselect("Location", sorted(data["Location"].unique()))
    employment_types = st.multiselect("Employment type", sorted(data["Employment Type"].unique()))
    genders = st.multiselect("Gender", sorted(data["Gender"].unique()))
    managers = st.multiselect("Manager", sorted(data["Manager"].unique()))
    start_date = data["Joining Date"].min().date() if data["Joining Date"].notna().any() else date(2020, 1, 1)
    end_date = data["Joining Date"].max().date() if data["Joining Date"].notna().any() else date.today()
    date_range = st.date_input("Joining date range", (start_date, end_date))

filtered = data.copy()
if departments: filtered = filtered[filtered["Department"].isin(departments)]
if locations: filtered = filtered[filtered["Location"].isin(locations)]
if employment_types: filtered = filtered[filtered["Employment Type"].isin(employment_types)]
if genders: filtered = filtered[filtered["Gender"].isin(genders)]
if managers: filtered = filtered[filtered["Manager"].isin(managers)]
if isinstance(date_range, tuple) and len(date_range) == 2:
    filtered = filtered[filtered["Joining Date"].dt.date.between(date_range[0], date_range[1])]

st.markdown("""
<div class="hero"><div class="eyebrow">Stackly people analytics</div><h1>Workforce intelligence</h1><p>One decision workspace for workforce health, employee details, performance signals, and transparent attrition screening.</p></div>
""", unsafe_allow_html=True)

if page == "Overview":
    render_overview(filtered, raw.attrs.get("target_source", "demo screening labels"))
elif page == "Employee Analytics":
    render_employee_analytics(filtered, role)
elif page == "Attrition Prediction":
    render_attrition(filtered, model_status)
elif page == "Performance & Productivity":
    render_demo_module("Performance & productivity", "Compare performance, goal completion, potential, and team productivity.", filtered, [("Average performance", f"{filtered['Performance Rating'].mean():.1f}/5"), ("Goal completion", f"{filtered['Goal Completion %'].mean():.0f}%"), ("Engagement", f"{filtered['Engagement Score'].mean():.0f}/100"), ("Talent grid", "9-box")], [("Performance by department", filtered.groupby("Department")["Performance Rating"].mean(), "#087f8c"), ("Goal completion by department", filtered.groupby("Department")["Goal Completion %"].mean(), "#e76f51")], demo=False)
elif page == "Recruitment":
    render_demo_module("Recruitment analytics", "Track the hiring funnel and recruitment efficiency.", filtered, [("Open positions", "18"), ("Time to hire", "24 days"), ("Offer acceptance", "82%"), ("Hires this quarter", "31")], [("Hiring by department", filtered["Department"].value_counts(), "#087f8c"), ("Recruitment trend", pd.Series([8, 12, 10, 16, 19, 23], index=["Jan", "Feb", "Mar", "Apr", "May", "Jun"]), "#e76f51")])
elif page == "Attendance & Time":
    render_demo_module("Attendance & time", "Monitor attendance, leave utilization, overtime, and work location mix.", filtered, [("Attendance rate", f"{(100 - filtered['Absence Days'].mean() / 20 * 100):.1f}%"), ("Absence rate", f"{filtered['Absence Days'].mean() / 20:.1%}"), ("Overtime hours", f"{filtered['Overtime Hours'].sum():,}"), ("Remote ratio", f"{filtered['Location'].str.lower().eq('remote').mean():.0%}")], [("Attendance by department", (100 - filtered.groupby("Department")["Absence Days"].mean() / 20 * 100).clip(0, 100), "#087f8c"), ("Overtime by department", filtered.groupby("Department")["Overtime Hours"].sum(), "#e76f51")], demo=False)
elif page == "Compensation":
    render_demo_module("Compensation analytics", "Review salary distribution, benchmarking, and pay equity signals without implying causation.", filtered, [("Average salary", f"Rs. {filtered['Salary'].mean():,.0f}"), ("Median salary", f"Rs. {filtered['Salary'].median():,.0f}"), ("Salary bands", str(filtered['Salary'].nunique()),), ("Pay equity review", "Ready")], [("Salary by department", filtered.groupby("Department")["Salary"].mean(), "#087f8c"), ("Compensation vs performance", filtered.groupby("Performance Rating")["Salary"].mean(), "#e76f51")], demo=False)
elif page == "Engagement & Retention":
    render_demo_module("Engagement & retention", "Track engagement, eNPS, concerns, and retention indicators.", filtered, [("Engagement score", f"{filtered['Engagement Score'].mean():.0f}/100"), ("eNPS", f"{(filtered['Engagement Score'].ge(70).mean() - filtered['Engagement Score'].le(50).mean()) * 100:.0f}"), ("Positive trend", f"{filtered['Engagement Score'].ge(70).mean():.0%}"), ("Retention signals", f"{int((filtered['Risk Level'] == 'High').sum())}")], [("Engagement by department", filtered.groupby("Department")["Engagement Score"].mean(), "#087f8c"), ("Engagement trend", filtered.groupby(filtered["Joining Date"].dt.year)["Engagement Score"].mean(), "#e76f51")], demo=False)
elif page == "Learning & Development":
    render_demo_module("Learning & development", "Track training participation, certification coverage, and skill gaps.", filtered, [("Training completion", "76%"), ("Participation", "84%"), ("Skill gaps", "12"), ("Certifications expiring", "7")], [("Training by department", filtered.groupby("Department")["Goal Completion %"].mean(), "#087f8c"), ("Learning progress", pd.Series([48, 55, 61, 68, 73, 76], index=["Jan", "Feb", "Mar", "Apr", "May", "Jun"]), "#e76f51")])
elif page == "Reports":
    render_reports(filtered)

st.caption(f"Role: {role} | Data source: {source_name} | Demo/sample analytics are clearly labeled and should be validated before production decisions.")
