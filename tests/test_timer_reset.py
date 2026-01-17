import pytest
from datetime import datetime, timedelta
from models import Pet
from crud import set_pet_timer, clear_all_expired_timers
from main import daily_reset_job
from unittest.mock import patch, MagicMock

def test_clear_all_expired_timers_logic(db_session):
    """Test that only expired and alerted timers are cleared."""
    # 1. Setup pets with various timer states
    pet1 = Pet(name="Expired Alerted", species="dog")
    pet2 = Pet(name="Expired NOT Alerted", species="dog")
    pet3 = Pet(name="Active", species="dog")
    db_session.add_all([pet1, pet2, pet3])
    db_session.commit()
    
    # Pet 1: Expired and Alerted (Should be cleared)
    set_pet_timer(db_session, pet1.id, -1, "Expired Alerted")
    pet1.timer_alert_sent = True
    
    # Pet 2: Expired but NOT Alerted (Should NOT be cleared yet)
    set_pet_timer(db_session, pet2.id, -1, "Expired NOT Alerted")
    pet2.timer_alert_sent = False
    
    # Pet 3: Active (Should NOT be cleared)
    set_pet_timer(db_session, pet3.id, 1, "Active")
    pet3.timer_alert_sent = False
    
    db_session.commit()
    
    # 2. Run the clearing function
    count = clear_all_expired_timers(db_session)
    
    # 3. Verify results
    db_session.refresh(pet1)
    db_session.refresh(pet2)
    db_session.refresh(pet3)
    
    assert count == 1
    assert pet1.timer_end_time is None
    assert pet1.timer_label is None
    assert pet1.timer_alert_sent is False
    
    assert pet2.timer_end_time is not None
    assert pet3.timer_end_time is not None

def test_daily_reset_job_execution(db_session):
    """Test the daily_reset_job wrapper."""
    # Setup an expired alerted timer
    pet = Pet(name="Reset Test", species="dog")
    db_session.add(pet)
    db_session.commit()
    set_pet_timer(db_session, pet.id, -1, "Reset Test")
    pet.timer_alert_sent = True
    db_session.commit()
    
    # Mock main.SessionLocal to use our test db_session
    db_session.close = MagicMock() # Prevent closing the test session
    with patch("main.SessionLocal", return_value=db_session):
        with patch("crud.clear_all_expired_timers", wraps=clear_all_expired_timers) as mock_clear:
            daily_reset_job()
            assert mock_clear.called
    
    db_session.refresh(pet)
    assert pet.timer_end_time is None


