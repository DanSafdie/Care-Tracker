import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'app', 'backend'))

from database import SessionLocal
from models import TaskLog, CareItem
from sqlalchemy import desc

def check_logs():
    db = SessionLocal()
    try:
        logs = db.query(TaskLog).order_by(desc(TaskLog.id)).limit(10).all()
        print(f"{'ID':<5} | {'Item ID':<8} | {'Care Day':<12} | {'Action':<10} | {'Timestamp'}")
        print("-" * 60)
        for log in logs:
            print(f"{log.id:<5} | {log.care_item_id:<8} | {str(log.care_day):<12} | {log.action:<10} | {log.timestamp}")
    finally:
        db.close()

if __name__ == "__main__":
    check_logs()
