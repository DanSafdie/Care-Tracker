"""
Utility to send a test SMS using the project's Twilio configuration.
Usage: python notebooks/send_test_sms.py +1234567890
"""
import sys
import os

# Add the backend directory to path so we can import sms_utils
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app", "backend"))

from sms_utils import send_sms

def main():
    if len(sys.argv) < 2:
        print("Usage: python notebooks/send_test_sms.py <phone_number>")
        print("Example: python notebooks/send_test_sms.py +17755551234")
        return

    to_number = sys.argv[1]
    print(f"Attempting to send test SMS to {to_number}...")
    
    success = send_sms(to_number, "🐾 Care-Tracker: This is a test message to confirm your Twilio integration is working!")
    
    if success:
        print("✅ Test SMS sent successfully!")
    else:
        print("❌ Failed to send test SMS. Check your .env file and console output for errors.")

if __name__ == "__main__":
    main()

