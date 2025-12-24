from sqlalchemy.orm import Session
from app.backend.database import SessionLocal
from app.backend.models import CareItem

def update_denamarin_note():
    db = SessionLocal()
    try:
        denamarin = db.query(CareItem).filter(CareItem.name == "Denamarin").first()
        if denamarin:
            new_note = "Give on empty stomach, at least 1 hour before food, and at least 2 hours after food"
            if denamarin.notes != new_note:
                denamarin.notes = new_note
                db.commit()
                print(f"Updated Denamarin note to: {new_note}")
            else:
                print("Denamarin note is already up to date.")
        else:
            print("Denamarin item not found in database.")
    finally:
        db.close()

if __name__ == "__main__":
    update_denamarin_note()

