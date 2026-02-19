import os
import requests
import sqlite3
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

API_KEY = os.getenv("EVENTBRITE_API_KEY")
DB_NAME = "conferences.db"

BASE_URL = "https://www.eventbriteapi.com/v3/events/search/"


def map_category_to_industry(category_id):
    mapping = {
        "101": "business",
        "102": "technology",
        "107": "health",
        "113": "finance"
    }
    return mapping.get(category_id, "other")


def fetch_events():
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    params = {
        "q": "conference",
        "online_events": "true",
        "sort_by": "date",
        "expand": "category"
    }

    response = requests.get(BASE_URL, headers=headers, params=params)

    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        return []

    data = response.json()
    return data.get("events", [])


def normalize_and_save(events):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    inserted = 0

    for event in events:
        try:
            external_id = event["id"]
            title = event["name"]["text"]
            description = event["description"]["text"] if event["description"] else None
            start_datetime = event["start"]["local"]
            end_datetime = event["end"]["local"] if event["end"] else None
            registration_url = event["url"]
            location_type = "online" if event["online_event"] else "in_person"
            category_id = event["category_id"]

            industry = map_category_to_industry(category_id)

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
                "eventbrite",
                external_id,
                title,
                description,
                start_datetime,
                end_datetime,
                industry,
                location_type,
                None,
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
    print("Fetching events from Eventbrite...")
    events = fetch_events()
    print(f"Fetched {len(events)} events.")
    normalize_and_save(events)


if __name__ == "__main__":
    main()
