# Global Methane Tracker

Streamlit app to explore methane emissions by country, region, source, segment, and reason using the provided Excel dataset.

## Setup
- Python 3.9+ recommended.
- Install deps: `pip install -r requirements.txt`
- Ensure the following files are in the project folder:
  - `METHANE TRACKER.xlsx` (data)
  - `emission.md` (article content)
  - `glossary.md` (glossary content)
  - `logo.png` (optional footer logo)
  - `licensed-image.jpeg` (image used in `emission.md`)
  - `Picture1.jpg`, `Picture2.jpg` (images used in `glossary.md`)

## Run
```bash
streamlit run streamlit_app.py
```

## Features
- Sidebar filters: Region, Country, Source, Segment, Reason.
- Dashboard tab:
  - Choropleth map of emissions by country.
  - Sunburst: Sources (inner) and Segment-for-Energy/else Country (outer).
  - Top 10 Countries bar chart.
  - Regional stacked bar by Sources.
  - Filtered data table.
- Methane Emission tab: renders `emission.md` with inline image support.
- Emission Glossary tab: renders `glossary.md` and shows `Picture1.jpg` and `Picture2.jpg`.
- Fixed bottom-right logo if `logo.png` is present.
