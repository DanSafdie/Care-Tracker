"""
Utility to check the status of a specific Twilio Message SID.
Usage: python notebooks/check_sms_status.py SMxxxx
"""
import sys
import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

def main():
    if len(sys.argv) < 2:
        print("Usage: python notebooks/check_sms_status.py <message_sid>")
        return

    sid = sys.argv[1]
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    if not all([account_sid, auth_token]):
        print("Error: Twilio credentials not configured.")
        return

    try:
        client = Client(account_sid, auth_token)
        message = client.messages(sid).fetch()
        print(f"--- Status for {sid} ---")
        print(f"From: {message.from_}")
        print(f"To: {message.to}")
        print(f"Status: {message.status}")
        if message.error_code:
            print(f"Error Code: {message.error_code}")
            print(f"Error Message: {message.error_message}")
        print(f"Date Created: {message.date_created}")
    except Exception as e:
        print(f"Error fetching message details: {e}")

if __name__ == "__main__":
    main()

