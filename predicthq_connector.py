import os
import requests
import sqlite3
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

API_KEY = os.getenv("PREDICTHQ_API_KEY")
DB_NAME = "conferences.db"
BASE_URL = "https://api.predicthq.com/v1/events/"


def map_category_to_industry(event):
    labels = event.get("phq_labels", [])

    allowed = {
        "finance": "finance",
        "health": "healthcare",
        "education-and-careers": "education",
        "science-and-technology": "technology",
        "business-and-professional": "business"
    }

    for label in labels:
        name = label.get("label")
        if name in allowed:
            return allowed[name]

    return None


def fetch_events():
    if not API_KEY:
        print("Missing PREDICTHQ_API_KEY")
        return []

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }

    params = {
        "category": "conferences",
        "country": "US",
        "limit": 100,
        "active.gte": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "sort": "start",
        "phq_attendance.gte": 3000,
        "rank.gte": 60
}

    try:
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=10)
    except Exception as e:
        print("Request failed:", e)
        return []

    if response.status_code != 200:
        print("API Error:", response.status_code, response.text)
        return []

    return response.json().get("results", [])


def normalize_and_save(events):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    inserted = 0

    for event in events:
        external_id = event.get("id")
        title = event.get("title")
        description = event.get("description")
        start_datetime = event.get("start")
        end_datetime = event.get("end")

        # Industry filtering
        industry = map_category_to_industry(event)
        if industry is None:
            continue

        # Require US geo location (eliminates online-only events)
        geo = event.get("geo")
        if not geo or not geo.get("address"):
            continue

        location_name = geo["address"].get("formatted_address")
        location_type = "in_person"

        registration_url = f"https://www.predicthq.com/events/{external_id}"

        if not all([external_id, title, start_datetime, registration_url]):
            continue

        cursor.execute("""
            INSERT OR IGNORE INTO conferences (
                source,
                external_id,
                title,
                description,
                start_datetime,
                end_datetime,
                industry,
                location_type,
                location_name,
                registration_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "predicthq",
            external_id,
            title,
            description,
            start_datetime,
            end_datetime,
            industry,
            location_type,
            location_name,
            registration_url
        ))

        if cursor.rowcount > 0:
            inserted += 1

    conn.commit()
    conn.close()

    print(f"Inserted {inserted} curated events.")


def main():
    print("Fetching curated US large-scale conferences...")
    events = fetch_events()
    print(f"Fetched {len(events)} raw events.")
    normalize_and_save(events)


if __name__ == "__main__":
    main()
