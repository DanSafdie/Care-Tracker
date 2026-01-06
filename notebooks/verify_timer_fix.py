import sys
import os
from datetime import datetime, timedelta

# Add app/backend to path
workspace_root = "/Users/dan/Projects/Playground/Care-Tracker"
sys.path.append(os.path.join(workspace_root, "app", "backend"))

from database import SessionLocal
from models import Pet
from main import check_timers_job

def verify():
    db = SessionLocal()
    try:
        # 1. Setup a pet with an expired timer
        pet = db.query(Pet).first()
        if not pet:
            print("No pets found in database.")
            return

        print(f"Setting expired timer for {pet.name}...")
        pet.timer_end_time = datetime.now() - timedelta(minutes=5)
        pet.timer_label = "Test Expired Timer"
        pet.timer_alert_sent = False
        db.commit()

        # 2. Run the background job
        print("Running check_timers_job...")
        check_timers_job()

        # 3. Verify results
        db.refresh(pet)
        print("\nResults:")
        print(f"Pet: {pet.name}")
        print(f"timer_end_time: {pet.timer_end_time}")
        print(f"timer_label: {pet.timer_label}")
        print(f"timer_alert_sent: {pet.timer_alert_sent}")

        if pet.timer_end_time is not None and pet.timer_alert_sent == True:
            print("\nSUCCESS: Timer was NOT cleared, and alert flag WAS set.")
        else:
            print("\nFAILURE: Behavior not as expected.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify()

