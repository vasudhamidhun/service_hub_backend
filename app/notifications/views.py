
import logging

from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Notification
from .serializers import NotificationSerializer


logger = logging.getLogger("app")


class NotificationListView(generics.ListAPIView):

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        user = self.request.user

        logger.info(
            "User %s requested notification list.",
            user.id
        )

        queryset = Notification.objects.filter(
            recipient=user
        ).order_by("-created_at")

        logger.info(
            "Retrieved %s notifications for user %s.",
            queryset.count(),
            user.id
        )

        return queryset


class UnreadNotificationCountView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        logger.info(
            "User %s requested unread notification count.",
            request.user.id
        )

        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        logger.info(
            "User %s has %s unread notifications.",
            request.user.id,
            count
        )

        return Response({
            "unread_count": count
        })


class MarkNotificationReadView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):

        logger.info(
            "User %s requested to mark notification %s as read.",
            request.user.id,
            pk
        )

        notification = get_object_or_404(
            Notification,
            id=pk,
            recipient=request.user
        )

        if notification.is_read:

            logger.info(
                "Notification %s is already read by user %s.",
                pk,
                request.user.id
            )

        else:

            notification.is_read = True

            notification.save(update_fields=["is_read"])

            logger.info(
                "Notification %s successfully marked as read by user %s.",
                pk,
                request.user.id
            )

        return Response({
            "message": "Notification marked as read.",
            "is_read": notification.is_read
        })
