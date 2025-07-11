from django.urls import path
from . import views
from . import webhooks

urlpatterns = [
    # bounty payments
    path("add_bounty/<uuid:to_user_id>", views.AddBounty.as_view(), name="add_bounty_to_user"),
    path("add_bounty/", views.AddBounty.as_view(), name="add_bounty"),
    path(
        "bounty_payment_complete/<uuid:order_id>", views.BountyPaymentComplete.as_view(), name="bounty_payment_complete"
    ),
    path(
        "bounty_payment_canceled/<uuid:order_id>", views.BountyPaymentCanceled.as_view(), name="bounty_payment_canceled"
    ),
    path("create_customer_portal/", views.CreateStipeCustomerPortal.as_view(), name="create_customer_portal"),
    path(
        "admin_view_all_paid_invoices/", views.ADMIN_ViewAllPaidInvoices.as_view(), name="admin_view_all_paid_invoices"
    ),
    path("stripe_webhooks/", webhooks.stripe_webhook, name="stripe_webhook"),
    # management
    path("subscriptions/", views.Subscriptions.as_view(), name="subscriptions"),
    path(
        "cancel__bounty_subscription/<uuid:bounty_id>",
        views.CancelBountySubscription.as_view(),
        name="cancel_bounty_subscription",
    ),
    path(
        "cancel__donation_subscription/<uuid:donation_id>",
        views.CancelDonationSubscription.as_view(),
        name="cancel_donation_subscription",
    ),
    path(
        "partner_with_us/<uuid:donation_id>/",
        views.PartnerWithUsPage.as_view(),
        name="partner_with_us",
    ),
    path(
        "partner_with_us/",
        views.PartnerWithUsPage.as_view(),
        name="partner_with_us",
    ),
]
