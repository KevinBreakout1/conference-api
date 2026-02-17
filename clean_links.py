import sqlite3

DB_NAME = "conferences.db"

def clean_links():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id, link FROM conferences")
    rows = cursor.fetchall()

    cleaned_count = 0

    for row in rows:
        record_id, link = row

        if link and link.count("https://") > 1:
            # Keep only the second https:// onward
            parts = link.split("https://")
            cleaned_link = "https://" + parts[-1]

            cursor.execute(
                "UPDATE conferences SET link = ? WHERE id = ?",
                (cleaned_link, record_id)
            )
            cleaned_count += 1

    conn.commit()
    conn.close()

    print(f"✅ Cleaned {cleaned_count} broken links.")

if __name__ == "__main__":
    clean_links()
