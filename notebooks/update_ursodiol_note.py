import sys
import os

# Add the backend directory to the path so imports work correctly
backend_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'backend')
sys.path.insert(0, backend_path)

from sqlalchemy.orm import Session
from database import SessionLocal
from models import CareItem

def update_ursodiol_note():
    db = SessionLocal()
    try:
        ursodiol = db.query(CareItem).filter(CareItem.name == "Ursodiol").first()
        if ursodiol:
            new_note = "Give with food"
            if ursodiol.notes != new_note:
                ursodiol.notes = new_note
                db.commit()
                print(f"Updated Ursodiol note to: {new_note}")
            else:
                print("Ursodiol note is already up to date.")
        else:
            print("Ursodiol item not found in database.")
    finally:
        db.close()

if __name__ == "__main__":
    update_ursodiol_note()

