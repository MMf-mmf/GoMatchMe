import uuid
import logging
from utils.abstract_models import TimeStampedModel
from django.db import models
from accounts_app.models import CustomUser
import stripe
from django.conf import settings
from decimal import Decimal
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger("project")


class BountyOrder(TimeStampedModel):
    ACTIVE = 0
    PAID_IN_FULL = 1
    CANCELLED_BY_USER = 2
    CANCELLED_BY_ADMIN = 3
    ON_HOLD_PAYMENT_FAILED = 4
    ON_HOLD_BY_ADMIN = 5
    PAID_IN_FULL_OVER_TIME_NO_ENGAGEMENT = 5

    BOUNTY_STATUS_CHOICES = [
        (ACTIVE, "Active"),
        (PAID_IN_FULL, "Paid In Full"),
        (CANCELLED_BY_USER, "Cancelled By User"),
        (CANCELLED_BY_ADMIN, "Cancelled By Admin"),
        (ON_HOLD_PAYMENT_FAILED, "On Hold, Payment Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The user that the bounty is being added from, he is paying for the bounty",
    )
    to_user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bounty_orders",
        help_text="The user that bounty is being added to",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    email = models.EmailField(null=False, blank=False)
    address = models.CharField(max_length=255, null=True, blank=True)
    zip = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)

    paid = models.BooleanField(default=False)
    paid_in_full = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    was_pledge_added = models.BooleanField(
        default=False,
        help_text="was the pledge added to the to_users bounty, this can change from true to false if the subscription is cancelled",
        # help_text="was the initial pledge added to the to_users bounty,  since the whole sum is not charged at once we can only want to update the bounty after successful payment however only the first time the first of many by yearly charges will be charged",
    )
    amount_paid_so_far = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=(
            "this is the amount of the pledge that has been paid so far, "
            "this will be incremented every time a pledge fee is charged "
            "and should be paid in full when the match takes place"
        ),
    )
    stripe_payment_intent = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The stripe payment intent id that is returned in the webhook when a payment is successful",
    )
    stripe_subscription_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The stripe subscription id that is returned in the webhook when a payment is successful",
    )
    stripe_checkout_session_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="when payment is the first of a subscription, the first payment id is returned in the webhook and saved here",
    )
    stripe_invoice_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The stripe invoice id that is returned in the webhook when a payment is successful",
    )
    refund_date = models.DateTimeField(null=True, blank=True)
    recurring_payment = models.BooleanField(default=False, null=True, blank=True)
    number_of_months = models.PositiveIntegerField(
        null=True, blank=True, help_text="The number of months the user wants to pay this amount consecutively"
    )
    recurring_payment_expiration_date = models.DateField(null=True, blank=True)
    is_subscription_active = models.BooleanField(default=False, null=True, blank=True)
    bounty_status = models.IntegerField(choices=BOUNTY_STATUS_CHOICES, default=0)

    def update_failed_payment_status(self):
        """
        Update the bounty order status when a payment fails.
        """
        self.is_subscription_active = False
        self.bounty_status = self.ON_HOLD_PAYMENT_FAILED
        # self.was_pledge_added = False
        self.save(update_fields=["is_subscription_active", "bounty_status"])

    def reactivate_subscription(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        """
        Reactivate the subscription after a successful payment method update.
        
        This method attempts to reactivate the Stripe subscription and updates
        the local model status accordingly.
        
        Raises:
            stripe.error.StripeError: If there's an issue with the Stripe API call.
        """
        try:
            # Reactivate the Stripe subscription
            stripe_subscription = stripe.Subscription.retrieve(self.stripe_subscription_id)
            if stripe_subscription.status == "canceled":
                # If the subscription was canceled, create a new one
                new_subscription = stripe.Subscription.create(
                    customer=self.stripe_customer_id,
                    items=[{"price": stripe_subscription.plan.id}],
                )
                self.stripe_subscription_id = new_subscription.id
            else:
                # If the subscription wasn't canceled, just reactivate it
                stripe.Subscription.modify(
                    self.stripe_subscription_id, cancel_at_period_end=False, collection_method="charge_automatically"
                )

            # Update local model status
            self.bounty_status = self.ACTIVE
            self.is_subscription_active = True
            # self.was_pledge_added = True # removed since this filed will only be triggered once the bounty is added or moved
            self.save(update_fields=["bounty_status", "is_subscription_active", "stripe_subscription_id"])

        except stripe.error.StripeError as e:
            # Log the error and re-raise it
            logging.error(
                f"Stripe error while reactivating subscription: {str(e)}",
                exc_info=True,
                extra={"bounty_order_id": self.id},
            )
            print(f"Stripe error while reactivating subscription: {str(e)}")
            raise

    # give it a name
    def __str__(self):
        return f"{self.created}, from: {self.from_user} - to: {self.to_user} - amount: {self.amount}"

    # sort by created date
    class Meta:
        ordering = ["-created"]


# create a table to store bounty transactions for subscriptions
# this model is simply supposed to give additional information regarding every transaction related to a given BountyOrder, some of the fields are not very necessary but are there for debugging future purposes
class BountySubscriptionTransaction(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bounty_order = models.ForeignKey(
        BountyOrder,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="The bounty order that the subscription is for",
        related_name="bounty_order_transactions",
    )
    invoice_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The stripe invoice id that is returned in the webhook when a payment is successful",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=False,
        blank=False,
        help_text="The amount paid on this invoice not including tax, we want the amount that is added to the users account",
    )
    payment_method = models.CharField(
        max_length=255, null=True, blank=True, help_text="The payment method used to pay this invoice"
    )
    price_object_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="stripe uses a price object holds the price amount, the subscription gets its amount from the price object",
    )
    refund_date = models.DateTimeField(null=True, blank=True)
    billing_reason = models.CharField(
        max_length=255, null=True, blank=True, help_text="what on stripes end caused the billing to happen"
    )
    collection_method = models.CharField(
        max_length=255, null=True, blank=True, help_text="how the payment was collected (such as automatic or manual)"
    )
    event_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="every stripe event that is called to our webhook has a id or event_id, which can be used to look up the full event on stripe if needed",
    )

    def __str__(self):
        return f"{self.created},{self.bounty_order.id} - {self.amount}"

    # sort by created date
    class Meta:
        ordering = ["-created"]


class FeatureDonation(TimeStampedModel):
    ACTIVE = 0
    INACTIVE = 1
    STATUS_CHOICES = [
        (ACTIVE, "Active"),
        (INACTIVE, "Inactive"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feature_name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(blank=True)
    goal = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)

    def __str__(self):
        return f"{self.feature_name} - {self.current_amount} of {self.goal}"

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Feature Donation")
        verbose_name_plural = _("Feature Donations")


class Donation(TimeStampedModel):
    ACTIVE = 0
    CANCELLED_BY_USER = 1
    SUB_PAYMENT_FAILED = 2
    CANCELLED_SUB_PAYMENT_FAILED = 3
    CANCELLED_BY_ADMIN = 4

    DONATION_STATUS_CHOICES = [
        (ACTIVE, "Active"),
        (CANCELLED_BY_USER, "Cancelled"),
        (SUB_PAYMENT_FAILED, "Subscription Payment Failed"),
        (CANCELLED_SUB_PAYMENT_FAILED, "Cancelled, Subscription Payment Failed"),
        (CANCELLED_BY_ADMIN, "Cancelled By Admin"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("The user that the donation is being added from"),
    )
    feature_donation = models.ForeignKey(
        FeatureDonation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_("The feature donation this donation is associated with"),
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    email = models.EmailField(null=False, blank=False)
    paid = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_checkout_session_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("The Stripe checkout session ID that is created for a checkout session"),
    )
    stripe_payment_intent = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("The Stripe payment intent ID that is returned in the webhook when a payment is successful"),
    )
    stripe_invoice_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("The Stripe invoice ID that is returned in the webhook when a payment is successful"),
    )
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)
    recurring_payment = models.BooleanField(default=False, null=True, blank=True)
    number_of_months = models.PositiveIntegerField(
        null=True, blank=True, help_text=_("The number of months the user wants to pay this amount consecutively")
    )
    refund_date = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(choices=DONATION_STATUS_CHOICES, default=0)

    def __str__(self):
        return f"{self.email} has donated {self.amount}"

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Donation")
        verbose_name_plural = _("Donations")
