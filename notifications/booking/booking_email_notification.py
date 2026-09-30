from sib_api_v3_sdk import ApiClient, Configuration, TransactionalEmailsApi
from sib_api_v3_sdk.models import SendSmtpEmail
from decouple import config
from datetime import datetime


def send_booking_status_email(booking):
    time_obj = datetime.strptime(booking.time, "%H:%M").time()
    formatted_time = time_obj.strftime("%I:%M %p")

    if booking.status == "confirmed":
        subject = "✅ Booking Confirmed"

        html_content = f"""
        <p>Hi {booking.name},</p>

        <p>Your booking has been confirmed.</p>

        <ul>
            <li>Date: {booking.date}</li>
            <li>Time: {formatted_time}</li>
            <li>Guests: {booking.people}</li>
        </ul>

        <p>We look forward to welcoming you.</p>
        """

    elif booking.status == "cancelled":
        subject = "❌ Booking Cancelled"

        html_content = f"""
        <p>Hi {booking.name},</p>

        <p>Unfortunately, your booking has been cancelled.</p>

        <ul>
            <li>Date: {booking.date}</li>
            <li>Time: {formatted_time}</li>
            <li>Guests: {booking.people}</li>
        </ul>

        <p>If you have any questions, please contact us.</p>
        """

    else:
        return

    configuration = Configuration()
    configuration.api_key["api-key"] = config("BREVO_API_KEY")

    api_instance = TransactionalEmailsApi(
        ApiClient(configuration)
    )

    email = SendSmtpEmail(
        to=[{"email": booking.email, "name": booking.name}],
        sender={
            "email": "info@orderup.space",
            "name": "Klub Kitchen 83 Restaurant"
        },
        subject=subject,
        html_content=html_content,
    )

    api_instance.send_transac_email(email)

