import sys
import os

# Add the app/backend directory to the path so we can import models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'backend')))

from database import SessionLocal
from models import CareItem, Pet

def add_dental_chew():
    db = SessionLocal()
    try:
        # Get Chessie
        chessie = db.query(Pet).filter(Pet.name == "Chessie").first()
        if not chessie:
            print("Chessie not found in database.")
            return

        # Check if Dental Chew already exists
        existing = db.query(CareItem).filter(
            CareItem.pet_id == chessie.id,
            CareItem.name == "Dental Chew"
        ).first()

        if existing:
            print(f"Dental Chew already exists for {chessie.name} (ID: {existing.id}).")
            return

        print(f"Adding Dental Chew to {chessie.name}'s regimen...")
        
        dental_chew = CareItem(
            pet_id=chessie.id,
            name="Dental Chew",
            description="Daily dental health treat",
            notes="Give after dinner",
            category="supplement",
            display_order=7
        )
        
        db.add(dental_chew)
        db.commit()
        db.refresh(dental_chew)
        print(f"Successfully added Dental Chew (ID: {dental_chew.id}) at display_order {dental_chew.display_order}.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_dental_chew()

