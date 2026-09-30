# order/utils.py
from datetime import datetime, time, timedelta
import calendar
from decimal import Decimal

# Sunday = 0, Monday = 1, ..., Saturday = 6
SCHEDULE = {
    0: (time(14, 0), time(0, 0)),     # Sunday: 2:00 PM – 12:00 AM
    1: (time(14, 0), time(0, 0)),     # Monday
    2: (time(14, 0), time(0, 0)),     # Tuesday
    3: (time(14, 0), time(0, 0)),     # Wednesday
    4: (time(14, 0), time(0, 0)),     # Thursday
    5: (time(14, 30), time(3, 0)),    # Friday
    6: (time(14, 30), time(3, 0)),    # Saturday
}


def is_restaurant_open(now=None):
    now = now or datetime.now()

    # Adjust Python's weekday: Monday=0 -> Sunday=0
    python_weekday = now.weekday()  # Monday=0
    weekday = (python_weekday + 1) % 7  # Sunday=0

    # First check today's schedule
    open_time, close_time = SCHEDULE[weekday]
    open_dt = now.replace(hour=open_time.hour, minute=open_time.minute, second=0, microsecond=0)

    if close_time <= open_time:
        close_dt = open_dt + timedelta(days=1)
        close_dt = close_dt.replace(hour=close_time.hour, minute=close_time.minute)
    else:
        close_dt = open_dt.replace(hour=close_time.hour, minute=close_time.minute)

    if open_dt <= now < close_dt:
        return True, open_time, close_time, calendar.day_name[python_weekday]

    # Check previous day for overnight open
    prev_weekday = (weekday - 1) % 7
    prev_open_time, prev_close_time = SCHEDULE[prev_weekday]
    if prev_close_time <= prev_open_time:
        prev_open_dt = now - timedelta(days=1)
        prev_open_dt = prev_open_dt.replace(hour=prev_open_time.hour, minute=prev_open_time.minute, second=0, microsecond=0)
        prev_close_dt = prev_open_dt + timedelta(days=1)
        prev_close_dt = prev_close_dt.replace(hour=prev_close_time.hour, minute=prev_close_time.minute)

        if prev_open_dt <= now < prev_close_dt:
            return True, prev_open_time, prev_close_time, calendar.day_name[(python_weekday - 1) % 7]

    return False, open_time, close_time, calendar.day_name[python_weekday]


def decimal_to_float(obj):
    """Recursively convert Decimal to float in dicts/lists"""

    if isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

# Restaurant weekly schedule
# SCHEDULE = {
    # 0: (time(14, 0), time(0, 0)),     # Monday
    # 1: (time(14, 0), time(0, 0)),     # Tuesday
    # 2: (time(14, 0), time(0, 0)),     # Wednesday
    # 3: (time(14, 0), time(0, 0)),     # Thursday
    # 4: (time(14, 30), time(3, 0)),    # Friday
    # 5: (time(14, 30), time(3, 0)),    # Saturday
    # 6: (time(14, 0), time(0, 0)),     # Sunday
# }

# def is_restaurant_open(now=None):
    # now = now or datetime.now()
    # weekday = now.weekday()  # Monday = 0, Sunday = 6
    # day_name = calendar.day_name[weekday]  # e.g. "Friday"
    # today_schedule = SCHEDULE.get(weekday)

    # if not today_schedule:
        # return False, None, None, day_name

    # open_time, close_time = today_schedule

    # open_dt = now.replace(hour=open_time.hour, minute=open_time.minute, second=0, microsecond=0)

    # # Handle overnight close
    # if close_time <= open_time:
        # close_dt = open_dt + timedelta(days=1)
        # close_dt = close_dt.replace(hour=close_time.hour, minute=close_time.minute)
    # else:
        # close_dt = open_dt.replace(hour=close_time.hour, minute=close_time.minute)

    # is_open = open_dt <= now < close_dt
    # return is_open, open_time, close_time, day_name

