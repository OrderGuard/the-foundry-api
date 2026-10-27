# menu/tasks.py

import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.utils import timezone

from .models import Menu
from notifications.models import DeviceToken
from notifications.utils import send_push_notification

logger = logging.getLogger(__name__)


def send_menu_opening_reminder(menu):
    """
    Send an Expo push notification to registered devices.

    TODO: Filter DeviceToken by the restaurant owner
    or merchant once the ownership relationship is known.
    """

    tokens = DeviceToken.objects.values_list(
        "expo_push_token",
        flat=True,
    ).distinct()

    for token in tokens:
        try:
            send_push_notification(
                token=token,
                title="Restaurant Opening Reminder",
                body=(
                    f"{menu.name} is scheduled to open. "
                    "Please open your store."
                ),
                data={
                    "type": "OPEN_RESTAURANT",
                    "menu_id": menu.id,
                    "menu_name": menu.name,
                },
            )

        except Exception:
            logger.exception(
                "Failed to send opening reminder for menu %s",
                menu.id,
            )


@shared_task
def manage_menu_schedules():
    now = timezone.localtime()
    current_tz = timezone.get_current_timezone()

    for menu in Menu.objects.all():

        # Build today's opening and closing datetimes.
        opening_dt = timezone.make_aware(
            datetime.combine(now.date(), menu.start_time),
            current_tz,
        )

        closing_dt = timezone.make_aware(
            datetime.combine(now.date(), menu.end_time),
            current_tz,
        )

        # ----------------------------------
        # 1. AUTOMATIC CLOSE
        # ----------------------------------
        if now >= closing_dt:
            if menu.is_open:
                menu.is_open = False
                menu.save(update_fields=["is_open"])

                logger.info(
                    "Menu %s automatically closed",
                    menu.id,
                )

            continue

        # ----------------------------------
        # 2. BEFORE OPENING REMINDER WINDOW
        # ----------------------------------
        reminder_start = opening_dt - timedelta(minutes=1)

        if now < reminder_start:
            continue

        # ----------------------------------
        # 3. AUTOMATICALLY OPEN AT START TIME
        # ----------------------------------
        if now >= opening_dt and not menu.is_open:
            menu.is_open = True
            menu.save(update_fields=["is_open"])

            logger.info(
                "Menu %s automatically opened",
                menu.id,
            )

        # ----------------------------------
        # 4. STOP REMINDERS WHEN OPEN
        # ----------------------------------
        if menu.is_open:
            continue

        # ----------------------------------
        # 5. SEND OPENING REMINDER
        # ----------------------------------
        last_reminder = menu.last_open_reminder_at

        if last_reminder is not None:
            elapsed = (
                now - timezone.localtime(last_reminder)
            ).total_seconds()

            if elapsed < 60:
                continue

        send_menu_opening_reminder(menu)

        menu.last_open_reminder_at = now
        menu.save(update_fields=["last_open_reminder_at"])

        logger.info(
            "Opening reminder sent for menu %s",
            menu.id,
        )


@shared_task
def update_menu_status():
    for menu in Menu.objects.all():
        should_be_open = (
            menu.is_within_schedule
            and not menu.is_temporarily_closed
        )

        if menu.is_open != should_be_open:
            menu.is_open = should_be_open
            menu.save(update_fields=["is_open"])

