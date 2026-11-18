
from django.urls import path

from .views import (
    CreateReviewView,
    MyReviewsView,
    ProviderReviewsView,
    UpdateReviewView,
    MyProviderReviewsView,
    CreateComplaintView,
    AdminComplaintListView,
    MyComplaintsView,
    ComplaintDetailView,
    ProviderComplaintResponseView,
    MyProviderComplaintsView,
    ProviderComplaintResponseView,
    AdminComplaintDetailView,
    AdminProviderActionView,
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
    path(
    "my-provider-reviews/",
    MyProviderReviewsView.as_view(),
    name="my-provider-reviews"
),

# -----------------------------complaint

    path(
        "complaints/create/",
        CreateComplaintView.as_view(),
        name="create-complaint"
    ),

    path(
        "admin/complaints/",
        AdminComplaintListView.as_view(),
        name="admin-complaints"
    ),
    path(
        "complaints/my/",
        MyComplaintsView.as_view(),
        name="my-complaints"
    ),

    path(
        "complaints/<int:pk>/",
        ComplaintDetailView.as_view(),
        name="complaint-detail"
    ),
    

    path(
        "provider/complaints/<int:pk>/respond/",
        ProviderComplaintResponseView.as_view(),
        name="provider-complaint-response"
    ),
    path(
    "provider/complaints/",
    MyProviderComplaintsView.as_view(),
    name="provider-complaints"
    ),

   
    # Admin Complaint Management

    path(
        "admin/complaints/<int:pk>/",
        AdminComplaintDetailView.as_view(),
        name="admin-complaint-detail"
    ),

    path(
        "admin/provider-actions/",
        AdminProviderActionView.as_view(),
        name="admin-provider-action"
    ),

]
