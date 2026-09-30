from sib_api_v3_sdk import ApiClient, Configuration, TransactionalSMSApi
from sib_api_v3_sdk.models import SendTransacSms
from decouple import config
import logging

logger = logging.getLogger(__name__)


def send_order_sms_notification(order, status=None):

    if not order.phone_number:
        logger.warning(f"[SMS] Order {order.id} has no phone number")
        return

    if status == "preparing":
        message = (
            f"🍔 Klub Kitchen 83\n\n"
            f"Hi {order.customer_name or 'there'},\n\n"
            f"Your order #{order.id} is now being prepared.\n\n"
            f"Estimated time: {order.estimated_time} mins.\n\n"
            # f"We'll notify you when it's ready."
        )
    else:
        return  # 🚫 no SMS for other statuses

    try:
        logger.info(f"[SMS] Sending SMS for Order {order.id}")

        config_brevo = Configuration()
        config_brevo.api_key['api-key'] = config("BREVO_API_KEY")

        api_instance = TransactionalSMSApi(ApiClient(config_brevo))

        sms = SendTransacSms(
            sender=config("BREVO_SMS_SENDER"),
            recipient=order.phone_number,
            content=message,
            type="transactional",
        )

        response = api_instance.send_transac_sms(sms)

        logger.info(f"[SMS SUCCESS] Order {order.id} | {response}")

    except Exception as e:
        logger.error(
            f"[SMS ERROR] Order {order.id} | Error: {str(e)}",
            exc_info=True,
        )
