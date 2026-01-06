import sqlite3
import os

def migrate():
    # Use absolute path for safety as requested in user rules
    workspace_root = "/Users/dan/Projects/Playground/Care-Tracker"
    db_path = os.path.join(workspace_root, "data", "pet_care.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Adding timer_alert_sent column to pets table...")
        # Boolean in SQLite is stored as integer (0 or 1). 
        # Defaulting to 0 (False) for existing records.
        cursor.execute("ALTER TABLE pets ADD COLUMN timer_alert_sent BOOLEAN DEFAULT 0")
        print("Column added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Note: Column 'timer_alert_sent' already exists.")
        else:
            print(f"Error: {e}")

    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == "__main__":
    migrate()

