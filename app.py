from flask import Flask, jsonify, request
import sqlite3
import math

app = Flask(__name__)

DB_NAME = "conferences.db"
RESULTS_PER_PAGE = 10


@app.route("/", methods=["GET"])
def home():
    return "Conference API is running."


@app.route("/api/conferences", methods=["GET"])
def get_conferences():
    page = request.args.get("page", 1, type=int)
    industry = request.args.get("industry")
    keyword = request.args.get("keyword")

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    base_query = "FROM conferences WHERE 1=1"
    params = []

    if industry:
        base_query += " AND industry = ?"
        params.append(industry)

    if keyword:
        base_query += " AND title LIKE ?"
        params.append(f"%{keyword}%")

    cursor.execute(f"SELECT COUNT(*) {base_query}", params)
    total = cursor.fetchone()[0]

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
