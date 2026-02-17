from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from search import query_database
import math

app = Flask(__name__)
CORS(app)

RESULTS_PER_PAGE = 10

INDUSTRIES = [
    "business--conferences",
    "technology--conferences",
    "health--conferences",
    "finance--conferences"
]

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Conference Explorer</title>
    <style>
        body { font-family: Arial; margin: 40px; background-color: #f4f6f8; }
        h1 { color: #333; }
        form { margin-bottom: 20px; }
        input, select { padding: 8px; margin-right: 10px; }
        button { padding: 8px 14px; }
        .result {
            background: white;
            padding: 15px;
            margin-top: 15px;
            border-radius: 6px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .pagination { margin-top: 20px; }
        .pagination a {
            margin-right: 10px;
            text-decoration: none;
            font-weight: bold;
        }
        .count { margin-bottom: 15px; color: #666; }
    </style>
</head>
<body>

<h1>Conference Explorer</h1>

<form method="GET">
    <input type="text" name="keyword" placeholder="Keyword"
        value="{{ keyword or '' }}">

    <select name="industry">
        <option value="">All Industries</option>
        {% for ind in industries %}
            <option value="{{ ind }}"
                {% if ind == industry %}selected{% endif %}>
                {{ ind }}
            </option>
        {% endfor %}
    </select>

    <button type="submit">Search</button>
</form>

<div class="count">
    Showing {{ results|length }} of {{ total }} result(s)
</div>

{% for r in results %}
<div class="result">
    <strong>{{ r.title }}</strong><br>
    <b>Industry:</b> {{ r.industry }}<br>
    <b>Date:</b> {{ r.date }}<br>
    <b>Location:</b> {{ r.location }}<br>
    <a href="{{ r.link }}" target="_blank">View Event</a>
</div>
{% endfor %}

<div class="pagination">
    {% if page > 1 %}
        <a href="?keyword={{ keyword or '' }}&industry={{ industry or '' }}&page={{ page-1 }}">⬅ Previous</a>
    {% endif %}

    {% if page < total_pages %}
        <a href="?keyword={{ keyword or '' }}&industry={{ industry or '' }}&page={{ page+1 }}">Next ➡</a>
    {% endif %}
</div>

</body>
</html>
"""

# ----------------------------
# WEB UI ROUTE
# ----------------------------
@app.route("/", methods=["GET"])
def home():
    keyword = request.args.get("keyword")
    industry = request.args.get("industry")
    page = request.args.get("page", 1, type=int)

    keyword = keyword or None
    industry = industry or None

    results, total, total_pages = query_database(keyword, industry, page)

    return render_template_string(
        HTML_TEMPLATE,
        results=results,
        total=total,
        page=page,
        total_pages=total_pages,
        keyword=keyword,
        industry=industry,
        industries=INDUSTRIES
    )


# ----------------------------
# API ROUTE
# ----------------------------
@app.route("/api/conferences", methods=["GET"])
def api_conferences():
    keyword = request.args.get("keyword")
    industry = request.args.get("industry")
    page = request.args.get("page", 1, type=int)

    keyword = keyword or None
    industry = industry or None

    results, total, total_pages = query_database(keyword, industry, page)

    return jsonify({
        "success": True,
        "total": total,
        "page": page,
        "per_page": RESULTS_PER_PAGE,
        "total_pages": total_pages,
        "results": results
    })


# ----------------------------
# RUN APP
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
