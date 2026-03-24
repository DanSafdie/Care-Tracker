"""
Migration: Add owner_id column to the pets table.

owner_id is a nullable FK to users.id.
- NULL means the pet/subject is shared (visible to all users).
- A user ID means it's private to that user only.

Run once against an existing pet_care.db to add the column.
Safe to re-run (catches 'duplicate column' error).
"""
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
        print("Adding owner_id column to pets table...")
        cursor.execute("ALTER TABLE pets ADD COLUMN owner_id INTEGER REFERENCES users(id)")
        print("Column added successfully.")
    except sqlite3.OperationalError as e:
        print(f"Note: {e}")

    conn.commit()
    conn.close()
    print("Migration completed.")


if __name__ == "__main__":
    migrate()
