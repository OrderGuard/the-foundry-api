from django.core.mail import send_mail
from django.conf import settings


def send_booking_status_email(booking):

    if booking.status == "confirmed":
        subject = "✅ Booking Confirmed"
        message = f"""
Hello {booking.name},

Your booking has been CONFIRMED.

Date: {booking.date}
Time: {booking.time}
Guests: {booking.people}

We look forward to seeing you!
"""

    elif booking.status == "cancelled":
        subject = "❌ Booking Cancelled"
        message = f"""
Hello {booking.name},

Unfortunately your booking has been cancelled.

Date: {booking.date}
Time: {booking.time}

Please contact us if you have questions.
"""
    else:
        return

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [booking.email],
        fail_silently=False,
    )

