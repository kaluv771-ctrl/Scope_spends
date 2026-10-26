"""
Naira Expense Tracker - web API + frontend.

Uses the same expenses.csv format as the command-line expenses.py:
    date,time,description,amount

Run locally:
    pip install -r requirements.txt
    python app.py              -> http://localhost:5000

Environment variables:
    EXPENSES_FILE   path to the CSV file (default: expenses.csv)
    APP_TIMEZONE    timezone used for timestamps (default: Africa/Lagos)
    PORT            port to listen on (set automatically by Railway/Render)
"""

import csv
import io
import os
from datetime import datetime
from threading import Lock
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, request, Response

FILE_NAME = os.environ.get("EXPENSES_FILE", "expenses.csv")
TZ = ZoneInfo(os.environ.get("APP_TIMEZONE", "Africa/Lagos"))
FIELDS = ["date", "time", "description", "amount"]
DATE_FMT = "%Y-%m-%d"
TIME_FMT = "%H:%M:%S"

app = Flask(__name__, static_folder="static", static_url_path="")
file_lock = Lock()


# ---------- CSV helpers ----------
def read_rows():
    """Return all valid rows with an id (their position in the file)."""
    rows = []
    try:
        with open(FILE_NAME, "r", newline="", encoding="utf-8") as f:
            for index, row in enumerate(csv.DictReader(f)):
                try:
                    datetime.strptime(f"{row['date']} {row['time']}", f"{DATE_FMT} {TIME_FMT}")
                    amount = float(row["amount"])
                except (ValueError, KeyError, TypeError):
                    continue
                rows.append({
                    "id": index,
                    "date": row["date"],
                    "time": row["time"],
                    "description": row["description"],
                    "amount": round(amount, 2),
                })
    except FileNotFoundError:
        pass
    return rows


def write_all(rows):
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow({**{k: r[k] for k in FIELDS}, "amount": f"{float(r['amount']):.2f}"})


def append_row(row):
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            needs_header = f.read(1) == ""
    except FileNotFoundError:
        needs_header = True
    with open(FILE_NAME, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if needs_header:
            writer.writeheader()
        writer.writerow(row)


# ---------- Routes ----------
PAGE_HEAD = (
    '<!doctype html><html lang="en"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
    "</head><body>"
)


@app.get("/")
def index():
    with open(os.path.join(app.static_folder, "index.html"), encoding="utf-8") as f:
        return PAGE_HEAD + f.read() + "</body></html>"


@app.get("/api/expenses")
def list_expenses():
    with file_lock:
        return jsonify(read_rows())


@app.post("/api/expenses")
def add_expense():
    data = request.get_json(silent=True) or {}
    description = str(data.get("description", "")).strip()
    if not description:
        return jsonify(error="Description is required."), 400
    try:
        amount = float(data.get("amount"))
        if amount < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify(error="Enter a valid non-negative amount."), 400

    now = datetime.now(TZ)
    row = {
        "date": now.strftime(DATE_FMT),
        "time": now.strftime(TIME_FMT),
        "description": description[:200],
        "amount": f"{amount:.2f}",
    }
    with file_lock:
        append_row(row)
        saved = read_rows()[-1]
    return jsonify(saved), 201


@app.delete("/api/expenses/<int:expense_id>")
def delete_expense(expense_id):
    with file_lock:
        rows = read_rows()
        remaining = [r for r in rows if r["id"] != expense_id]
        if len(remaining) == len(rows):
            return jsonify(error="Expense not found."), 404
        write_all(remaining)
    return jsonify(ok=True)


@app.get("/api/export")
def export_csv():
    with file_lock:
        rows = read_rows()
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=FIELDS)
    writer.writeheader()
    for r in rows:
        writer.writerow({**{k: r[k] for k in FIELDS}, "amount": f"{r['amount']:.2f}"})
    stamp = datetime.now(TZ).strftime("%Y-%m-%d")
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="expenses-{stamp}.csv"'},
    )


@app.get("/api/health")
def health():
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
