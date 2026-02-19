import requests
import sqlite3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import re

DB_NAME = "conferences.db"

BASE_URL = "https://www.eventbrite.com/d/online/business--conferences/?page={}"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def scrape_page(page):
    url = BASE_URL.format(page)
    print(f"Scraping page {page}...")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        print("Status code:", response.status_code)
    except Exception as e:
        print("Request failed:", e)
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    events = []

    cards = soup.find_all("div", {"data-testid": "event-card"})
    print("Found", len(cards), "cards")

    for card in cards:
        title_tag = card.find("h3")
        link_tag = card.find("a", href=True)
        time_tag = card.find("time")

        title = title_tag.get_text(strip=True) if title_tag else None
        link = urljoin("https://www.eventbrite.com", link_tag["href"]) if link_tag else None

        date = None
        if time_tag:
            potential_date = time_tag.get_text(strip=True)

            if re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", potential_date):
                date = potential_date

        if title and link:
            events.append((title, date, link))

    return events



def save_events(events):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for title, date, link in events:
        cursor.execute("""
            INSERT INTO conferences (industry, title, date, location, link)
            VALUES (?, ?, ?, ?, ?)
        """, ("business--conferences", title, date, "N/A", link))

    conn.commit()
    conn.close()


def main():
    print("Starting scraper...")

    all_events = []

    for page in range(1, 2):  # scrape only 1 page for testing
        events = scrape_page(page)
        print("Returned", len(events), "events")
        all_events.extend(events)
        time.sleep(1)

    save_events(all_events)
    print(f"Saved {len(all_events)} events.")


if __name__ == "__main__":
    main()
