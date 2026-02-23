from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import math

app = Flask(__name__)
CORS(app)

DB_NAME = "conferences.db"
DEFAULT_PER_PAGE = 10


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
    per_page = request.args.get("limit", DEFAULT_PER_PAGE, type=int)

    industry = request.args.get("industry")
    search = request.args.get("search")

    conn = get_db_connection()
    cursor = conn.cursor()

    base_query = "FROM conferences WHERE 1=1"
    params = []

    if industry:
        base_query += " AND industry = ?"
        params.append(industry)

    if search:
        base_query += " AND title LIKE ?"
        params.append(f"%{search}%")

    # Count total matching rows
    cursor.execute(f"SELECT COUNT(*) {base_query}", params)
    total = cursor.fetchone()[0]

    offset = (page - 1) * per_page

    cursor.execute(
        f"""
        SELECT *
        {base_query}
        ORDER BY start_datetime ASC
        LIMIT ? OFFSET ?
        """,
        params + [per_page, offset]
    )

    rows = cursor.fetchall()
    conn.close()

    results = [dict(row) for row in rows]

    total_pages = math.ceil(total / per_page) if total else 1

    return jsonify({
        "events": results,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages
        }
    })


if __name__ == "__main__":
    app.run(debug=True)
