"""
SMS utility for Care-Tracker using Twilio.
"""
import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


def mask_phone(number: str) -> str:
    """Mask a phone number for safe logging, e.g. +1***...7890"""
    if not number or len(number) < 6:
        return "***"
    return f"{number[:2]}***{number[-4:]}"


def send_sms(to_number: str, body: str) -> bool:
    """
    Sends an SMS message using Twilio.
    
    Args:
        to_number: The recipient's phone number in E.164 format (e.g., +1234567890)
        body: The message content
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    if not all([account_sid, auth_token, from_number]):
        print("SMS Warning: Twilio credentials not fully configured in environment.")
        return False

    if not to_number:
        return False

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number
        )
        print(f"SMS Sent successfully: {message.sid}")
        # Log the status immediately to catch A2P issues
        print(f"Initial Status: {message.status}")
        return True
    except Exception as e:
        print(f"Failed to send SMS to {mask_phone(to_number)}: {e}")
        return False

