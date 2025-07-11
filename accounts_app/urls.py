from django.urls import path
from . import views
from payments_app.views import BillingView


TEMPLATE_URLS = [
    # path('resend_email_verification/', views.ResendEmailVerificationView.as_view(), name='resend_email_verification'), # not in use as of now
    # path('create_profile/', views.CreateProfileView.as_view(), name='create_profile'), # not in use since ww are using the regular profile page to handle both cases
    path("update_address/", views.UpdateAddressView.as_view(), name="update_address"),
    path("profile/", views.ProfileView.as_view(), name="profile"),  # main profile page
    path("update_general_profile/", views.UpdateGeneralProfileView.as_view(), name="update_general_profile"),
    path("edit_shadchan_faq/<uuid:pk>/", views.EditShadchanFaqView.as_view(), name="edit_shadchan_faq"),
    path(
        "update_profile_identification/", views.UpdateIdentificationView.as_view(), name="update_profile_identification"
    ),
    path("download_resume/<uuid:profile_id>/", views.download_resume, name="download_resume"),
    path("shadchan_contact_requests", views.ShadchanContactRequestsView.as_view(), name="shadchan_contact_requests"),
    path("billing/", BillingView.as_view(), name="customer_billing"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
    path("notifications/", views.NotificationsView.as_view(), name="notifications"),
    # admin urls
    path(
        "unverified_shadchan_profiles/",
        views.UnverifiedShadchanProfilesView.as_view(),
        name="unverified_shadchan_profiles",
    ),
]


urlpatterns = TEMPLATE_URLS
