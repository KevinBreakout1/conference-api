import sqlite3
import math

DB_NAME = "conferences.db"
RESULTS_PER_PAGE = 10

def query_database(keyword=None, industry=None, page=1):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    base_query = "FROM conferences WHERE 1=1"
    params = []

    if keyword:
        base_query += """
        AND (
            title LIKE ? COLLATE NOCASE
            OR industry LIKE ? COLLATE NOCASE
        )
        """
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    if industry:
        base_query += " AND industry = ?"
        params.append(industry)

    # Total count
    cursor.execute(f"SELECT COUNT(*) {base_query}", params)
    total = cursor.fetchone()[0]

    total_pages = math.ceil(total / RESULTS_PER_PAGE) if total else 1
    offset = (page - 1) * RESULTS_PER_PAGE

    cursor.execute(
        f"""
        SELECT industry, title, date, location, link
        {base_query}
        ORDER BY title ASC
        LIMIT ? OFFSET ?
        """,
        params + [RESULTS_PER_PAGE, offset]
    )

    results = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return results, total, total_pages
