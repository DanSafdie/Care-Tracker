import sys
import os

# Add the app/backend directory to the path so we can import models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'backend')))

from database import SessionLocal
from models import CareItem, Pet

def reorder_items():
    db = SessionLocal()
    try:
        # Get Chessie
        chessie = db.query(Pet).filter(Pet.name == "Chessie").first()
        if not chessie:
            print("Chessie not found in database.")
            return

        # New ordering mapping: Name -> New display_order
        new_order = {
            "Fish Oil": 1,
            "Breakfast": 2,
            "Ursodiol": 3,
            "Cosequin": 4,
            "Denamarin": 5,
            "Dinner": 6
        }

        print(f"Updating order for {chessie.name}'s items...")
        
        # Get all care items for Chessie
        items = db.query(CareItem).filter(CareItem.pet_id == chessie.id).all()
        
        updated_count = 0
        for item in items:
            if item.name in new_order:
                old_order = item.display_order
                item.display_order = new_order[item.name]
                print(f"  - {item.name}: {old_order} -> {item.display_order}")
                updated_count += 1
            else:
                print(f"  - Skipping {item.name} (not in reorder list)")
        
        db.commit()
        print(f"Successfully updated {updated_count} items.")

    except Exception as e:
        db.rollback()
        print(f"Error during reordering: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reorder_items()

