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


def map_category_to_industry(category):
    """
    Map PredictHQ categories to your internal industry labels.
    You can expand this mapping later.
    """
    mapping = {
        "conferences": "business",
        "expos": "business",
        "academic": "technology",
        "community": "other",
        "sports": "other",
        "performing-arts": "other"
    }
    return mapping.get(category, "other")


def fetch_events():
    """
    Fetch conference events from PredictHQ.
    """

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
    """
    Normalize PredictHQ event data to your database schema and insert.
    """

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

            category = event.get("category")
            industry = map_category_to_industry(category)

            # PredictHQ marks virtual events differently
            location = event.get("location")
            location_type = "online" if event.get("virtual", False) else "in_person"

            location_name = None
            if location and isinstance(location, list) and len(location) == 2:
                location_name = f"{location[0]}, {location[1]}"

            # Skip if required fields missing
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
    print(events[0])
    normalize_and_save(events)


if __name__ == "__main__":
    main()
