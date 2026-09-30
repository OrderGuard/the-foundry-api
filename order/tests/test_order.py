from datetime import datetime
from django.test import TestCase
from order.utils import is_restaurant_open


class TestRestaurantSchedule(TestCase):
    def test_is_open_friday_3pm(self):
        # June 13, 2025 is a Friday
        now = datetime(2025, 6, 13, 15, 0)  # 3:00 PM
        is_open, open_time, close_time, day_name = is_restaurant_open(now)

        print(f"DEBUG: Today is: {day_name}, now: {now}, Open from: {open_time} to {close_time}")

        self.assertTrue(is_open)
        # self.assertEqual(open_time.hour, 14)
        # self.assertEqual(open_time.minute, 30)
        # self.assertEqual(close_time.hour, 3)
        # self.assertEqual(close_time.minute, 0)

    def test_is_not_open_friday_2pm(self):
        # June 13, 2025 is a Friday
        now = datetime(2025, 6, 13, 14, 0)  # 2:00 PM
        is_open, open_time, close_time, day_name = is_restaurant_open(now)

        print(f"DEBUG: Today is: {day_name}, now: {now}, Open from: {open_time} to {close_time}")

        # self.assertTrue(is_open)
        self.assertFalse(is_open)
        # self.assertEqual(open_time.hour, 14)
        # self.assertEqual(open_time.minute, 30)
        # self.assertEqual(close_time.hour, 3)
        # self.assertEqual(close_time.minute, 0)
