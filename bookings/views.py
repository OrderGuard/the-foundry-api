from rest_framework import viewsets
from .models import Booking
from .serializers import BookingSerializer

from notifications.models import DeviceToken
from notifications.utils import send_push_notification

from .utils import send_booking_status_email

class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing booking instances.
    """
    queryset = Booking.objects.all().order_by("-created_at")
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        booking = serializer.save()

        # Send push notifications to all registered device tokens
        tokens = DeviceToken.objects.values_list("expo_push_token", flat=True)

        for token in tokens:
            send_push_notification(
                token,
                title="📅 New Booking Received",
                body=f"Booking from {booking.name} for {booking.people} people at {booking.time}",
                data={
                    "booking_id": booking.id,
                    "name": booking.name,
                    "time": str(booking.time),
                    "people": booking.people
                }
            )

        print(f"📢 Sent push notification for Booking #{booking.id} to {len(tokens)} devices")

    def perform_update(self, serializer):
        old_booking = self.get_object()
        booking = serializer.save()

        # Check if status changed
        if old_booking.status != booking.status:
            send_booking_status_email(booking)

            print(f"📧 Email sent to {booking.email} for status {booking.status}")

