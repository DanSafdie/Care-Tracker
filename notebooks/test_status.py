import sys
import os
from datetime import date
sys.path.append(os.path.join(os.getcwd(), 'app', 'backend'))

from database import SessionLocal
import crud

def test():
    db = SessionLocal()
    try:
        care_day = date(2025, 12, 23)
        status = crud.get_task_status_for_day(db, 6, care_day)
        print(f"Status for item 6 on {care_day}: {status}")
        
        last_log = db.query(crud.TaskLog).filter(
            crud.TaskLog.care_item_id == 6,
            crud.TaskLog.care_day == care_day
        ).order_by(crud.desc(crud.TaskLog.timestamp), crud.desc(crud.TaskLog.id)).first()
        
        if last_log:
            print(f"Last log: ID={last_log.id}, Action={last_log.action}, TS={last_log.timestamp}")
        else:
            print("No log found")
    finally:
        db.close()

if __name__ == "__main__":
    test()
