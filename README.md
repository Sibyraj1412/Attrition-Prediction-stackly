# Stackly Attrition Prediction

A small Streamlit dashboard that reads the Stackly employee Excel workbook and estimates attrition probability with Logistic Regression.

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
