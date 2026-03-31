import pytest
from datetime import datetime, date, timedelta
from models import User, Pet, CareItem
from schemas import UserUpdate
from crud import update_user, set_pet_timer
from main import check_timers_job, nightly_reminder_job
from auth import hash_password
from unittest.mock import patch, MagicMock, call

# Reusable placeholder hash for direct-DB user creation in tests
_PW_HASH = hash_password("testpass")

class TestNotifications:
    def test_user_update_notification_fields(self, db_session):
        """Test that user notification fields can be updated."""
        user = User(name="Test User", password_hash=_PW_HASH)
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
        today = date(2026, 1, 3)
        mock_get_care_day.return_value = today
        
        pet = Pet(name="Buddy", species="dog")
        db_session.add(pet)
        db_session.commit()
        set_pet_timer(db_session, pet.id, -1, "Test Timer")
    
        user_active = User(
            name="Active User",
            password_hash=_PW_HASH,
            phone_number="+1000000000", 
            wants_alerts=True,
            alert_expiry_date=today + timedelta(days=1)
        )
        user_expired = User(
            name="Expired User",
            password_hash=_PW_HASH,
            phone_number="+2000000000", 
            wants_alerts=True,
            alert_expiry_date=today - timedelta(days=1)
        )
        db_session.add_all([user_active, user_expired])
        db_session.commit()
        
        db_session.close = MagicMock()
        with patch("main.SessionLocal", return_value=db_session):
            check_timers_job()
        
        mock_send_sms.assert_called_once_with("+1000000000", "⏰ Timer for Buddy (Test Timer) has run out!")
    
        db_session.expire_all()
        assert pet.timer_end_time is not None
        assert pet.timer_alert_sent is True

    @patch("main.send_sms")
    def test_signup_confirmation_sms(self, mock_send_sms, auth_client):
        """Test that an SMS is sent when a new user signs up with alerts via check-in."""
        client, _ = auth_client
        payload = {
            "name": "New Tester",
            "phone_number": "+15551112222",
            "wants_alerts": True,
            "alert_expiry_date": (date.today() + timedelta(days=7)).isoformat()
        }
        response = client.post("/api/users/check-in", json=payload)
        assert response.status_code == 200
        
        assert mock_send_sms.called
        args, _ = mock_send_sms.call_args
        assert "+15551112222" in args
        assert "Welcome to the pack" in args[1]
        assert str(date.today() + timedelta(days=7)) in args[1]

    @patch("main.send_sms")
    def test_update_confirmation_sms(self, mock_send_sms, auth_client):
        """Test that an SMS is re-triggered when alert settings are updated."""
        client, user = auth_client
        mock_send_sms.reset_mock()
        
        update_payload = {
            "phone_number": "+15559998888",
            "wants_alerts": True
        }
        response = client.put(f"/api/users/{user.id}", json=update_payload)
        assert response.status_code == 200
        
        mock_send_sms.assert_called_once()
        args, _ = mock_send_sms.call_args
        assert "+15559998888" in args
        assert "Test User" in args[1]


class TestPrivateItemAlerts:
    """Tests that private pets/items only send text alerts to their owner."""

    @patch("main.send_sms")
    @patch("main.get_care_day")
    def test_private_pet_timer_alert_only_sent_to_owner(
        self, mock_get_care_day, mock_send_sms, db_session
    ):
        """A private pet's timer alert should only go to the owner, not all users."""
        today = date(2026, 3, 28)
        mock_get_care_day.return_value = today

        owner = User(
            name="Owner", password_hash=_PW_HASH,
            phone_number="+1111111111", wants_alerts=True,
        )
        other_user = User(
            name="Other", password_hash=_PW_HASH,
            phone_number="+2222222222", wants_alerts=True,
        )
        db_session.add_all([owner, other_user])
        db_session.commit()

        # Private pet owned by 'Owner'
        pet = Pet(name="Secret", species="cat", is_private=True, owner_id=owner.id)
        db_session.add(pet)
        db_session.commit()
        set_pet_timer(db_session, pet.id, -1, "Private Timer")

        db_session.close = MagicMock()
        with patch("main.SessionLocal", return_value=db_session):
            check_timers_job()

        # Only the owner should have received the SMS
        mock_send_sms.assert_called_once_with(
            "+1111111111", "⏰ Timer for Secret (Private Timer) has run out!"
        )

    @patch("main.send_sms")
    @patch("main.get_care_day")
    def test_public_pet_timer_alert_sent_to_everyone(
        self, mock_get_care_day, mock_send_sms, db_session
    ):
        """A public (non-private) pet's timer alert should go to all opted-in users."""
        today = date(2026, 3, 28)
        mock_get_care_day.return_value = today

        user_a = User(
            name="Alice", password_hash=_PW_HASH,
            phone_number="+1111111111", wants_alerts=True,
        )
        user_b = User(
            name="Bob", password_hash=_PW_HASH,
            phone_number="+2222222222", wants_alerts=True,
        )
        db_session.add_all([user_a, user_b])
        db_session.commit()

        pet = Pet(name="Buddy", species="dog")  # is_private defaults to False
        db_session.add(pet)
        db_session.commit()
        set_pet_timer(db_session, pet.id, -1, "Walk Timer")

        db_session.close = MagicMock()
        with patch("main.SessionLocal", return_value=db_session):
            check_timers_job()

        assert mock_send_sms.call_count == 2
        called_numbers = {c.args[0] for c in mock_send_sms.call_args_list}
        assert called_numbers == {"+1111111111", "+2222222222"}

    @patch("main.send_sms")
    @patch("main.get_care_day")
    def test_nightly_reminder_excludes_private_pet_from_non_owner(
        self, mock_get_care_day, mock_send_sms, db_session
    ):
        """Nightly reminder should not include private pet tasks for non-owners."""
        today = date(2026, 3, 28)
        mock_get_care_day.return_value = today

        owner = User(
            name="Owner", password_hash=_PW_HASH,
            phone_number="+1111111111", wants_alerts=True,
        )
        other_user = User(
            name="Other", password_hash=_PW_HASH,
            phone_number="+2222222222", wants_alerts=True,
        )
        db_session.add_all([owner, other_user])
        db_session.commit()

        # Private pet with an incomplete care item
        private_pet = Pet(name="Secret", species="cat", is_private=True, owner_id=owner.id)
        db_session.add(private_pet)
        db_session.commit()

        care_item = CareItem(
            pet_id=private_pet.id, name="Secret Meds", category="medication",
        )
        db_session.add(care_item)
        db_session.commit()

        db_session.close = MagicMock()
        with patch("main.SessionLocal", return_value=db_session):
            nightly_reminder_job()

        # Only the owner should get the nightly reminder about the private pet
        assert mock_send_sms.call_count == 1
        args, _ = mock_send_sms.call_args
        assert args[0] == "+1111111111"
        assert "Secret" in args[1]
        assert "Secret Meds" in args[1]

    @patch("main.send_sms")
    @patch("main.get_care_day")
    def test_nightly_reminder_excludes_private_care_item_from_non_owner(
        self, mock_get_care_day, mock_send_sms, db_session
    ):
        """A private care item on a public pet is excluded from non-owners' reminders."""
        today = date(2026, 3, 28)
        mock_get_care_day.return_value = today

        owner = User(
            name="Owner", password_hash=_PW_HASH,
            phone_number="+1111111111", wants_alerts=True,
        )
        other_user = User(
            name="Other", password_hash=_PW_HASH,
            phone_number="+2222222222", wants_alerts=True,
        )
        db_session.add_all([owner, other_user])
        db_session.commit()

        # Public pet
        pet = Pet(name="Buddy", species="dog")
        db_session.add(pet)
        db_session.commit()

        # One public item, one private item
        public_item = CareItem(
            pet_id=pet.id, name="Breakfast", category="food",
        )
        private_item = CareItem(
            pet_id=pet.id, name="Private Supplement", category="supplement",
            is_private=True, owner_id=owner.id,
        )
        db_session.add_all([public_item, private_item])
        db_session.commit()

        db_session.close = MagicMock()
        with patch("main.SessionLocal", return_value=db_session):
            nightly_reminder_job()

        # Both users should get a message (public item is pending for both)
        assert mock_send_sms.call_count == 2

        # Find the message sent to each user
        msgs = {c.args[0]: c.args[1] for c in mock_send_sms.call_args_list}

        # Owner sees both items
        assert "Breakfast" in msgs["+1111111111"]
        assert "Private Supplement" in msgs["+1111111111"]

        # Other user sees only the public item
        assert "Breakfast" in msgs["+2222222222"]
        assert "Private Supplement" not in msgs["+2222222222"]
