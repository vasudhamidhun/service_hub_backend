
import os
import asyncio
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from channels.layers import get_channel_layer


async def test_channels():
    channel_layer = get_channel_layer()

    print("Testing group_add...")

    await channel_layer.group_add(
        "test_notifications",
        "test_channel"
    )

    print("Group add successful")

    print("Testing group_send...")

    await channel_layer.group_send(
        "test_notifications",
        {
            "type": "notification.message",
            "notification": {
                "id": 1,
                "title": "Test Notification",
                "message": "Testing Channels Redis",
                "notification_type": "new_request"
            }
        }
    )

    print("Group send successful")

    print("Testing receive...")

    event = await channel_layer.receive("test_channel")

    print("Received event:", event)

    await channel_layer.group_discard(
        "test_notifications",
        "test_channel"
    )

    print("All Channels Redis tests passed")


asyncio.run(test_channels())
