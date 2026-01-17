import pytest
from unittest.mock import patch
from main import sync_led_status
from models import Pet
from datetime import datetime, timedelta

def test_sync_led_status_logic(db_session):
    """Verify LED logic priority: Expired > Active > Clear"""
    
    # Setup: Create one pet
    pet = Pet(name="TestPet", species="dog")
    db_session.add(pet)
    db_session.commit()

    with patch("main.call_hass_script") as mock_script:
        # 1. Test Active Timer -> Should be Yellow
        pet.timer_end_time = datetime.now() + timedelta(hours=1)
        db_session.commit()
        sync_led_status(db_session)
        mock_script.assert_called_with("downstairs_spotlight_led_yellow_solid")

        # 2. Test Expired Timer -> Should be Green (takes priority)
        pet.timer_end_time = datetime.now() - timedelta(hours=1)
        db_session.commit()
        sync_led_status(db_session)
        mock_script.assert_called_with("downstairs_spotlight_led_green_pulse")

        # 3. Test No Timer -> Should be Clear
        pet.timer_end_time = None
        db_session.commit()
        sync_led_status(db_session)
        mock_script.assert_called_with("downstairs_spotlight_led_clear")
