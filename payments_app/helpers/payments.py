from django.conf import settings
from decimal import Decimal
import stripe
from django.shortcuts import redirect
from django.urls import reverse
from urllib.parse import urlencode


# this function used as part of the process of setting up a subscription for a user
# util func
def return_stripe_customer_id(email, givers_full_name=None):
    # fetch the customer with the stripe api
    customer = stripe.Customer.list(email=email, limit=1)
    # check if the returned customer object has a stripe account associated with it
    if len(customer.data) < 1:
        # Create a Stripe Customer
        customer = stripe.Customer.create(email=email, name=givers_full_name)
        customer_id = customer.id
    else:
        customer_id = customer.data[0].id
    return customer_id


def create_stripe_customer_id(email, givers_full_name):
    # Create a Stripe Customer
    customer = stripe.Customer.create(email=email, name=givers_full_name)
    return customer.id


# util func
def get_price_object_id(product_id, custom_amount, lookup_key, recurring=False, billed_every=None):
    # SEE IF THERE IS ALREADY A PRICE OBJECT WITH THE SAME LOOKUP KEY/PRICE AMOUNT
    prices = stripe.Price.list(lookup_keys=[lookup_key], expand=["data.product"])

    # IF WE FIND ONE JUST USE ITS ID WHEN CREATING THE SUBSCRIPTION NO NEED TO CREATE A NEW ONE
    if len(prices.data) > 0:
        price = prices.data[0]
        price_object_id = price.id
    else:
        price_data = {
            "product": product_id,
            "unit_amount": custom_amount,
            "currency": "usd",
            "lookup_key": lookup_key,  # Add a unique lookup key for the custom price
        }

        if recurring:
            if billed_every is None:
                raise ValueError("billed_every must be specified for recurring payments")
            price_data["recurring"] = {"interval": "month", "interval_count": billed_every}

        price = stripe.Price.create(**price_data)
        price_object_id = price.id

    return price_object_id


# Util func
def get_stripe_session(stripe_checkout_session_id):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.retrieve(stripe_checkout_session_id, expand=["invoice"])
    return session


def expire_stripe_session(stripe_checkout_session_id):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        session = stripe.checkout.Session.expire(stripe_checkout_session_id)
        return session
    except stripe.error.InvalidRequestError as e:
        # Log the error or handle it as needed
        print(f"Error expiring session: {e}")
        return None


# create payment intent from here the user will be redirected to the stripe checkout page
def handel_bounty_payment(request, bounty_order, recurring_payment, givers_full_name, to_user):

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe.api_version = settings.STRIPE_API_VERSION

    BOUNTY_SUBSCRIPTION_PRICE_ID = settings.BOUNTY_SUBSCRIPTION_PRICE_ID
    BOUNTY_ONE_TIME_SUBSCRIPTION_PRICE_ID = settings.BOUNTY_ONE_TIME_SUBSCRIPTION_PRICE_ID

    success_url = request.build_absolute_uri(reverse("bounty_payment_complete", kwargs={"order_id": bounty_order.id}))
    cancel_url = request.build_absolute_uri(reverse("bounty_payment_canceled", kwargs={"order_id": bounty_order.id}))

    # Get the price object ID based on whether it's a recurring payment or not
    stripe_price_object_id = (
        BOUNTY_SUBSCRIPTION_PRICE_ID if recurring_payment else BOUNTY_ONE_TIME_SUBSCRIPTION_PRICE_ID
    )

    # if the user is logged in use his email to look up the stripe customer matching his email
    stripe_customer_id = request.user.stripe_customer_id
    if not stripe_customer_id:
        stripe_customer_id = create_stripe_customer_id(request.user.email, givers_full_name)
        request.user.stripe_customer_id = stripe_customer_id
        request.user.save()

    # Subscription Stripe Checkout Session Data
    session_data = {
        "mode": "subscription",
        "client_reference_id": str(bounty_order.id),
        "success_url": success_url,
        "cancel_url": cancel_url,
        "customer": stripe_customer_id,
        "line_items": [
            {
                "price": stripe_price_object_id,
                "quantity": 1,
            }
        ],
        "subscription_data": {
            "description": f"Bounty of ${bounty_order.amount} for {to_user.get_full_name()} ",
        },
        "payment_method_types": ["card"],
        "metadata": {
            "bounty recipient": to_user.get_full_name(),
            "bounty amount": bounty_order.amount,
            "bounty giver": givers_full_name,
        },
    }
    session = stripe.checkout.Session.create(**session_data)
    bounty_order.bounty_order_subscription_id = session.id
    bounty_order.stripe_subscription_id = session.subscription

    bounty_order.save()

    # Create the session
    session = stripe.checkout.Session.create(**session_data)
    bounty_order.stripe_checkout_session_id = session.id
    bounty_order.save()

    return redirect(session.url, code=303)


def handle_suggestion_payment(request, suggestion_object):

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe.api_version = settings.STRIPE_API_VERSION
    success_url = request.build_absolute_uri(
        reverse("suggestion_payment_complete", kwargs={"suggestion_id": suggestion_object.id})
    )
    cancel_url = request.build_absolute_uri(
        reverse("suggestion_payment_failed", kwargs={"suggestion_id": suggestion_object.id})
    )
    # One Time Stripe Checkout Session Data
    discount_value = Decimal(0)

    if request.user.is_authenticated:
        # if the user is logged in use his email to look up the stripe customer matching his email
        stripe_customer_id = request.user.stripe_customer_id
        if not stripe_customer_id:
            stripe_customer_id = create_stripe_customer_id(request.user.email, request.user.get_full_name())
            request.user.stripe_customer_id = stripe_customer_id
            request.user.save()
    else:
        stripe_customer_id = create_stripe_customer_id(suggestion_object.email, "No account")

    # if the suggestion is not custom (not one of the 3 default options i.e 1,5,15) create a new Price with the established product id
    # suggestion_amount = suggestion_object.amount

    # NOTE: this was put on hold since it seems stripe creates the price for the product if it does not exist (stripe will create it in cents however it will be charged the same amount)
    # if suggestion_amount == 1:
    #     stripe_price_object_id = settings.STRIPE_ONE_DOLLAR_SUGGESTION_PRICE_ID
    # elif suggestion_amount == 5:
    #     stripe_price_object_id = settings.STRIPE_FIVE_DOLLAR_SUGGESTION_PRICE_ID
    # elif suggestion_amount == 15:
    #     stripe_price_object_id = settings.STRIPE_FIFTEEN_DOLLAR_SUGGESTION_PRICE_ID
    # else:
    #     lookup_key = ('single_suggestion_' + f'{suggestion_object.amount}')#get_price_object_id(BOUNTY_SUBSCRIPTION_PRODUCT_ID, bounty_twice_yearly_charge, lookup_key, billed_every=6)
    #     stripe_price_object_id = get_price_object_id(settings.SUGGESTION_PRODUCT_ID, suggestion_amount, lookup_key)

    session_data = {
        "mode": "payment",
        "client_reference_id": str(suggestion_object.id),
        "success_url": success_url,
        "cancel_url": cancel_url,
        "customer": stripe_customer_id,
        "line_items": [
            {
                "price_data": {
                    "unit_amount": int(suggestion_object.amount * Decimal("100") - (discount_value * Decimal(100))),
                    "currency": "usd",
                    "product_data": {
                        "name": "Singles Suggestion",
                    },
                },
                "quantity": 1,
            }
        ],
        "invoice_creation": {
            "enabled": True,
        },
        "payment_method_types": ["card"],
    }

    # Create the session
    session = stripe.checkout.Session.create(**session_data)
    # store the session id on the suggestion_object object for later lookup
    suggestion_object.stripe_checkout_session_id = session.id
    suggestion_object.save()
    return redirect(session.url, code=303)


def handel_donation_payment(request, donation_object):

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe.api_version = settings.STRIPE_API_VERSION

    DONATION_SUBSCRIPTION_PRODUCT_ID = settings.DONATION_SUBSCRIPTION_PRODUCT_ID

    # Build the base URLs
    base_success_url = request.build_absolute_uri(
        reverse("partner_with_us", kwargs={"donation_id": donation_object.id})
    )
    base_cancel_url = request.build_absolute_uri(reverse("partner_with_us", kwargs={"donation_id": donation_object.id}))

    # Add query parameters
    success_url = f"{base_success_url}?{urlencode({'status': 'success'})}"
    cancel_url = f"{base_cancel_url}?{urlencode({'status': 'cancel'})}"
    amount_cents = int(donation_object.amount * Decimal("100"))
    # Get the price object ID based on whether it's a recurring payment or not
    recurring = True if donation_object.recurring_payment else False
    lookup_key = (
        "donation_sub_" + f"{donation_object.amount}"
        if recurring
        else "one_time_donation_" + f"{donation_object.amount}"
    )
    billed_every = 1 if recurring else None

    stripe_price_object_id = get_price_object_id(
        DONATION_SUBSCRIPTION_PRODUCT_ID if recurring else settings.DONATION_ONE_TIME_SUBSCRIPTION_PRICE_ID,
        amount_cents,
        lookup_key,
        recurring=recurring,
        billed_every=billed_every,
    )

    # if the user is logged in use his email to look up the stripe customer matching his email
    stripe_customer_id = request.user.stripe_customer_id if request.user.is_authenticated else None
    if not stripe_customer_id:
        if request.user.is_authenticated:
            stripe_customer_id = create_stripe_customer_id(request.user.email, request.user.get_full_name())
            request.user.stripe_customer_id = stripe_customer_id
            request.user.save()
        else:
            stripe_customer_id = create_stripe_customer_id(donation_object.email, "No account")

    mode = "subscription" if donation_object.recurring_payment else "payment"
    session_data = {
        "mode": mode,
        "client_reference_id": str(donation_object.id),
        "success_url": success_url,
        "cancel_url": cancel_url,
        "customer": stripe_customer_id,
        "line_items": [
            {
                "price": stripe_price_object_id,
                "quantity": 1,
            }
        ],
        "payment_method_types": ["card"],
        "metadata": {"Donation given by": donation_object.email, "bounty amount": donation_object.amount},
    }

    if mode == "subscription":
        session_data["subscription_data"] = {
            "description": f"Donation of ${donation_object.amount} for the further development of stripe",
        }
    session = stripe.checkout.Session.create(**session_data)

    donation_object.stripe_subscription_id = session.subscription
    donation_object.stripe_checkout_session_id = session.id

    donation_object.save()

    return redirect(session.url, code=303)
