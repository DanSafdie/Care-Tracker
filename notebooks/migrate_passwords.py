"""
Migration script: Add password_hash column to existing users table and
assign secure random passwords to every pre-existing account.

Prints a table of (username -> temporary password) so the admin can
distribute credentials to each user.

Run once against the production database:
    python notebooks/migrate_passwords.py

After running, each user should log in with their temporary password and
change it via Account Settings > Change Password.
"""
import sqlite3
import os
import sys
import secrets

# Add backend to path so we can reuse the auth module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "backend"))
from auth import hash_password

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pet_care.db")


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("(If this is a fresh install, the column will be created automatically on startup.)")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- Step 1: Add password_hash column if missing ---
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]

    if "password_hash" not in columns:
        print("Adding password_hash column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")
        conn.commit()
        print("Column added.")
    else:
        print("password_hash column already exists.")

    # --- Step 2: Generate random passwords for users that have no hash ---
    cursor.execute("SELECT id, name FROM users WHERE password_hash IS NULL OR password_hash = ''")
    users_without_password = cursor.fetchall()

    if not users_without_password:
        print("All users already have a password hash. Nothing to do.")
        conn.close()
        return

    print(f"\nGenerating temporary passwords for {len(users_without_password)} user(s)...\n")
    print("=" * 60)
    print(f"{'User ID':<10} {'Name':<25} {'Temporary Password'}")
    print("=" * 60)

    for user_id, name in users_without_password:
        temp_password = secrets.token_urlsafe(12)  # ~16 chars, URL-safe
        hashed = hash_password(temp_password)
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hashed, user_id),
        )
        print(f"{user_id:<10} {name:<25} {temp_password}")

    conn.commit()
    conn.close()

    print("=" * 60)
    print(f"\nDone! {len(users_without_password)} user(s) updated.")
    print("Share each user's temporary password privately and ask them")
    print("to change it via Account Settings > Change Password.\n")


if __name__ == "__main__":
    migrate()
