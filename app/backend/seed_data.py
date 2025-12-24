"""
Seed data for initial setup.
Creates Chessie and her care items.

Run this once to populate the database with initial data.
Can be extended to add more pets/items.
"""
from sqlalchemy.orm import Session
from models import Pet, CareItem
from database import SessionLocal, init_db


def seed_chessie_data(db: Session):
    """
    Seed the database with Chessie's care items.
    
    Care regimen:
    - Denamarin: Liver supplement (typically given on empty stomach, 1 hour before food)
    - Ursodiol: Liver medication
    - Fish oil: Supplement for coat/joints
    - Breakfast: Morning meal
    - Dinner: Evening meal
    - Cosequin: Joint supplement (typically given with food)
    
    Notes fields contain timing/dependency info for reference,
    but no rule enforcement in this version.
    """
    # Check if Chessie already exists
    existing = db.query(Pet).filter(Pet.name == "Chessie").first()
    if existing:
        print("Chessie already exists in database. Skipping seed.")
        return existing
    
    # Create Chessie
    chessie = Pet(
        name="Chessie",
        species="dog",
        notes="Our beloved pup. Requires daily medications and supplements."
    )
    db.add(chessie)
    db.flush()  # Get the ID without committing
    
    # Define care items with informational notes about timing
    care_items = [
        CareItem(
            pet_id=chessie.id,
            name="Denamarin",
            description="Liver supplement",
            notes="Give on empty stomach, at least 1 hour before food, and at least 2 hours after food",
            category="medication",
            display_order=1
        ),
        CareItem(
            pet_id=chessie.id,
            name="Ursodiol",
            description="Liver medication (ursodeoxycholic acid)",
            notes="Give with food",
            category="medication",
            display_order=2
        ),
        CareItem(
            pet_id=chessie.id,
            name="Fish Oil",
            description="Omega fatty acid supplement for coat and joints",
            notes="Give with food",
            category="supplement",
            display_order=3
        ),
        CareItem(
            pet_id=chessie.id,
            name="Breakfast",
            description="Morning meal",
            notes="",
            category="food",
            display_order=4
        ),
        CareItem(
            pet_id=chessie.id,
            name="Dinner",
            description="Evening meal",
            notes="",
            category="food",
            display_order=5
        ),
        CareItem(
            pet_id=chessie.id,
            name="Cosequin",
            description="Joint supplement (glucosamine/chondroitin)",
            notes="Give with food",
            category="supplement",
            display_order=6
        ),
    ]
    
    for item in care_items:
        db.add(item)
    
    db.commit()
    print(f"Created Chessie (ID: {chessie.id}) with {len(care_items)} care items.")
    return chessie


def run_seed():
    """Run the seeding process."""
    init_db()
    db = SessionLocal()
    try:
        seed_chessie_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
