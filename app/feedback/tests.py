
from django.urls import reverse
from rest_framework.test import APITestCase

from app.accounts.models import User, ProviderProfile
from app.services.models import ServiceRequest
from app.feedback.models import Review


class ReviewAPITestCase(APITestCase):

    def setUp(self):

        # 1. Create customer
        self.customer = User.objects.create_user(
            username="customer1",
            email="customer1@test.com",
            password="testpass123",
            full_name="Test Customer",
            role="customer"
        )

        # 2. Create another customer
        self.other_customer = User.objects.create_user(
            username="customer2",
            email="customer2@test.com",
            password="testpass123",
            full_name="Other Customer",
            role="customer"
        )

        # 3. Create provider user
        self.provider_user = User.objects.create_user(
            username="provider1",
            email="provider1@test.com",
            password="testpass123",
            full_name="Test Provider",
            role="provider"
        )

        # 4. Create provider profile
        self.provider = ProviderProfile.objects.create(
            user=self.provider_user,
            service_category="Electrician",
            experience_years=5,
            verification_status="approved"
        )

        # 5. Create completed service request
        self.service_request = ServiceRequest.objects.create(
            customer=self.customer,
            provider=self.provider,
            problem_description="Electrical wiring problem",
            service_location="Thrissur",
            status="completed"
        )

        # 6. Create pending service request
        self.pending_request = ServiceRequest.objects.create(
            customer=self.customer,
            provider=self.provider,
            problem_description="Fan repair",
            service_location="Thrissur",
            status="pending"
        )

        # 7. Create another customer's completed request
        self.other_request = ServiceRequest.objects.create(
            customer=self.other_customer,
            provider=self.provider,
            problem_description="Switch repair",
            service_location="Thrissur",
            status="completed"
        )

        # 8. Authenticate as customer by default
        self.client.force_authenticate(user=self.customer)

        # 9. Review API URL
        self.review_url = reverse("create-review")

    # --------------------------------------------------
    # TEST 1: Customer can submit a review
    # --------------------------------------------------

    def test_customer_can_submit_review(self):

        data = {
            "service_request": self.service_request.id,
            "rating": 5,
            "comment": "Excellent service!"
        }

        response = self.client.post(
            self.review_url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Review.objects.count(), 1)

        review = Review.objects.first()

        self.assertEqual(review.customer, self.customer)
        self.assertEqual(review.provider, self.provider)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Excellent service!")

    # --------------------------------------------------
    # TEST 2: Rating must be between 1 and 5
    # --------------------------------------------------

    def test_invalid_rating_rejected(self):

        for rating in [0, 6]:

            data = {
                "service_request": self.service_request.id,
                "rating": rating,
                "comment": "Testing invalid rating"
            }

            response = self.client.post(
                self.review_url,
                data,
                format="json"
            )

            self.assertEqual(response.status_code, 400)

        self.assertEqual(Review.objects.count(), 0)

    # --------------------------------------------------
    # TEST 3: Customer cannot review another customer's booking
    # --------------------------------------------------

    def test_customer_cannot_review_other_customer_request(self):

        data = {
            "service_request": self.other_request.id,
            "rating": 4,
            "comment": "Good service"
        }

        response = self.client.post(
            self.review_url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Review.objects.count(), 0)

    # --------------------------------------------------
    # TEST 4: Customer cannot review pending booking
    # --------------------------------------------------

    def test_customer_cannot_review_pending_request(self):

        data = {
            "service_request": self.pending_request.id,
            "rating": 5,
            "comment": "Good service"
        }

        response = self.client.post(
            self.review_url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Review.objects.count(), 0)

    # --------------------------------------------------
    # TEST 5: Duplicate review is not allowed
    # --------------------------------------------------

    def test_duplicate_review_rejected(self):

        Review.objects.create(
            customer=self.customer,
            provider=self.provider,
            service_request=self.service_request,
            rating=5,
            comment="First review"
        )

        data = {
            "service_request": self.service_request.id,
            "rating": 4,
            "comment": "Second review"
        }

        response = self.client.post(
            self.review_url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Review.objects.count(), 1)

    # --------------------------------------------------
    # TEST 6: Customer can view their own reviews
    # --------------------------------------------------

    def test_customer_can_view_my_reviews(self):

        Review.objects.create(
            customer=self.customer,
            provider=self.provider,
            service_request=self.service_request,
            rating=5,
            comment="Excellent!"
        )

        url = reverse("my-reviews")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    # --------------------------------------------------
    # TEST 7: Provider reviews can be viewed publicly
    # --------------------------------------------------

    def test_provider_reviews_list(self):

        Review.objects.create(
            customer=self.customer,
            provider=self.provider,
            service_request=self.service_request,
            rating=5,
            comment="Excellent!"
        )

        # Public endpoint: remove authentication
        self.client.force_authenticate(user=None)

        url = reverse(
            "provider-reviews",
            kwargs={"provider_id": self.provider.id}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    # --------------------------------------------------
    # TEST 8: Provider cannot submit a review
    # --------------------------------------------------

    def test_provider_cannot_submit_review(self):

        self.client.force_authenticate(user=self.provider_user)

        data = {
            "service_request": self.service_request.id,
            "rating": 5,
            "comment": "Excellent service!"
        }

        response = self.client.post(
            self.review_url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Review.objects.count(), 0)

    # --------------------------------------------------
    # TEST 9: Unauthenticated user cannot submit a review
    # --------------------------------------------------

    def test_unauthenticated_user_cannot_submit_review(self):

        self.client.force_authenticate(user=None)

        data = {
            "service_request": self.service_request.id,
            "rating": 5,
            "comment": "Excellent service!"
        }

        response = self.client.post(
            self.review_url,
            data,
            format="json"
        )

        self.assertIn(response.status_code, [401, 403])
        self.assertEqual(Review.objects.count(), 0)
