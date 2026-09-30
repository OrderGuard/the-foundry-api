# newsletter/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import NewsletterSubscriber
from .serializers import NewsletterSerializer
from django.core.mail import send_mail
from django.conf import settings

@api_view(['POST'])
def subscribe(request):
    serializer = NewsletterSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data['email']

        subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)

        if not created:
            return Response({"message": "Already subscribed"})

        # Send email
        send_mail(
            "Welcome 🎉",
            "Thanks for subscribing!",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=True,
        )

        return Response({"message": "Subscribed successfully!"})

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

