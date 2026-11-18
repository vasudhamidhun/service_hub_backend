
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from .models import Notification


User = get_user_model()


class NotificationAPITestCase(APITestCase):

    def setUp(self):

        self.user1 = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="testpassword123",
            full_name="Admin One",
            role="admin"
        )

        self.user2 = User.objects.create_user(
            username="admin2",
            email="admin2@example.com",
            password="testpassword123",
            full_name="Admin Two",
            role="admin"
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

        # Create notifications for user 1
        self.notification1 = Notification.objects.create(
            recipient=self.user1,
            title="New Complaint",
            message="A new complaint has been submitted.",
            notification_type="complaint",
            is_read=False
        )

        self.notification2 = Notification.objects.create(
            recipient=self.user1,
            title="Complaint Updated",
            message="Complaint status has been updated.",
            notification_type="complaint",
            is_read=True
        )

        # Create notification for user 2
        self.notification3 = Notification.objects.create(
            recipient=self.user2,
            title="Provider Registered",
            message="A new provider has registered.",
            notification_type="provider",
            is_read=False
        )

        # Set explicit timestamps for ordering test
        Notification.objects.filter(
            id=self.notification1.id
        ).update(
            created_at=timezone.now() - timedelta(hours=2)
        )

        Notification.objects.filter(
            id=self.notification2.id
        ).update(
            created_at=timezone.now()
        )

        # API URLs - adjust if your urls.py uses different paths
        self.list_url = "/api/notifications/"
        self.unread_count_url = "/api/notifications/unread-count/"

    # -----------------------------------
    # 1. Notification List Tests
    # -----------------------------------

    def test_notification_list_returns_200(self):

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_user_only_sees_own_notifications(self):

        response = self.client.get(self.list_url)

        self.assertEqual(len(response.data), 2)

        notification_ids = [
            item["id"] for item in response.data
        ]

        self.assertIn(self.notification1.id, notification_ids)
        self.assertIn(self.notification2.id, notification_ids)

        self.assertNotIn(self.notification3.id, notification_ids)

    def test_notifications_are_ordered_newest_first(self):

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.data[0]["id"],
            self.notification2.id
        )

        self.assertEqual(
            response.data[1]["id"],
            self.notification1.id
        )

    # -----------------------------------
    # 2. Unread Notification Count Tests
    # -----------------------------------

    def test_unread_notification_count(self):

        response = self.client.get(self.unread_count_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["unread_count"],
            1
        )

    def test_unread_count_does_not_include_other_users(self):

        response = self.client.get(self.unread_count_url)

        # User 2 has an unread notification,
        # but it must not be included.
        self.assertEqual(
            response.data["unread_count"],
            1
        )

    # -----------------------------------
    # 3. Mark Notification as Read Tests
    # -----------------------------------

    def test_mark_notification_as_read(self):

        url = f"/api/notifications/{self.notification1.id}/mark-read/"

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertTrue(response.data["is_read"])

        self.notification1.refresh_from_db()

        self.assertTrue(self.notification1.is_read)

    def test_mark_read_notification_again(self):

        url = f"/api/notifications/{self.notification2.id}/mark-read/"

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertTrue(response.data["is_read"])

    def test_user_cannot_mark_other_users_notification(self):

        url = f"/api/notifications/{self.notification3.id}/mark-read/"

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

        self.notification3.refresh_from_db()

        self.assertFalse(self.notification3.is_read)

    # -----------------------------------
    # 4. Authentication Tests
    # -----------------------------------

    def test_unauthenticated_user_cannot_access_notifications(self):

        self.client.force_authenticate(user=None)

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_unauthenticated_user_cannot_check_unread_count(self):

        self.client.force_authenticate(user=None)

        response = self.client.get(self.unread_count_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_unauthenticated_user_cannot_mark_notification_read(self):

        self.client.force_authenticate(user=None)

        url = f"/api/notifications/{self.notification1.id}/mark-read/"

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
