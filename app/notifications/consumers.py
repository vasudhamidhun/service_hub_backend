
import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        user = self.scope.get("user")

        logger.info("NotificationConsumer connect called")

        if not user or not user.is_authenticated:
            logger.warning("WebSocket rejected: unauthenticated user")
            await self.close()
            return

        self.group_name = f"notifications_{user.id}"

        try:
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            logger.info(
                "User %s joined notification group %s",
                user.id,
                self.group_name
            )

            await self.accept()

            logger.info("WebSocket connection accepted for user %s", user.id)

        except Exception:
            logger.exception("Error while connecting notification consumer")
            await self.close()

    async def disconnect(self, close_code):
        logger.info("WebSocket disconnected. Close code: %s", close_code)

        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def notification_message(self, event):
        await self.send_json(event["notification"])
