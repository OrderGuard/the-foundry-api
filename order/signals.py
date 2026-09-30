# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.conf import settings
# from django.core.mail import send_mail
# from .models import Order
# from decouple import config


# @receiver(post_save, sender=Order)
# def send_order_email_notification(sender, instance, created, **kwargs):

    # # No email → nothing to do
    # if not instance.customer_email:
        # return

    # # Send only on creation OR status change
    # if not created and not getattr(instance, "_status_changed", False):
        # return

    # SUBJECTS = {
        # "new": " 🧾 Order Received",
        # "accepted": "✅ Order Accepted",
        # "preparing": "🍳 Order Preparing",
        # "ready": "🍽️ Order Ready",
        # "delivering": "🚚 Order On The Way",
        # "completed": "🎉 Order Completed",
        # "cancelled": "❌ Order Cancelled",
    # }

    # subject = SUBJECTS.get(instance.status)
    # if not subject:
        # return

    # FRONTEND_URL = config("FRONTEND_URL")

    # tracking_url = f"{FRONTEND_URL}/track/{instance.tracking_token}"

    # if created:
        # status_text = "We’ve received your order 🎉"
    # else:
        # status_text = f"Your order is now **{instance.status.upper()}**"

    # message = f"""
# Hi {instance.customer_name or "there"},

# {status_text}

# Order #{instance.id}
# Order type: {instance.order_type.title()}
# Estimated time: {instance.estimated_time} minutes
# Total: £{instance.get_total_amount()}

# Track your order here:
# {tracking_url}

# Thank you for ordering with Klub Kitchen 83 🍕
# """
    # send_mail(
        # subject=subject,
        # message=message,
        # from_email=None,
        # recipient_list=[instance.customer_email],
        # fail_silently=False,
    # )
