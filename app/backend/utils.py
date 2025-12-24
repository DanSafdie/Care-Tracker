"""
Utility functions for Pet Care Tracker.
"""
from datetime import datetime, date, time, timedelta
import pytz

# The hour at which the "care day" resets (4 AM)
DAY_RESET_HOUR = 4


def get_care_day(dt: datetime = None, timezone_str: str = "America/New_York") -> date:
    """
    Get the logical "care day" for a given datetime.
    
    The care day resets at 4 AM, not midnight.
    This means:
    - 3:59 AM on Jan 2nd is still considered Jan 1st's care day
    - 4:00 AM on Jan 2nd is the start of Jan 2nd's care day
    
    Args:
        dt: The datetime to evaluate. Defaults to current time.
        timezone_str: Timezone for determining local time. Defaults to Eastern.
    
    Returns:
        The logical care day as a date object.
    """
    if dt is None:
        # Use timezone-aware current time
        tz = pytz.timezone(timezone_str)
        dt = datetime.now(tz)
    
    # If before 4 AM, consider it the previous day
    if dt.hour < DAY_RESET_HOUR:
        return (dt - timedelta(days=1)).date()
    
    return dt.date()


def get_day_boundaries(care_day: date, timezone_str: str = "America/New_York") -> tuple[datetime, datetime]:
    """
    Get the start and end datetime for a care day.
    
    Args:
        care_day: The logical care day
        timezone_str: Timezone for the boundaries
    
    Returns:
        Tuple of (start_datetime, end_datetime) for the care day
    """
    tz = pytz.timezone(timezone_str)
    
    # Care day starts at 4 AM on the date
    start = tz.localize(datetime.combine(care_day, time(DAY_RESET_HOUR, 0, 0)))
    
    # Care day ends at 4 AM the next day
    end = start + timedelta(days=1)
    
    return start, end
