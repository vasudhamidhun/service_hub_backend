
import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token):
    validated_token = AccessToken(token)
    return JWTAuthentication().get_user(validated_token)


class JWTAuthMiddleware:

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):

        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)

        token = query_params.get("token", [None])[0]

        scope["user"] = AnonymousUser()

        if not token:
            logger.warning("WebSocket connection rejected: JWT token missing")

        else:
            try:
                user = await get_user_from_token(token)
                scope["user"] = user

                logger.info(
                    "WebSocket JWT authentication successful. User ID: %s",
                    user.id
                )

            except Exception as exc:
                logger.exception(
                    "WebSocket JWT authentication failed. Error: %s",
                    type(exc).__name__
                )

        return await self.inner(scope, receive, send)
