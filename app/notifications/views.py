
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).order_by("-created_at")


class UnreadNotificationCountView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        return Response({
            "unread_count": count
        })


class MarkNotificationReadView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):

        notification = get_object_or_404(
            Notification,
            id=pk,
            recipient=request.user
        )

        notification.is_read = True
        notification.save(update_fields=["is_read"])

        return Response({
            "message": "Notification marked as read.",
            "is_read": notification.is_read
        })
