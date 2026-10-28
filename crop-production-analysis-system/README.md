# Agricultural Crop Production Analysis System

A beginner-friendly Flask + MySQL project for analyzing historical crop production records.

## Features
- CSV upload and validation
- MySQL storage for crops, regions and crop records
- Crop-wise and region-wise production summaries
- Year-wise production comparison and chart
- Basic data-quality summary
- Optional rainfall data
- Yield formula: `production / cultivated_area`

## 1. Requirements
- Python 3.10 or newer
- MySQL Server running locally
- VS Code (recommended)

## 2. Create and activate a virtual environment

Windows PowerShell:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:
```bat
.venv\Scripts\activate.bat
```

## 3. Install dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure MySQL
Start MySQL Server. In MySQL Workbench or the MySQL command line, run:
```sql
CREATE DATABASE crop_analysis;
```

Copy `.env.example` to `.env` and update `DB_USER` and `DB_PASSWORD` with your local MySQL credentials. Do not upload `.env` to GitHub.

## 5. Run the app
```bash
python app.py
```
Open http://127.0.0.1:5000 in your browser.

## 6. Upload sample data
Open **Upload CSV** and select `static/sample_data/crop_production_sample.csv`.
The sample file is also included under `sample_data/` for easy access.

CSV required columns:
`crop_name, region_name, year, cultivated_area, production, area_unit, production_unit`

Optional column: `rainfall_mm`

## Data and interpretation notes
- Area must be greater than zero; otherwise yield cannot be calculated safely.
- Production must be zero or positive.
- Rainfall can be blank.
- Yield is expressed as production unit per area unit, for example `tonne/hectare`.
- Do not compare records whose units differ. The starter dashboard labels units but does not automatically convert them.
- Totals grouped by production unit must be interpreted separately when units differ.
- Historical association does not establish causation and is not agronomic advice.
- The starter app blocks a whole upload if validation issues are found. Review the reported issues and upload a corrected CSV.

## Project structure
```text
crop-production-analysis-system/
├── app.py
├── analysis.py
├── database.py
├── requirements.txt
├── .env.example
├── .gitignore
├── schema.sql
├── README.md
├── sample_data/
│   └── crop_production_sample.csv
├── static/
│   ├── css/style.css
│   └── sample_data/crop_production_sample.csv
└── templates/
    ├── base.html
    ├── index.html
    ├── upload.html
    └── reports.html
```

## 7. Push to GitHub
First create an empty repository on GitHub, for example `crop-production-analysis-system`. Do not initialize it with a README if you already have this local README.

In VS Code terminal, from the project folder:
```bash
git init
git add .
git status
git commit -m "Initial crop production analysis system"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/crop-production-analysis-system.git
git push -u origin main
```
Replace `YOUR-USERNAME` with your GitHub username. Sign in when Git asks.

For future changes:
```bash
git add .
git commit -m "Describe your changes"
git push
```

Before pushing, check that `.env` is not listed by `git status`. Never commit database passwords or secrets.
