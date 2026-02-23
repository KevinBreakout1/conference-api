from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import math

app = Flask(__name__)
CORS(app)

DB_NAME = "conferences.db"
RESULTS_PER_PAGE = 10


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Conference API is running.",
        "endpoints": {
            "GET /events": "List events with pagination and filters"
        }
    })


@app.route("/events", methods=["GET"])
def get_events():
    page = request.args.get("page", 1, type=int)
    industry = request.args.get("industry")
    keyword = request.args.get("keyword")

    conn = get_db_connection()
    cursor = conn.cursor()

    base_query = "FROM conferences WHERE 1=1"
    params = []

    if industry:
        base_query += " AND industry = ?"
        params.append(industry)

    if keyword:
        base_query += " AND title LIKE ?"
        params.append(f"%{keyword}%")

    # Count total records
    cursor.execute(f"SELECT COUNT(*) {base_query}", params)
    total = cursor.fetchone()[0]

    offset = (page - 1) * RESULTS_PER_PAGE

    # Fetch paginated results
    cursor.execute(
        f"""
        SELECT *
        {base_query}
        ORDER BY start_datetime ASC
        LIMIT ? OFFSET ?
        """,
        params + [RESULTS_PER_PAGE, offset]
    )

    rows = cursor.fetchall()
    conn.close()

    results = [dict(row) for row in rows]

    total_pages = math.ceil(total / RESULTS_PER_PAGE) if total else 1

    return jsonify({
        "events": results,
        "pagination": {
            "page": page,
            "per_page": RESULTS_PER_PAGE,
            "total": total,
            "total_pages": total_pages
        }
    })


if __name__ == "__main__":
    app.run(debug=True)
