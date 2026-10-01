from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from rest_framework import status
from rest_framework.views import APIView

from .serializers import (
    OrderCreateSerializer,
    OrderReadSerializer,
    PaymentStatusSerializer,
    OrderTrackingSerializer,
    OrderHistorySerializer,
)

from rewards.models import SpinReward
from rewards.services.points_service import add_points
from .models import Order, OrderItem, OrderItemTopping, OrderItemComponent
from menu.models import MenuItem
from collections import Counter

# Mollie
from mollie.api.client import Client
from mollie.api.error import Error
from merchant.utils import ensure_valid_token
from merchant.services.mollie_service import MollieService

# Filter
from django_filters.rest_framework import DjangoFilterBackend
# csrf
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
# env
from decouple import config
from decimal import Decimal

# Notifications
from notifications.utils import send_push_notification
from notifications.models import DeviceToken
# Email Notifications
from order.services.email_service import send_order_email_notification
# Sms Notifications
from order.services.sms_service import send_order_sms_notification

# Actions
from rest_framework.decorators import action

# Websocket
from asgiref.sync import async_to_sync
from .serializers import OrderReadSerializer

# Logging
import logging

logger = logging.getLogger(__name__)

from django.db import transaction
# Pagination
from .pagination import OrderPagination
from django.db.models import Count

# Coupon
from coupon.models import Coupon
from coupon.utils import calculate_discount
from django.utils import timezone
from datetime import timedelta

from django.shortcuts import get_object_or_404
from merchant.models import Merchant

# def calculate_delivery_fee(distance_km: float) -> float:
    # """
    # Returns delivery fee based on distance:
    # - ≤ 2.5 km -> £2.99
    # - > 2.5 km -> £3.99
    # """
    # if distance_km <= 2.5:
        # return Decimal("2.99")
    # return Decimal("3.99")

def calculate_delivery_fee(distance_km: float) -> Decimal:
    """
    Returns delivery fee based on distance:
    - Below 4 km -> £3.50
    - 4 km to 6.5 km -> £4.00
    - Over 6.5 km -> £4.50
    """
    if distance_km < 4:
        return Decimal("3.50")
    elif distance_km < 6.5:
        return Decimal("4.00")
    return Decimal("4.50")


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def create_payment(request):
    """
    Start Mollie payment before creating order.
    - Calculate total from cart
    - Create Mollie payment
    - Store cart in metadata
    - Include platform fee split for OrderGuard
    """
    data = request.data

    # Fixed service fee
    SERVICE_FEE = Decimal("0.75")

    # If deliver, add delivery charge
    # order_type = data.get("order_type")
    order_type = data.get("order_type", "pickup")
    distance_km = 0  # default for pickup

    # Calculate delivery fee
    delivery_charge = 0

    if order_type == "delivery":
        distance_km = float(data.get("distanceKm", 0))  # passed from frontend
        print(distance_km)
        delivery_charge = calculate_delivery_fee(distance_km)

    # Reject orders > 8 km
    if order_type == "delivery" and distance_km > 8:
        return Response(
            {"detail": "Delivery distance > 8 km. Cannot order."},
            status=status.HTTP_400_BAD_REQUEST
    )

    # Calculate cart total
    items = data.get("items", [])
    # cart_total = sum(Decimal(str(item["total"])) for item in items)
    cart_total = Decimal("0.00")

    ## Get User if login
    user = request.user if request.user.is_authenticated else None
    logger.info(f"[CREATE] user: {request.user} | auth={request.user.is_authenticated}")

    for item in items:
        menu_item = MenuItem.objects.get(id=item["item"])
        quantity = int(item.get("quantity", 1))

        # Check if this reward makes the item free
        is_free = False
        reward_id = item.get("rewardId")

        if reward_id and user:
            reward = (
                SpinReward.objects.filter(
                    id=reward_id,
                    user=user,
                    status="redeemed",
                )
                .select_related("reward_config")
                .first()
            )

            if reward and reward.reward_config.free_item_id == menu_item.id:
                is_free = True

        if is_free:
            item_total = Decimal("0.00")
        else:
            item_total = menu_item.price * quantity

        # Add toppings only if the item isn't free
        if not is_free:
            toppings_list = item.get("toppings", [])
            for topping_id in toppings_list:
                topping_obj = MenuItem.objects.get(id=topping_id)
                item_total += topping_obj.price

        cart_total += item_total

    # Coupon code
    coupon_code = data.get("coupon_code")
    discount = Decimal("0.00")
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code, active=True)

            now = timezone.now()
            if not (coupon.valid_from <= now <= coupon.valid_to):
                raise Coupon.DoesNotExist

            discount = calculate_discount(coupon, cart_total)

        except Coupon.DoesNotExist:
            return Response(
                {"detail": "Invalid or expired coupon"},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Add service fee, and delivery charge if deliver
    # total_amount = cart_total + SERVICE_FEE - didscount
    # total_amount = cart_total + SERVICE_FEE + delivery_charge
    total_amount = cart_total + SERVICE_FEE + delivery_charge - discount

    if total_amount <= 0:
        return Response({"detail": "Cart total must be greater than zero"}, status=status.HTTP_400_BAD_REQUEST)

    # Calculate platform fee dynamically (7.5% + £0.75)
    platform_fee_value = (total_amount * Decimal("0.075") + Decimal("0.75")).quantize(Decimal("0.01"))

    # Redirect Url
    REDIRECT_URL = config("MOLLIE_REDIRECT_URL")
    # Webhook Url
    WEBHOOK_URL = config("WEBHOOK_URL")

    merchant = Merchant.objects.get(name="foundry")
    mollie = MollieService(merchant)

    # Decide test/live mode based on merchant
    is_test = merchant.mollie_mode == "test"

    try:
        payment = mollie.create_payment({
            "amount": {
                "currency": "GBP",
                "value": f"{total_amount:.2f}",
            },
            "description": "The Foundry - New order payment",
            "profileId": merchant.mollie_profile_id,
            "redirectUrl": REDIRECT_URL,
            "webhookUrl": WEBHOOK_URL,
            "testmode": is_test,
            "metadata": {
                "items": items,
                "coupon_code": coupon_code,
                "discount": str(discount),
                "user_id": user.id if user else None,
                "customer_name": data.get("customer_name"),
                # "customer_email": data.get("customer_email"),
                # "customer_email": user.email if user else data.get("customer_email"),  # ✅ smarter
                "customer_email": user.email if user and user.email else data.get("customer_email"),
                "phone_number": data.get("phone_number"),
                "order_type": data.get("order_type"),
                "delivery_address": data.get("delivery_address"),
                "service_fee": str(SERVICE_FEE),
                "delivery_charge": str(delivery_charge),
                "mollie_mode": merchant.mollie_mode,
            },
            "applicationFee": {
                "amount": {
                    "value": f"{platform_fee_value:.2f}",
                    "currency": "GBP"
                },
                "description": "OrderGuard platform fee (7.5% + £0.75)"
            },
        })

        logger.info(f"[CREATE] user: {request.user} | auth={request.user.is_authenticated}")

        # payment = mollie_client.payments.get(payment_id, testmode=True)
        metadata = payment.metadata or {}

        order_type = (metadata.get("order_type") or "pickup").lower().strip()

        # ✅ Apply default estimated times here
        if order_type == "pickup":
            estimated_time = 25
        elif order_type == "delivery":
            estimated_time = 40
        else:
            estimated_time = 15

    # ✅ Update order status based on Mollie payment
    # if payment.is_paid():
        # order.status = "new"
    # elif payment.is_canceled():
        # order.status = "cancelled"
    # elif payment.is_expired():
        # order.status = "cancelled"
    # else:
        # order.status = "new"

    # order.total_amount = Decimal(str(payment.amount["value"]))
    # order.save()

    # Websocket
    # channel_layer = get_channel_layer()
    # # .data - means serialized json data
    # order_data = OrderReadSerializer(order).data
    # order_data = decimal_to_float(order_data)

    # async_to_sync(channel_layer.group_send)(
        # "orders",  # your shared group name
        # {
            # "type": "order_update",
            # "order": order_data,
        # }
    # )

    # print(f"📡 WebSocket broadcast sent for Order #{order.id}")
    # # Email notification
    # send_order_email_notification(order, created=True)

    # # Send push notifications to all registered device tokens
    # tokens = DeviceToken.objects.values_list("expo_push_token", flat=True)
    # for token in tokens:
        # send_push_notification(
            # token,
            # title="🧾 KK83 - New Order Received",
            # body=f"Order #{order.id} from {order.customer_name} is now {order.status.upper()}",
            # data={"order_id": order.id, "status": order.status}
        # )

    # print(f"📢 Sent push notification for Order #{order.id} to {len(tokens)} devices")

    # return HttpResponse("OK")
    # except Exception as e:
        # return HttpResponse(str(e), status=400)
    # except Exception as e:
        # import traceback
        # print("🔥 ERROR IN WEBHOOK:", e)
        # traceback.print_exc()
        # return HttpResponse(str(e), status=400)

    except Error as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        {
            "checkout_url": payment.checkout_url,
            "payment_id": payment.id
        },
        status=status.HTTP_200_OK
    )


@csrf_exempt
def mollie_webhook(request):
    """
    PRODUCTION-READY Mollie webhook:
    - Handles test/live mode automatically
    - Idempotent (no duplicate orders)
    - Safe DB transactions
    """

    # -----------------------------
    # 1. Get payment ID (form + JSON)
    # -----------------------------
    payment_id = request.POST.get("id")

    if not payment_id:
        try:
            body = request.body.decode("utf-8")
            if body:
                data = json.loads(body)
                payment_id = data.get("id")
        except Exception as e:
            logger.warning(f"[MOLLIE] JSON decode failed: {e}")
            return HttpResponse("OK")

    if not payment_id:
        logger.error("[MOLLIE] Missing payment ID")
        return HttpResponse("OK")

    logger.info(f"[MOLLIE] Webhook received: {payment_id}")

    # -----------------------------
    # 2. Get merchant (IMPORTANT)
    # -----------------------------
    # You can improve this later (multi-merchant)
    from merchant.models import Merchant
    merchant = Merchant.objects.get(name="foundry")
    logger.info(f"[MOLLIE] Access token prefix: {merchant.oauth_access_token[:6]}")

    # -----------------------------
    # 3. Init client
    # -----------------------------
    # mollie_client = Client()
    # mollie_client.set_access_token(merchant.oauth_access_token)

    # -----------------------------
    # 3. Use MollieService
    # -----------------------------
    mollie = MollieService(merchant)

    # -----------------------------
    # 4. Fetch payment (AUTO MODE DETECTION)
    # -----------------------------
    # test
    # try:
        # try:
            # payment = mollie_client.payments.get(payment_id, testmode=True)
            # is_test = True
        # except:
            # payment = mollie_client.payments.get(payment_id, testmode=False)
            # is_test = False

        # logger.info(f"[MOLLIE] Payment fetched (test={is_test})")

    # except Error as e:
        # logger.error(f"[MOLLIE] Payment fetch failed: {e}")
        # return HttpResponse("OK")

    ## live
    # try:
        # payment = mollie_client.payments.get(payment_id)
        # # 🔍 DEBUG: payment mode from Mollie (LIVE or TEST)
        # logger.info(f"[MOLLIE] Payment mode: {payment.mode}")
        # logger.info(f"[MOLLIE] Payment id: {payment.id}")

        # is_test = payment.mode == "test"

        # logger.info(f"[MOLLIE] Payment fetched successfully (test={is_test})")

    # except Error as e:
        # logger.error(f"[MOLLIE] Payment fetch failed: {e}")
        # return HttpResponse("OK")

    try:
        payment = mollie.get_payment(payment_id)

        logger.info(f"[MOLLIE] Payment mode: {payment.mode}")
        logger.info(f"[MOLLIE] Payment id: {payment.id}")

        is_test = payment.mode == "test"

        logger.info(f"[MOLLIE] Payment fetched successfully (test={is_test})")

    except Error as e:
        logger.error(f"[MOLLIE] Payment fetch failed: {e}")
        return HttpResponse("OK")

    metadata = payment.metadata or {}

    ## Get User
    User = get_user_model()

    customer_email = metadata.get("customer_email")

    user = None
    user_id = metadata.get("user_id")

    if user_id:
        user = User.objects.filter(id=user_id).first()

    if not user:
        customer_email = (metadata.get("customer_email") or "").strip().lower()
        if customer_email:
            user = User.objects.filter(email__iexact=customer_email).first()

    logger.info(f"[MOLLIE] Attached user: {user}")

    logger.info(f"[WEBHOOK] metadata: {metadata}")
    logger.info(f"[WEBHOOK] resolved user: {user}")

    # -----------------------------
    # 5. Process ONLY paid payments
    # -----------------------------
    if not payment.is_paid():
        logger.info(f"[MOLLIE] Payment not paid: {payment.status}")
        return HttpResponse("OK")

    # -----------------------------
    # 6. CREATE ORDER (IDEMPOTENT)
    # -----------------------------
    from order.models import Order, OrderItem, OrderItemTopping, OrderItemComponent
    from collections import Counter

    try:
        with transaction.atomic():

            order, created = Order.objects.get_or_create(
                payment_id=payment.id,
                defaults={
                    "user": user,
                    "customer_name": metadata.get("customer_name", ""),
                    "customer_email": metadata.get("customer_email", ""),
                    "phone_number": metadata.get("phone_number", ""),
                    "order_type": metadata.get("order_type", "pickup"),
                    "merchant": merchant,
                    "delivery_address": metadata.get("delivery_address", ""),
                    "status": "new",
                    "service_fee": Decimal(str(metadata.get("service_fee", 0))),
                    "delivery_charge": Decimal(str(metadata.get("delivery_charge", 0))),
                    "coupon_code": metadata.get("coupon_code"),
                    "discount": Decimal(str(metadata.get("discount", 0))),
                }
            )

            # -----------------------------
            # 7. Prevent duplicate items
            # -----------------------------
            if not created:
                logger.info(f"[MOLLIE] Order already exists: {order.id}")

                # 🔥 FIX: attach user if missing
                if not order.user and user:
                    order.user = user
                    order.save(update_fields=["user"])
                    logger.info(f"[MOLLIE] User attached to existing order: {order.id}")

                return HttpResponse("OK")

            logger.info(f"[MOLLIE] Order created: {order.id}")

            # -----------------------------
            # 8. Convert to User Points
            # -----------------------------
            try:
                if user:  # Only logged-in users earn points

                    total = Decimal(
                        payment.amount.value
                        if hasattr(payment.amount, "value")
                        else payment.amount["value"]
                    )

                    points = int(total)

                    # rewards/services/points_service.py
                    # add_points function
                    user_points = add_points(user, points)

                    logger.info(
                        f"[MOLLIE] Awarded {points} points to user {user.id}. "
                        f"Current points={user_points.points}, "
                        f"spins={user_points.spins_available}"
                    )
                else:
                    logger.info(
                        "[MOLLIE] Guest checkout - no loyalty points awarded."
                    )

            except Exception as e:
                logger.exception(f"[MOLLIE] Failed to award loyalty points: {e}")

            # -----------------------------
            # 8. Create OrderItems
            # -----------------------------
            for item_data in metadata.get("items", []):

                from rewards.models import SpinReward

                is_free = False
                reward = None

                reward_id = item_data.get("rewardId")

                if reward_id and user:
                    reward = SpinReward.objects.filter(
                        id=reward_id,
                        user=user,
                        status="redeemed",
                    ).select_related("reward_config").first()

                    if reward:
                        # Verify that the reward matches the menu item
                        if reward.reward_config.free_item_id == item_data["item"]:
                            is_free = True

                order_item = OrderItem.objects.create(
                    order=order,
                    item_id=item_data["item"],
                    quantity=item_data.get("quantity", 1),
                    note=item_data.get("note", ""),
                    is_free=is_free
                )

                if reward and is_free:
                    reward.status = "consumed"
                    reward.save(update_fields=["status"])

                # Toppings
                toppings_list = item_data.get("toppings", [])
                if toppings_list:
                    topping_counts = Counter(toppings_list)

                    for topping_id, qty in topping_counts.items():
                        OrderItemTopping.objects.create(
                            order_item=order_item,
                            topping_id=int(topping_id),
                            quantity=qty,
                        )

                # Components
                components = item_data.get("components", [])
                for component in components:

                    if isinstance(component, int):
                        component_id = component
                        quantity = 1
                        category = None

                    elif isinstance(component, dict):
                        component_id = component.get("id")
                        quantity = component.get("quantity", 1)
                        category = component.get("category")

                    else:
                        continue

                    OrderItemComponent.objects.create(
                        order_item=order_item,
                        category=category,
                        item_id=component_id,
                        quantity=quantity
                    )

                # reward_id = item_data.get("rewardId")
                # if reward_id and user:
                    # from rewards.models import SpinReward  # replace with your model

                    # SpinReward.objects.filter(
                        # id=reward_id,
                        # user=user,
                        # status="redeemed",
                    # ).update(status="consumed")


    except Exception as e:
        logger.error(f"[MOLLIE] Order creation failed: {e}")
        return HttpResponse("OK")

    # -----------------------------
    # 9. Notifications (AFTER COMMIT)
    # -----------------------------
    try:
        from order.utils import decimal_to_float
        from order.serializers import OrderReadSerializer

        order_data = OrderReadSerializer(order).data
        order_data = decimal_to_float(order_data)

        def send_notifications():
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            # --- WebSocket ---
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "orders",
                    {"type": "order_update", "order": order_data}
                )
                logger.info(f"[MOLLIE] WebSocket sent for order {order.id}")
            except Exception as e:
                logger.warning(f"[MOLLIE] WebSocket failed: {repr(e)}")

            # --- Email ---
            # try:
                # send_order_email_notification(order, created=True)
                # logger.info(f"[MOLLIE] Email sent for order {order.id}")
            # except Exception as e:
                # logger.error(f"[MOLLIE] Email failed for order {order.id}: {repr(e)}")

            # --- SMS ---
            # try:
                # send_order_sms_notification(order, created=True)
                # logger.info(f"[MOLLIE] SMS sent for order {order.id}")
            # except Exception as e:
                # logger.error(f"[MOLLIE] SMS failed for order {order.id}: {repr(e)}")

            # --- Push ---
            try:
                tokens = DeviceToken.objects.values_list("expo_push_token", flat=True)
                for token in tokens:
                    send_push_notification(
                        token,
                        title="🧾 New Order Received",
                        body=f"Order #{order.id} from {order.customer_name} is now {order.status.upper()}",
                        data={"order_id": order.id, "status": order.status}
                    )
                logger.info(f"[MOLLIE] Push sent for order {order.id} to {len(tokens)} devices")
            except Exception as e:
                logger.error(f"[MOLLIE] Push notification failed for order {order.id}: {repr(e)}")

        # ✅ THIS IS THE KEY LINE
        transaction.on_commit(send_notifications)

    except Exception as e:
        logger.warning(f"[MOLLIE] Notification setup failed: {e}")

    # -----------------------------
    # 10. DONE
    # -----------------------------
    return HttpResponse("OK")


@api_view(["GET"])
@csrf_exempt
def check_payment(request, payment_id):

    mollie_client = Client()
    mollie_client.set_api_key(settings.MOLLIE_API_KEY)

    try:
        # Get payment from Mollie
        payment = mollie_client.payments.get(payment_id)

        # Try to find matching order by payment_id
        order = Order.objects.filter(payment_id=payment_id).first()

        # Update order status if found
        if order:
            if payment.is_paid():
                order.status = "completed"
            elif payment.is_canceled() or payment.is_expired():
                order.status = "cancelled"
            else:
                order.status = "new"
            order.save()

        # Use serializer
        serializer = PaymentStatusSerializer({
            "payment_id": payment.id,
            "status": payment.status,
            "amount": payment.amount,
            "paid": payment.is_paid(),
            "order_id": order.id if order else None,
            "tracking_token": str(order.tracking_token) if order else None,
        })

        return Response(serializer.data, status=status.HTTP_200_OK)

        # return JsonResponse({
            # "payment_id": payment.id,
            # "status": payment.status,   # "paid", "open", "failed"
            # "amount": payment.amount,
            # "paid": payment.is_paid(),
            # "order_id": order.id if order else None,
        # })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# class OrderStatusSummaryView(APIView):
    # def get(self, request):
        # data = (
            # Order.objects
            # .values('status')
            # .annotate(total=Count('id'))
        # )

        # # convert to dict: { pending: 5, preparing: 2 }
        # summary = {item['status']: item['total'] for item in data}

        # return Response(summary)


class OrderStatusSummaryView(APIView):
    def get(self, request):
        now = timezone.localtime()

        if now.hour < 1:
            start_date = (now - timedelta(days=1)).replace(
                hour=1, minute=0, second=0, microsecond=0
            )
        else:
            start_date = now.replace(
                hour=1, minute=0, second=0, microsecond=0
            )

        data = (
            Order.objects
            .filter(created_at__gte=start_date)
            .values('status')
            .annotate(total=Count('id'))
        )

        summary = {
            item['status']: item['total']
            for item in data
        }

        return Response(summary)


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing customer orders.

    • Supports guest checkout (unauthenticated users can create orders).
    • Creates Mollie payments and returns checkout URL.
    • Allows filtering by status.
    • Updates order status via PATCH.
    """

    queryset = Order.objects.all().order_by('-created_at')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    pagination_class = OrderPagination

    # def get_queryset(self):
        # """
        # Show all query
        # """
        # queryset = super().get_queryset()
        # return queryset

    def get_queryset(self):
        """
        Show today order only
        """
        queryset = super().get_queryset()

        now = timezone.localtime()

        # Reset at 1:00 AM
        if now.hour < 1:
            # Before 1 AM, still show yesterday's business day
            start_date = (now - timedelta(days=1)).replace(
                hour=1, minute=0, second=0, microsecond=0
            )
        else:
            # After 1 AM, start today's business day
            start_date = now.replace(
                hour=1, minute=0, second=0, microsecond=0
            )

        return queryset.filter(created_at__gte=start_date)

    def get_permissions(self):
        """Allow any user to create an order (guest checkout)."""
        return [AllowAny()]

    def get_serializer_class(self):
        """Use create serializer for POST, read serializer for other actions."""
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderReadSerializer

    def get_serializer_context(self):
        """Pass request into serializer context (e.g. for user binding)."""
        return {'request': self.request}

    def perform_create(self, serializer):
        """Save order with authenticated user if available, else None."""
        # restaurant = serializer.validated_data["restaurant"]

        # If restaurant is closed or open
        # if not restaurant.is_open:
            # raise ValidationError("Restaurant is currently closed. Orders and preorders are not allowed")

        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)

    def create(self, request, *args, **kwargs):
        """
        Handle new order creation:
        - Save order
        - Create Mollie payment
        - Return order details + Mollie checkout URL
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save order first
        order = serializer.save(user=request.user if request.user.is_authenticated else None)
        total_amount = order.get_total_amount()

        mollie_client = Client()
        mollie_client.set_api_key(settings.MOLLIE_API_KEY)

        redirect_url = f"http://localhost:3000/payment/return?order_id={order.id}"

        try:
            payment = mollie_client.payments.create({
                "amount": {
                    "currency": "GBP",
                    "value": f"{total_amount:.2f}"  # string, two decimals
                },
                "description": f"Order #{order.id}",
                "redirectUrl": redirect_url,
                "webhookUrl": "https://0fc953cc9e42.ngrok-free.app/api/order/mollie/webhook/",
                "metadata": {
                    "order_id": order.id
                },
                # "applicationFee": {
                        # "amount": {"currency": "GBP", "value": "1.50"}, # service + commission
                        # "description": "OrderGuard platform fee",
                # }
            })

            headers = self.get_success_headers(serializer.data)
            return Response({
                "order": OrderReadSerializer(order).data,
                "payment_id": payment.id,
                "checkout_url": payment.checkout_url,
                # "checkout_url": payment.get("checkoutUrl"),  # Frontend redirects here
                "amount": total_amount,
                "currency": "GBP",
            }, status=status.HTTP_201_CREATED, headers=headers)

        except Exception as e:
            raise ValidationError({"detail": str(e)})

    def partial_update(self, request, *args, **kwargs):
        """
        Allow partial update of an order, primarily to update `status`.
        Expected payload: { "status": "preparing" }
        """
        order = self.get_object()
        old_status = order.status
        new_status = request.data.get('status')

        if not new_status:
            return Response(
                {'error': 'Status field is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status
        order.save()

        # 🔔 Notify ONLY when status becomes "preparing"
        if old_status != new_status and new_status == "preparing":

            def send_notifications():
                try:
                    send_order_email_notification(order, status="preparing")
                except Exception as e:
                    logger.error(f"Email failed for order {order.id}: {e}")

                try:
                    send_order_sms_notification(order, status="preparing")
                except Exception as e:
                    logger.error(f"SMS failed for order {order.id}: {e}")

            transaction.on_commit(send_notifications)

        serializer = self.get_serializer(order)
        return Response(serializer.data)


    @action(detail=True, methods=["get", "post"])
    def adjust_time(self, request, pk=None):
        """
        Adjust estimated_time by + or - minutes.
        Example body: { "minutes": 5 } or { "minutes": -5 }
        """
        order = self.get_object()
        minutes = request.data.get("minutes", 0)

        try:
            minutes = int(minutes)
        except (TypeError, ValueError):
            return Response({"error": "Invalid minutes"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Prevent negative total time
        new_time = max(0, order.estimated_time + minutes)
        order.estimated_time = new_time
        order.save()

        return Response(
            {"id": order.id, "new_estimated_time": new_time},
            status=status.HTTP_200_OK,
        )


@api_view(["GET"])
def track_order(request, token):
    order = get_object_or_404(Order, tracking_token=token)
    serializer = OrderTrackingSerializer(order)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_orders(request):
    orders = Order.objects.filter(user=request.user) \
        .prefetch_related(
            "items__order_toppings__topping",
            "items__order_components__item",
        ) \
        .order_by("-created_at")

    serializer = OrderHistorySerializer(orders, many=True)
    return Response(serializer.data)

