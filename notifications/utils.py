# notifications/utils.py
import logging
import os
import json
import base64
import firebase_admin
from firebase_admin import credentials, messaging
from exponent_server_sdk import PushClient, PushMessage, DeviceNotRegisteredError, PushServerError, PushTicketError
from requests.exceptions import ConnectionError, HTTPError

logger = logging.getLogger(__name__)

# Initialize Firebase Admin once
if not firebase_admin._apps:
    firebase_b64 = os.environ.get("FIREBASE_SERVICE_ACCOUNT_B64")
    if not firebase_b64:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_B64 is not set in environment variables!")
    service_account_info = json.loads(base64.b64decode(firebase_b64))
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)
    logger.info("✅ Firebase Admin initialized successfully")

def send_push_notification(token: str, title: str, body: str, data: dict = None):
    """
    Send push notification via Expo. Uses FCM (Firebase Cloud Messaging) under the hood for Android.
    """
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

        logger.info(f"Expo response for {token}: {response}")

        # Validate response
        try:
            response.validate_response()
        except DeviceNotRegisteredError:
            logger.warning(f"❌ Device not registered: {token}")
        except PushTicketError as e:
            logger.error(f"❌ Push ticket error for {token}: {e}")
        except Exception as e:
            logger.error(f"❌ Unknown validation error for {token}: {e}")

        return response

    except (PushServerError, ConnectionError, HTTPError) as e:
        logger.error(f"❌ Failed to send push to {token}: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error sending to {token}: {e}")

