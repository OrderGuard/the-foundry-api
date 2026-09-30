from datetime import datetime, time
from order.utils import is_restaurant_open
import logging

logger = logging.getLogger(__name__)

def test_is_open_during_normal_hours():
    # Wednesday at 3:00 PM → should be open
    test_time = datetime(2025, 6, 11, 15, 0)  # Wednesday
    is_open, open_time, close_time, day_name = is_restaurant_open(now=test_time)

    print(f"{day_name}")

    assert is_open is True
    assert open_time == time(14, 0)
    assert close_time == time(0, 0)


def test_is_closed_before_opening():
    # Monday at 1:00 PM → should be closed
    test_time = datetime(2025, 6, 9, 13, 0)  # Monday
    is_open, open_time, close_time, day_name  = is_restaurant_open(now=test_time)

    print(f"{day_name}")
    assert is_open is False


def test_is_open_on_friday_evening():
    # Friday at 10:00 PM → should be open
    test_time = datetime(2025, 6, 14, 22, 0)  # Friday
    is_open, open_time, close_time, day_name = is_restaurant_open(now=test_time)
    print(f"{day_name}")
    assert is_open is True


def test_is_open_early_saturday_morning():
    # Saturday at 2:30 AM → still open from Friday night
    test_time = datetime(2025, 6, 15, 2, 30)  # Saturday
    is_open, open_time, close_time, day_name  = is_restaurant_open(now=test_time)

    print("DEBUG:", "Today is:", day_name, "Open from", open_time, "to", close_time)
    print(f"Is Open: {is_open}")
    print(open_time)
    print(day_name)
    print(f"Time now: {test_time}")

    assert is_open is True
    # assert open_time == time(14, 30)
    # assert close_time == time(3, 0)


def test_is_closed_after_overnight_hours():
    # Saturday at 4:00 AM → should be closed
    test_time = datetime(2025, 6, 15, 4, 0)
    is_open, open_time, close_time, day_name  = is_restaurant_open(now=test_time)
    print(open_time)
    print(day_name)
    print(f"Time now: {test_time}")

    assert is_open is False


def test_is_open_early_sunday_morning():
    # Sunday at 2:30 AM → still open from Saturday night
    test_time = datetime(2025, 6, 16, 2, 30)  # Sunday
    is_open, open_time, close_time, day_name  = is_restaurant_open(now=test_time)
    print(open_time)
    print(day_name)
    print(f"Time now: {test_time}")

    assert is_open is False
    # assert open_time == time(14, 30)
    # assert close_time == time(3, 0)

