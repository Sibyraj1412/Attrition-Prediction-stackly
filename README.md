# Stackly Workforce Analytics

A Streamlit workforce analytics workspace that loads the bundled Indian employee workbook and provides workforce overview metrics alongside an explainable attrition-risk radar.

The app includes:

- One combined dashboard that brings workforce health and attrition priorities onto one screen.
- Workforce overview with headcount, active employees, tenure, department, location, and employment-status analysis.
- Employee roster filtered by department, location, and risk level.
- Attrition risk screening with Logistic Regression, risk signals, charts, and individual employee inspection.

## Data note

The bundled workbook contains 106 Indian-format employee records. Uploaded workbooks may use the standard employee columns or supported Indian-format aliases. A `Resigned` status is normalized into the model's `Attrition` target, while `Active` and `On Leave` are treated as non-attrition examples. Use validated historical outcomes before treating model probabilities as production predictions.

## Run

```powershell
cd "$HOME\Downloads\stackly_attrition_prediction"
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app uses the bundled workbook automatically and also accepts an `.xlsx` upload with the standard employee columns or supported aliases.

## Documentation

- [Full project guide](docs/ATTRITION_PROJECT_GUIDE.md)
