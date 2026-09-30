from sib_api_v3_sdk import ApiClient, Configuration, TransactionalSMSApi
from sib_api_v3_sdk.models import SendTransacSms
from decouple import config
import logging

logger = logging.getLogger(__name__)


def send_booking_sms_notification(booking, status=None):

    if not booking.phone:
        logger.warning(f"[SMS] Booking {booking.id} has no phone number")
        return

    # Normalize status (use argument OR booking.status)
    status = status or booking.status

    date_str = booking.date.strftime("%A, %d %B %Y")
    time_str = booking.time.strftime("%I:%M %p")

    # ✅ CONFIRMED
    if status == "confirmed":
        message = (
            f"🍽 Klub Kitchen 83\n\n"
            f"Hi {booking.name},\n\n"
            f"Your booking #{booking.id} is CONFIRMED ✅\n\n"
            f"Date: {date_str}\n"
            f"Time: {time_str}\n"
            f"Guests: {booking.people}\n\n"
            f"We look forward to seeing you!"
        )

    # ❌ CANCELLED
    elif status == "cancelled":
        message = (
            f"🍽 Klub Kitchen 83\n\n"
            f"Hi {booking.name},\n\n"
            f"Your booking #{booking.id} has been CANCELLED ❌\n\n"
            f"Date: {date_str}\n"
            f"Time: {time_str}\n\n"
            f"If this is a mistake, please contact us."
        )

    else:
        logger.info(f"[SMS] Booking {booking.id} status '{status}' ignored")
        return

    try:
        logger.info(f"[SMS] Sending SMS for Booking {booking.id}")

        config_brevo = Configuration()
        config_brevo.api_key["api-key"] = config("BREVO_API_KEY")

        api_instance = TransactionalSMSApi(ApiClient(config_brevo))

        sms = SendTransacSms(
            sender=config("BREVO_SMS_SENDER"),
            recipient=booking.phone,
            content=message,
            type="transactional",
        )

        response = api_instance.send_transac_sms(sms)

        logger.info(f"[SMS SUCCESS] Booking {booking.id} | {response}")

        return response

    except Exception as e:
        logger.error(
            f"[SMS ERROR] Booking {booking.id} | Error: {str(e)}",
            exc_info=True,
        )

