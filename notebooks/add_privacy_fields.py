"""
Migration: Add created_by and is_public columns to pets and care_items tables.

These columns enable ownership and visibility controls so that non-public
pets/items are only visible to (and send alerts to) their creator.

Safe to re-run: silently skips columns that already exist.
"""
import sqlite3
import os

# Column definitions: (table, column_name, column_type_with_default)
COLUMNS_TO_ADD = [
    ("pets", "created_by", "INTEGER REFERENCES users(id)"),
    ("pets", "is_public", "BOOLEAN DEFAULT 1"),
    ("care_items", "created_by", "INTEGER REFERENCES users(id)"),
    ("care_items", "is_public", "BOOLEAN DEFAULT 1"),
]


def migrate():
    data_dir = os.environ.get(
        "DATA_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data")),
    )
    db_path = os.path.join(data_dir, "pet_care.db")

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for table, col, col_type in COLUMNS_TO_ADD:
        try:
            print(f"Adding {col} to {table}...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            print(f"  -> added.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"  -> already exists, skipping.")
            else:
                print(f"  -> Error: {e}")

    conn.commit()
    conn.close()
    print("Migration finished.")


if __name__ == "__main__":
    migrate()
