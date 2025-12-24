import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "pet_care.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Adding timer_end_time column to pets table...")
        cursor.execute("ALTER TABLE pets ADD COLUMN timer_end_time DATETIME")
    except sqlite3.OperationalError as e:
        print(f"Note: {e}")

    try:
        print("Adding timer_label column to pets table...")
        cursor.execute("ALTER TABLE pets ADD COLUMN timer_label VARCHAR(100)")
    except sqlite3.OperationalError as e:
        print(f"Note: {e}")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()


