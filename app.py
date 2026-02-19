from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import math

app = Flask(__name__)
CORS(app)

DB_NAME = "conferences.db"
RESULTS_PER_PAGE = 10


def query_database(
    industry=None,
    location_type=None,
    start_date=None,
    end_date=None,
    page=1
):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    base_query = "FROM conferences WHERE 1=1"
    params = []

    if industry:
        base_query += " AND industry = ?"
        params.append(industry)

    if location_type:
        base_query += " AND location_type = ?"
        params.append(location_type)

    if start_date:
        base_query += " AND start_datetime >= ?"
        params.append(start_date)

    if end_date:
        base_query += " AND start_datetime <= ?"
        params.append(end_date)

    # Total count
    cursor.execute(f"SELECT COUNT(*) {base_query}", params)
    total = cursor.fetchone()[0]

    total_pages = math.ceil(total / RESULTS_PER_PAGE) if total else 1
    offset = (page - 1) * RESULTS_PER_PAGE

    cursor.execute(
        f"""
        SELECT *
        {base_query}
        ORDER BY start_datetime ASC
        LIMIT ? OFFSET ?
        """,
        params + [RESULTS_PER_PAGE, offset]
    )

    results = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return results, total, total_pages


# -----------------------------------
# ROOT
# -----------------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Conference Intelligence API is running.",
        "endpoints": {
            "GET /conferences": "Query conferences with filters"
        }
    })


# -----------------------------------
# MAIN CONFERENCES ENDPOINT
# -----------------------------------
@app.route("/conferences", methods=["GET"])
def get_conferences():

    industry = request.args.get("industry")
    location_type = request.args.get("location_type")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page = request.args.get("page", 1, type=int)

    results, total, total_pages = query_database(
        industry=industry,
        location_type=location_type,
        start_date=start_date,
        end_date=end_date,
        page=page
    )

    return jsonify({
        "success": True,
        "total": total,
        "page": page,
        "per_page": RESULTS_PER_PAGE,
        "total_pages": total_pages,
        "results": results
    })


if __name__ == "__main__":
    app.run(debug=True)
