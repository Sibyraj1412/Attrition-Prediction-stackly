# Stackly Attrition Prediction

A small Streamlit demo that reads the Stackly employee Excel workbook and estimates attrition risk from the fields available in the sample data.

## Important note

The source workbook does not contain a historical `Attrition` outcome column. This app therefore uses an explainable screening score, not a trained predictive model. Use the result for demonstration only until historical attrition labels and stronger HR features are available.

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
