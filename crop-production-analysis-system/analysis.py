import pandas as pd
from database import get_connection

REQUIRED = ["crop_name", "region_name", "year", "cultivated_area", "production",
            "area_unit", "production_unit"]
OPTIONAL = ["rainfall_mm"]

def validate_dataframe(df):
    """Return (cleaned_dataframe, issues). Invalid files are not imported."""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        return df, [f"Missing required column(s): {', '.join(missing)}"]

    issues = []
    for col in ["crop_name", "region_name", "area_unit", "production_unit"]:
        df[col] = df[col].astype("string").str.strip()
        bad = df[col].isna() | (df[col] == "")
        if bad.any():
            issues.append(f"{col}: {int(bad.sum())} row(s) have blank values.")

    for col in ["year", "cultivated_area", "production"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        bad = df[col].isna()
        if bad.any():
            issues.append(f"{col}: {int(bad.sum())} row(s) are missing or not numeric.")

    if not df["year"].isna().any():
        non_integer = (df["year"] % 1 != 0)
        if non_integer.any():
            issues.append("year must contain whole-number years.")
        if ((df["year"] < 1900) | (df["year"] > 2100)).any():
            issues.append("year contains values outside the supported range 1900–2100.")

    if not df["cultivated_area"].isna().any() and (df["cultivated_area"] <= 0).any():
        issues.append("cultivated_area must be greater than zero. Zero/negative area is not imported.")
    if not df["production"].isna().any() and (df["production"] < 0).any():
        issues.append("production cannot be negative.")

    if "rainfall_mm" not in df.columns:
        df["rainfall_mm"] = None
    else:
        df["rainfall_mm"] = pd.to_numeric(df["rainfall_mm"], errors="coerce")
        if (df["rainfall_mm"].dropna() < 0).any():
            issues.append("rainfall_mm cannot be negative.")

    # Yield is only comparable when units are explicitly supplied and consistent.
    df["yield_value"] = df["production"] / df["cultivated_area"]
    return df, issues

def load_records(df):
    conn = get_connection()
    imported = 0
    try:
        cur = conn.cursor()
        for _, row in df.iterrows():
            cur.execute("INSERT IGNORE INTO crops (crop_name) VALUES (%s)", (str(row["crop_name"]),))
            cur.execute("SELECT crop_id FROM crops WHERE crop_name=%s", (str(row["crop_name"]),))
            crop_id = cur.fetchone()[0]
            cur.execute("INSERT IGNORE INTO regions (region_name) VALUES (%s)", (str(row["region_name"]),))
            cur.execute("SELECT region_id FROM regions WHERE region_name=%s", (str(row["region_name"]),))
            region_id = cur.fetchone()[0]
            rainfall = None if pd.isna(row["rainfall_mm"]) else float(row["rainfall_mm"])
            cur.execute("""
                INSERT INTO crop_records
                (crop_id, region_id, year, cultivated_area, production, rainfall_mm, area_unit, production_unit)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (crop_id, region_id, int(row["year"]), float(row["cultivated_area"]),
                  float(row["production"]), rainfall, str(row["area_unit"]),
                  str(row["production_unit"])))
            imported += 1
        conn.commit()
        return imported
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_summary():
    conn = get_connection()
    try:
        return {
            "records": pd.read_sql("SELECT COUNT(*) AS value FROM crop_records", conn).iloc[0]["value"],
            "crops": pd.read_sql("SELECT COUNT(*) AS value FROM crops", conn).iloc[0]["value"],
            "regions": pd.read_sql("SELECT COUNT(*) AS value FROM regions", conn).iloc[0]["value"],
            "years": pd.read_sql("SELECT COUNT(DISTINCT year) AS value FROM crop_records", conn).iloc[0]["value"],
            "by_crop": pd.read_sql("""
                SELECT c.crop_name, r.production_unit, SUM(r.production) AS total_production
                FROM crop_records r JOIN crops c ON c.crop_id=r.crop_id
                GROUP BY c.crop_name, r.production_unit ORDER BY c.crop_name
            """, conn).to_dict(orient="records"),
            "by_region": pd.read_sql("""
                SELECT g.region_name, r.production_unit, SUM(r.production) AS total_production
                FROM crop_records r JOIN regions g ON g.region_id=r.region_id
                GROUP BY g.region_name, r.production_unit ORDER BY g.region_name
            """, conn).to_dict(orient="records"),
            "quality": pd.read_sql("""
                SELECT
                  SUM(cultivated_area <= 0) AS invalid_area_rows,
                  SUM(production < 0) AS negative_production_rows,
                  SUM(rainfall_mm IS NULL) AS missing_rainfall_rows
                FROM crop_records
            """, conn).to_dict(orient="records")[0],
        }
    finally:
        conn.close()

def get_yearly_comparison():
    conn = get_connection()
    try:
        return pd.read_sql("""
            SELECT year, production_unit, SUM(production) AS total_production
            FROM crop_records
            GROUP BY year, production_unit
            ORDER BY year, production_unit
        """, conn).to_dict(orient="records")
    finally:
        conn.close()
