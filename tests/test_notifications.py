import pytest
from datetime import datetime, date, timedelta
from models import User, Pet
from schemas import UserUpdate
from crud import update_user, set_pet_timer
from main import check_timers_job
from unittest.mock import patch, MagicMock

class TestNotifications:
    def test_user_update_notification_fields(self, db_session):
        """Test that user notification fields can be updated."""
        user = User(name="Test User")
        db_session.add(user)
        db_session.commit()
        
        update_data = UserUpdate(
            phone_number="+1234567890",
            wants_alerts=True,
            alert_expiry_date=date.today() + timedelta(days=7)
        )
        updated_user = update_user(db_session, user.id, update_data)
        
        assert updated_user.phone_number == "+1234567890"
        assert updated_user.wants_alerts is True
        assert updated_user.alert_expiry_date == date.today() + timedelta(days=7)

    @patch("main.send_sms")
    @patch("main.get_care_day")
    def test_timer_alert_expiry_logic(self, mock_get_care_day, mock_send_sms, db_session):
        """Test that alerts are sent only when not expired."""
        # Fix the care day for predictable testing
        today = date(2026, 1, 3)
        mock_get_care_day.return_value = today
        
        # Setup: Pet with expired timer
        pet = Pet(name="Buddy", species="dog")
        db_session.add(pet)
        db_session.commit()
        set_pet_timer(db_session, pet.id, -1, "Test Timer") # Expired 1 hour ago
    
        # Setup: Active user (expires tomorrow)
        user_active = User(
            name="Active User", 
            phone_number="+1000000000", 
            wants_alerts=True,
            alert_expiry_date=today + timedelta(days=1)
        )
        # Setup: Expired user (expired yesterday)
        user_expired = User(
            name="Expired User", 
            phone_number="+2000000000", 
            wants_alerts=True,
            alert_expiry_date=today - timedelta(days=1)
        )
        db_session.add_all([user_active, user_expired])
        db_session.commit()
        
        # Run the timer check job
        # We need to mock SessionLocal in main to use our test db_session
        # We also mock .close() so the session stays open for our verification
        db_session.close = MagicMock()
        with patch("main.SessionLocal", return_value=db_session):
            check_timers_job()
        
        # Verify: Only Active User got the SMS
        mock_send_sms.assert_called_once_with("+1000000000", "⏰ Timer for Buddy (Test Timer) has run out!")
    
        # Verify: Timer was NOT cleared, but marked as alerted
        # We need to expire the object to force a reload since it was changed in the "job"
        db_session.expire_all()
        assert pet.timer_end_time is not None
        assert pet.timer_alert_sent is True

    @patch("main.send_sms")
    def test_signup_confirmation_sms(self, mock_send_sms, client):
        """Test that an SMS is sent when a new user signs up with alerts."""
        payload = {
            "name": "New Tester",
            "phone_number": "+15551112222",
            "wants_alerts": True,
            "alert_expiry_date": (date.today() + timedelta(days=7)).isoformat()
        }
        response = client.post("/api/users/check-in", json=payload)
        assert response.status_code == 200
        
        # Verify SMS was sent
        assert mock_send_sms.called
        args, _ = mock_send_sms.call_args
        assert "+15551112222" in args
        assert "Welcome to the pack" in args[1]
        assert str(date.today() + timedelta(days=7)) in args[1]

    @patch("main.send_sms")
    def test_update_confirmation_sms(self, mock_send_sms, client):
        """Test that an SMS is re-triggered when alert settings are updated."""
        # 1. Create user first
        setup_resp = client.post("/api/users/check-in", json={"name": "Update Tester"})
        user_id = setup_resp.json()["user"]["id"]
        mock_send_sms.reset_mock()
        
        # 2. Update with alerts enabled
        update_payload = {
            "phone_number": "+15559998888",
            "wants_alerts": True
        }
        response = client.put(f"/api/users/{user_id}", json=update_payload)
        assert response.status_code == 200
        
        # Verify SMS was sent to the new number
        mock_send_sms.assert_called_once()
        args, _ = mock_send_sms.call_args
        assert "+15559998888" in args
        assert "Update Tester" in args[1]

