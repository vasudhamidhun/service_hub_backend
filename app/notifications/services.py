
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

from .models import Notification


logger = logging.getLogger(__name__)


def create_notification(
    recipient,
    title,
    message,
    notification_type,
    complaint=None,
    service_request=None
):

    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        complaint=complaint,
        service_request=service_request
    )

    notification_data = {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "notification_type": notification.notification_type,
        "service_request": notification.service_request_id,
        "complaint": notification.complaint_id,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat(),
    }

    def send_realtime_notification():

        try:
            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                f"notifications_{recipient.id}",
                {
                    "type": "notification.message",
                    "notification": notification_data,
                }
            )

        except Exception:
            logger.exception(
                "Failed to send real-time notification. "
                "Notification ID: %s",
                notification.id
            )

    transaction.on_commit(send_realtime_notification)

    return notification
