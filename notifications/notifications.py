from exponent_server_sdk import (
    PushClient,
    PushMessage,
    DeviceNotRegisteredError,
    PushServerError,
    PushTicketError,
)
from requests.exceptions import ConnectionError, HTTPError
import logging

logger = logging.getLogger(__name__)

def send_push_notification(token: str, title: str, body: str, data: dict = None):
    try:
        response = PushClient().publish(
            PushMessage(
                to=token,
                title=title,
                body=body,
                data=data or {},
                sound="default",
            )
        )

        # Log the raw response object
        logger.info(f"Expo response for {token}: {response}")

        # Validate response to catch errors
        try:
            response.validate_response()
        except DeviceNotRegisteredError:
            logger.warning(f"❌ Device not registered: {token}")
            # Here you could delete token from DB if you want
        except PushTicketError as e:
            logger.error(f"❌ Push ticket error for {token}: {e}")
        except Exception as e:
            logger.error(f"❌ Unknown validation error for {token}: {e}")

        return response

    except (PushServerError, ConnectionError, HTTPError) as e:
        logger.error(f"❌ Failed to send push to {token}: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error sending to {token}: {e}")

