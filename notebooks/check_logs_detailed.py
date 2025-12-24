import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'app', 'backend'))

from database import SessionLocal
from models import TaskLog

def check_logs():
    db = SessionLocal()
    try:
        logs = db.query(TaskLog).order_by(TaskLog.id.desc()).limit(10).all()
        print(f"{'ID':<5} | {'Item':<5} | {'Action':<10} | {'By':<10} | {'Notes'}")
        print("-" * 50)
        for log in logs:
            print(f"{log.id:<5} | {log.care_item_id:<5} | {log.action:<10} | {str(log.completed_by):<10} | {log.notes}")
    finally:
        db.close()

if __name__ == "__main__":
    check_logs()
