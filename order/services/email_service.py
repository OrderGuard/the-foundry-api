from sib_api_v3_sdk import ApiClient, Configuration, TransactionalEmailsApi
from sib_api_v3_sdk.models import SendSmtpEmail
from decouple import config
import logging

logger = logging.getLogger(__name__)


def send_order_email_notification(order, status=None):

    if not order.customer_email:
        logger.warning(f"[EMAIL] Order {order.id} has no customer email")
        return

    SUBJECTS = {
        "new": "🧾 Order Received",
        "accepted": "✅ Order Accepted",
        "preparing": "🍳 Order Preparing",
        "ready": "🍽️ Order Ready",
        "delivering": "🚚 Order On The Way",
        "completed": "🎉 Order Completed",
        "cancelled": "❌ Order Cancelled",
    }

    subject = SUBJECTS.get(order.status)
    if not subject:
        logger.warning(f"[EMAIL] No subject for status '{order.status}' (Order {order.id})")
        return

    FRONTEND_URL = config("FRONTEND_URL")
    tracking_url = f"{FRONTEND_URL}/track/{order.tracking_token}"

    # if created:
        # status_text = "We’ve received your order 🎉"
    # else:
        # status_text = f"Your order is now {order.status.upper()}"
    status_text = f"Your order is now {order.status.upper()}"

    html_content = f"""
    <h2>Hi {order.customer_name or "there"},</h2>
    <p>{status_text}</p>

    <p><strong>Order #{order.id}</strong></p>
    <ul>
        <li>Order type: {order.order_type.title()}</li>
        <li>Estimated time: {order.estimated_time} minutes</li>
        <li>Total: £{order.get_total_amount()}</li>
    </ul>

    <p><a href="{tracking_url}">Track your order</a></p>

    <p>Thank you for ordering with Klub Kitchen 83 🍕</p>
    """

    try:
        logger.info(f"[EMAIL] Sending email for Order {order.id} to {order.customer_email}")

        config_brevo = Configuration()
        config_brevo.api_key['api-key'] = config("BREVO_API_KEY")

        api_instance = TransactionalEmailsApi(ApiClient(config_brevo))

        email = SendSmtpEmail(
            to=[{"email": order.customer_email}],
            subject=subject,
            html_content=html_content,
            sender={
                "email": "info@orderup.space",
                "name": "Klub Kitchen 83 Restaurant"
            },
        )

        response = api_instance.send_transac_email(email)

        logger.info(f"[EMAIL SUCCESS] Order {order.id} | Message ID: {response.message_id}")

    except Exception as e:
        logger.error(f"[EMAIL ERROR] Order {order.id} | Error: {str(e)}", exc_info=True)

