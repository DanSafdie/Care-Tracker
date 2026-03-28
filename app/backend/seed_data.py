"""
Seed data for initial setup.
Creates Chessie (shared household pet) and Dan's personal care items.

Run this once to populate the database with initial data.
Can be extended to add more pets/items.
"""
from sqlalchemy.orm import Session
from models import Pet, CareItem, User
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
            name="Fish Oil",
            description="Omega fatty acid supplement for coat and joints",
            notes="Give with food",
            category="supplement",
            display_order=1
        ),
        CareItem(
            pet_id=chessie.id,
            name="Breakfast",
            description="Morning meal",
            notes="",
            category="food",
            display_order=2
        ),
        CareItem(
            pet_id=chessie.id,
            name="Ursodiol",
            description="Liver medication (ursodeoxycholic acid)",
            notes="Give with food",
            category="medication",
            display_order=3
        ),
        CareItem(
            pet_id=chessie.id,
            name="Cosequin",
            description="Joint supplement (glucosamine/chondroitin)",
            notes="Give with food",
            category="supplement",
            display_order=4
        ),
        CareItem(
            pet_id=chessie.id,
            name="Denamarin",
            description="Liver supplement",
            notes="Give on empty stomach, at least 1 hour before food, and at least 2 hours after food",
            category="medication",
            display_order=5
        ),
        CareItem(
            pet_id=chessie.id,
            name="Dinner",
            description="Evening meal",
            notes="",
            category="food",
            display_order=6
        ),
        CareItem(
            pet_id=chessie.id,
            name="Dental Chew",
            description="Daily dental health treat",
            notes="Give after dinner",
            category="supplement",
            display_order=7
        ),
    ]
    
    for item in care_items:
        db.add(item)
    
    db.commit()
    print(f"Created Chessie (ID: {chessie.id}) with {len(care_items)} care items.")
    return chessie


def seed_dan_data(db: Session):
    """
    Seed Dan's personal care items, scoped to the 'Danny murda' user account.
    These items are only visible when logged in as Danny murda.
    
    If the Danny murda account doesn't exist yet, skip seeding
    (items will be created once the account exists and seed runs again).
    """
    # Look up the Danny murda user account
    dan_user = db.query(User).filter(User.name == "Danny murda").first()
    if not dan_user:
        print("Danny murda account not found. Skipping Dan's seed data (will retry on next startup).")
        return None

    # Check if Dan's subject already exists
    existing = db.query(Pet).filter(Pet.name == "Dan", Pet.owner_id == dan_user.id).first()
    if existing:
        print("Dan already exists in database. Skipping seed.")
        return existing
    
    dan = Pet(
        name="Dan",
        species="human",
        notes="Daily supplements and medications",
        owner_id=dan_user.id,
    )
    db.add(dan)
    db.flush()
    
    care_items = [
        CareItem(
            pet_id=dan.id,
            name="Minoxidil",
            description="Topical hair growth treatment",
            notes="Apply to scalp",
            category="medication",
            display_order=1,
        ),
        CareItem(
            pet_id=dan.id,
            name="Claritin",
            description="Loratadine — daily antihistamine",
            notes="",
            category="medication",
            display_order=2,
        ),
        CareItem(
            pet_id=dan.id,
            name="Fish Oil",
            description="Omega-3 fatty acid supplement",
            notes="Take with food",
            category="supplement",
            display_order=3,
        ),
        CareItem(
            pet_id=dan.id,
            name="Calcium Citrate",
            description="Calcium supplement (citrate form)",
            notes="Take with food",
            category="supplement",
            display_order=4,
        ),
        CareItem(
            pet_id=dan.id,
            name="Vitamin D",
            description="Vitamin D3 supplement",
            notes="Take with food for better absorption",
            category="supplement",
            display_order=5,
        ),
        CareItem(
            pet_id=dan.id,
            name="Vitamin K",
            description="Vitamin K2 supplement",
            notes="Synergistic with Vitamin D and Calcium",
            category="supplement",
            display_order=6,
        ),
    ]
    
    for item in care_items:
        db.add(item)
    
    db.commit()
    print(f"Created Dan (ID: {dan.id}, owner: Danny murda) with {len(care_items)} care items.")
    return dan


def run_seed():
    """Run the seeding process."""
    init_db()
    db = SessionLocal()
    try:
        seed_chessie_data(db)
        seed_dan_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
