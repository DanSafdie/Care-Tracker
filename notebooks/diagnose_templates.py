import sys
import os
from datetime import datetime, date
import pytz

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'app', 'backend'))

from main import app, templates, to_local_time
from database import SessionLocal
import crud

def diagnose():
    db = SessionLocal()
    try:
        care_day = date(2025, 12, 24)
        daily_status = crud.get_daily_summary(db, care_day)
        
        print("Testing index.html rendering...")
        try:
            html = templates.get_template("index.html").render({
                "request": {"url": {"path": "/"}},
                "care_day": care_day,
                "daily_status": daily_status,
                "now": to_local_time(datetime.utcnow())
            })
            print("index.html rendered successfully")
        except Exception as e:
            print(f"Error rendering index.html: {e}")
            import traceback
            traceback.print_exc()

        print("\nTesting history.html rendering...")
        try:
            history = crud.get_history(db, limit=10)
            history_entries = []
            for log in history:
                care_item = crud.get_care_item(db, log.care_item_id)
                pet = crud.get_pet(db, care_item.pet_id) if care_item else None
                history_entries.append({
                    "log": log,
                    "pet_name": pet.name if pet else "Unknown",
                    "care_item_name": care_item.name if care_item else "Unknown"
                })
            
            html = templates.get_template("history.html").render({
                "request": {"url": {"path": "/history"}},
                "care_day": care_day,
                "history_entries": history_entries,
                "now": to_local_time(datetime.utcnow())
            })
            print("history.html rendered successfully")
        except Exception as e:
            print(f"Error rendering history.html: {e}")
            import traceback
            traceback.print_exc()
            
    finally:
        db.close()

if __name__ == "__main__":
    diagnose()
