from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
from pathlib import Path
from database import read_failures
from analysis import summarize_for_report, compute_regression_health, compute_module_hotspots

app = Flask(__name__)
CORS(app)

DATA_DIR = Path("data")

@app.route("/api/failures", methods=["GET"])
def get_failures():
    df = read_failures()
    if df.empty:
        return jsonify([])
    return jsonify(df.to_dict(orient="records"))

@app.route("/api/summary", methods=["GET"])
def get_summary():
    df = read_failures()
    if df.empty:
        return jsonify({
            "total_failures": 0,
            "unique_failures": 0,
            "regression_health_score": 100,
            "problematic_modules": []
        })
    summary = summarize_for_report(df)
    return jsonify(summary)

@app.route("/api/report/<filename>", methods=["GET"])
def get_report(filename):
    if filename not in ["debug_report.txt", "debug_report.md"]:
        return "File not found", 404
    return send_from_directory(DATA_DIR, filename)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
