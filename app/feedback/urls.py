
from django.urls import path

from .views import (
    CreateReviewView,
    MyReviewsView,
    ProviderReviewsView,
    UpdateReviewView,
)

urlpatterns = [

   
    path(
        "reviews/",
        CreateReviewView.as_view(),
        name="create-review"
    ),

    path(
        "my-reviews/",
        MyReviewsView.as_view(),
        name="my-reviews"
    ),

    # Provider Reviews
    path(
        "providers/<int:provider_id>/reviews/",
        ProviderReviewsView.as_view(),
        name="provider-reviews"
    ),

    # Update Review
    path(
        "reviews/<int:pk>/",
        UpdateReviewView.as_view(),
        name="update-review"
    ),

]
