import sys
import os
from datetime import date, datetime, timedelta
sys.path.append(os.path.join(os.getcwd(), 'app', 'backend'))

from database import SessionLocal, init_db
from models import TaskLog
import crud

def test_collision():
    db = SessionLocal()
    care_item_id = 999  # Mock ID
    care_day = date(2025, 12, 24)
    ts = datetime(2025, 12, 24, 10, 0, 0)
    
    try:
        # Clean up
        db.query(TaskLog).filter(TaskLog.care_item_id == care_item_id).delete()
        
        # Insert "completed"
        log1 = TaskLog(care_item_id=care_item_id, care_day=care_day, action="completed", timestamp=ts)
        db.add(log1)
        db.commit()
        
        # Insert "undone" with same timestamp but higher ID
        log2 = TaskLog(care_item_id=care_item_id, care_day=care_day, action="undone", timestamp=ts)
        db.add(log2)
        db.commit()
        
        print(f"Log 1: ID={log1.id}, Action={log1.action}, TS={log1.timestamp}")
        print(f"Log 2: ID={log2.id}, Action={log2.action}, TS={log2.timestamp}")
        
        is_completed = crud.get_task_status_for_day(db, care_item_id, care_day)
        print(f"Status (should be False): {is_completed}")
        
    finally:
        db.query(TaskLog).filter(TaskLog.care_item_id == care_item_id).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_collision()
