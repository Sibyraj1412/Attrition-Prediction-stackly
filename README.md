# Stackly Workforce Analytics

A Streamlit workforce intelligence platform for HR teams, managers, and administrators. It loads the bundled Indian employee workbook, supports alternate `.xlsx` uploads, and combines workforce analytics with explainable attrition screening.

The app includes:

- One combined dashboard that brings workforce health and attrition priorities onto one screen.
- Overview with headcount, location, department, hiring, diversity, leave, and alert signals.
- Employee Analytics with search, pagination, workforce charts, and complete employee details.
- Attrition Prediction with risk watchlist, confidence, evaluation metrics, and screening-factor importance.
- Dedicated platform routes for performance, recruitment, attendance, compensation, engagement, learning, and reports.
- Role-aware navigation for HR, Manager, and Admin users; salary is hidden from Manager tables.

## Data note

The bundled workbook contains 106 Indian-format rows, of which 100 are employee records after summary rows are removed. It now includes development fields for gender, performance, potential, engagement, goals, manager changes, promotions, overtime, absence, satisfaction, role changes, and attrition. Uploaded workbooks may use the standard employee columns or supported Indian-format aliases. A `Resigned` status is normalized into the model's `Attrition` target, while `Active` and `On Leave` are treated as non-attrition examples.

Recruitment and Learning & Development remain demo modules because the workbook has no requisition, candidate, training, or certification entities. The other analytics modules use workbook-backed fields. Development fields are deterministic sample values and must be replaced with approved operational data before production use. Predictions are decision-support signals, not automatic employment decisions.

## Run

```powershell
cd "$HOME\Downloads\stackly_attrition_prediction"
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app uses the bundled workbook automatically and also accepts an `.xlsx` upload with the standard employee columns or supported aliases.

## Documentation

- [Full project guide](docs/ATTRITION_PROJECT_GUIDE.md)
