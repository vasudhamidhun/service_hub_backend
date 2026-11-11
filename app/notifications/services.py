from .models import Notification


def create_notification(
    recipient,
    title,
    message,
    notification_type,
    complaint=None,
    service_request=None
):

    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        complaint=complaint,
        service_request=service_request
    )