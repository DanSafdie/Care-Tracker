import sys
import os
from datetime import datetime, date, time
import pytz
import pytest

# Add backend to path (already handled in conftest but good for IDE resolution if run directly)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "backend")))

from utils import get_care_day, to_local_time

class TestCareDayLogic:
    def test_care_day_normal_hours(self):
        """Test that noon counts as the same day."""
        tz = pytz.timezone("America/New_York")
        # Jan 1st, 12:00 PM
        dt = tz.localize(datetime(2025, 1, 1, 12, 0, 0))
        assert get_care_day(dt) == date(2025, 1, 1)

    def test_care_day_late_night(self):
        """Test that 3:59 AM counts as the previous day."""
        tz = pytz.timezone("America/New_York")
        # Jan 2nd, 3:59 AM -> Should still be Jan 1st
        dt = tz.localize(datetime(2025, 1, 2, 3, 59, 59))
        assert get_care_day(dt) == date(2025, 1, 1)

    def test_care_day_reset(self):
        """Test that 4:00 AM counts as the new day."""
        tz = pytz.timezone("America/New_York")
        # Jan 2nd, 4:00 AM -> Should be Jan 2nd
        dt = tz.localize(datetime(2025, 1, 2, 4, 0, 0))
        assert get_care_day(dt) == date(2025, 1, 2)

    def test_timezone_conversion(self):
        """Test UTC to Local conversion."""
        # 5 PM UTC is 12 PM EST (standard time) or 1 PM EDT
        # For simplicity, let's pick a winter date (EST is UTC-5)
        utc_dt = datetime(2025, 1, 1, 17, 0, 0) # 17:00 UTC
        
        local_dt = to_local_time(utc_dt)
        # Should be 12:00 PM EST
        assert local_dt.hour == 12
        assert local_dt.day == 1

