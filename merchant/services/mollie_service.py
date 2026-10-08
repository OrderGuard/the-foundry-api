from mollie.api.client import Client
from mollie.api.error import UnauthorizedError, Error
from merchant.utils import refresh_mollie_token, ensure_valid_token
import logging

logger = logging.getLogger(__name__)


class MollieService:
    """
    Service class for interacting with the Mollie API.

    This class encapsulates all Mollie API operations for a specific merchant,
    including automatic access token validation and refresh.

    Attributes:
        merchant: Merchant model instance containing OAuth credentials and
            Mollie configuration.
    """

    def __init__(self, merchant):
        """
        Initialize the Mollie service.

        Args:
            merchant: Merchant model instance that owns the Mollie account.
        """
        self.merchant = merchant

    def _get_client(self):
        """
        Create and return an authenticated Mollie API client.

        Before creating the client, the merchant's OAuth access token is
        validated and refreshed if necessary. The merchant object is then
        reloaded from the database to ensure the latest token is used.

        Returns:
            Client: Authenticated Mollie API client.
        """
        logger.info(f"[MOLLIE] Checking token for merchant {self.merchant.id}")

        ensure_valid_token(self.merchant)

        # Reload object to get the latest access token after a possible refresh.
        self.merchant.refresh_from_db()

        logger.info(f"[MOLLIE] Using token: {self.merchant.oauth_access_token}")

        client = Client()
        client.set_access_token(self.merchant.oauth_access_token)
        return client

    def create_payment(self, payload):
        """
        Create a payment in Mollie.

        Automatically sets the payment mode (test/live) based on the merchant's
        configuration. If the access token has expired, it is refreshed and the
        payment creation is retried once.

        Args:
            payload (dict): Mollie payment request payload.

        Returns:
            Payment: Mollie Payment object.

        Raises:
            Error: If the Mollie API returns an error other than an expired
                access token.
        """
        logger.info(f"[MOLLIE] Creating payment for merchant {self.merchant.id}")

        client = self._get_client()

        # Force the correct payment mode.
        is_test = self.merchant.mollie_mode == "test"
        payload["testmode"] = is_test

        try:
            payment = client.payments.create(payload)
            logger.info(f"[MOLLIE] Payment created: {payment}")
            return payment

        except UnauthorizedError:
            logger.warning(
                f"[MOLLIE] Token expired, refreshing for merchant {self.merchant.id}"
            )

            new_token = refresh_mollie_token(self.merchant)

            client.set_access_token(new_token)

            payment = client.payments.create(payload)
            logger.info(f"[MOLLIE] Payment created after refresh: {payment}")
            return payment

        except Error as e:
            logger.error(f"[MOLLIE] Payment error: {str(e)}")
            raise

    def get_payment(self, payment_id):
        client = self._get_client()

        is_test = self.merchant.mollie_mode == "test"

        logger.info(f"Fetching payment in testmode={is_test}")

        return client.payments.get(
            payment_id
            # payment_id,
            # testmode="true" if is_test else "false",
        )

