# Stackly Workforce Analytics

A Streamlit workforce analytics workspace that reads the Stackly employee Excel workbook and provides workforce overview metrics alongside an explainable attrition-risk radar.

The app includes:

- One combined dashboard that brings workforce health and attrition priorities onto one screen.
- Workforce overview with headcount, active employees, tenure, department, location, and employment-status analysis.
- Employee roster filtered by department, location, and risk level.
- Attrition risk screening with Logistic Regression, risk signals, charts, and individual employee inspection.

## Important note

The source workbook does not contain a historical `Attrition` outcome column. The app uses clearly labeled demo targets generated from the original screening rules so the Logistic Regression workflow can run. Upload historical `Attrition` values of `Yes` or `No` for a real training target.

## Run

```powershell
cd "$HOME\Downloads\stackly_attrition_prediction"
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app accepts the included workbook or another `.xlsx` file with the same basic employee columns.

## Documentation

- [Full project guide](docs/ATTRITION_PROJECT_GUIDE.md)
- [Team-lead presentation outline](docs/TEAM_LEAD_PRESENTATION_OUTLINE.md)
