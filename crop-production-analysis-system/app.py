import os
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from database import get_connection, init_db
from analysis import validate_dataframe, load_records, get_summary, get_yearly_comparison

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-development-key")

REQUIRED_COLUMNS = ["crop_name", "region_name", "year", "cultivated_area", "production",
                    "area_unit", "production_unit"]
OPTIONAL_COLUMNS = ["rainfall_mm"]

@app.route("/")
def index():
    try:
        summary = get_summary()
        yearly = get_yearly_comparison()
        return render_template("index.html", summary=summary, yearly=yearly)
    except Exception as exc:
        return render_template("index.html", summary=None, yearly=None,
                               setup_error=str(exc))

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("dataset")
        if not file or not file.filename:
            flash("Choose a CSV file first.", "error")
            return redirect(url_for("upload"))
        if not file.filename.lower().endswith(".csv"):
            flash("Only CSV files are supported.", "error")
            return redirect(url_for("upload"))
        try:
            df = pd.read_csv(file)
            cleaned, issues = validate_dataframe(df)
            if issues:
                return render_template("upload.html", issues=issues,
                                       preview=cleaned.head(10).to_html(
                                           classes="table", index=False, border=0))
            count = load_records(cleaned)
            flash(f"Successfully imported {count} records.", "success")
            return redirect(url_for("index"))
        except Exception as exc:
            flash(f"Could not import file: {exc}", "error")
    return render_template("upload.html", issues=None, preview=None)

@app.route("/yield-chart.png")
def yield_chart():
    try:
        conn = get_connection()
        try:
            df = pd.read_sql(
                """SELECT c.crop_name, r.year, r.area_unit, r.production_unit,
                          SUM(r.production) / NULLIF(SUM(r.cultivated_area), 0) AS yield_value
                   FROM crop_records r JOIN crops c ON c.crop_id=r.crop_id
                   GROUP BY c.crop_name, r.year, r.area_unit, r.production_unit
                   ORDER BY c.crop_name, r.year""", conn)
        finally:
            conn.close()
        fig, ax = plt.subplots(figsize=(8, 4.5))
        if df.empty:
            ax.text(0.5, 0.5, "No data yet. Upload a CSV file.", ha="center", va="center")
            ax.set_axis_off()
        else:
            for crop, group in df.groupby("crop_name"):
                # Each series is grouped by crop; unit columns are retained in SQL to avoid mixing units.
                for (area_unit, production_unit), unit_group in group.groupby(["area_unit", "production_unit"]):
                    label = f"{crop} ({production_unit}/{area_unit})"
                    ax.plot(unit_group["year"], unit_group["yield_value"], marker="o", label=label)
            ax.set_title("Recorded yield by crop and year")
            ax.set_xlabel("Year")
            ax.set_ylabel("Production unit per area unit")
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize="small")
        fig.tight_layout()
        image = BytesIO()
        fig.savefig(image, format="png", dpi=140)
        plt.close(fig)
        image.seek(0)
        return send_file(image, mimetype="image/png")
    except Exception as exc:
        return f"Could not generate yield chart: {exc}", 500

@app.route("/reports")
def reports():
    try:
        summary = get_summary()
        yearly = get_yearly_comparison()
        return render_template("reports.html", summary=summary, yearly=yearly)
    except Exception as exc:
        flash(f"Unable to build report: {exc}", "error")
        return redirect(url_for("index"))

@app.route("/chart.png")
def chart():
    try:
        conn = get_connection()
        try:
            df = pd.read_sql(
                """SELECT year, SUM(production) AS production
                   FROM crop_records GROUP BY year ORDER BY year""", conn)
        finally:
            conn.close()
        fig, ax = plt.subplots(figsize=(8, 4.5))
        if df.empty:
            ax.text(0.5, 0.5, "No data yet. Upload a CSV file.", ha="center", va="center")
            ax.set_axis_off()
        else:
            ax.plot(df["year"], df["production"], marker="o")
            ax.set_title("Total recorded production by year")
            ax.set_xlabel("Year")
            ax.set_ylabel("Production (grouped values; check units)")
            ax.grid(True, alpha=0.3)
        fig.tight_layout()
        image = BytesIO()
        fig.savefig(image, format="png", dpi=140)
        plt.close(fig)
        image.seek(0)
        return send_file(image, mimetype="image/png")
    except Exception as exc:
        return f"Could not generate chart: {exc}", 500

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
