import os
import requests
import sqlite3
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

API_KEY = os.getenv("PREDICTHQ_API_KEY")
DB_NAME = "conferences.db"

BASE_URL = "https://api.predicthq.com/v1/events/"


def map_category_to_industry(event):
    labels = event.get("phq_labels", [])

    for label in labels:
        name = label.get("label")

        if name == "science-and-technology":
            return "technology"
        if name == "education-and-careers":
            return "education"
        if name == "health":
            return "healthcare"

    return "business"


def fetch_events():
    if not API_KEY:
        print("ERROR: PREDICTHQ_API_KEY not found in .env file.")
        return []

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }

    params = {
        "category": "conferences",
        "limit": 50,
        "active.gte": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "sort": "start"
    }

    try:
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=10)
    except Exception as e:
        print("Request failed:", e)
        return []

    if response.status_code != 200:
        print("API Error:", response.status_code, response.text)
        return []

    data = response.json()
    return data.get("results", [])


def normalize_and_save(events):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    inserted = 0

    for event in events:
        try:
            external_id = event["id"]
            title = event.get("title")
            description = event.get("description")

            start_datetime = event.get("start")
            end_datetime = event.get("end")

            registration_url = event.get("url") or f"https://www.predicthq.com/events/{external_id}"

            industry = map_category_to_industry(event)

            # Improved location handling
            location_type = "in_person"
            location_name = None

            geo = event.get("geo")

            if geo and geo.get("address"):
                location_name = geo["address"].get("formatted_address")
            else:
                location = event.get("location")
                if location and isinstance(location, list) and len(location) == 2:
                    location_name = f"{location[0]}, {location[1]}"

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

        except Exception as e:
            print("Skipping event due to error:", e)

    conn.commit()
    conn.close()

    print(f"Inserted {inserted} new events.")


def main():
    print("Fetching conferences from PredictHQ...")
    events = fetch_events()
    print(f"Fetched {len(events)} events.")
    normalize_and_save(events)


if __name__ == "__main__":
    main()
