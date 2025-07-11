import stripe
import logging
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from payments_app.models import BountyOrder, BountySubscriptionTransaction, Donation
from accounts_app.models import Bounty, BountyTransaction, Profile
from utils.email_sender import (
    send_sub_payment_failed_email,
    send_payment_update_successfully,
    send_bounty_successfully_created_email,
    send_bounty_assurance_charge_email,
    send_bounty_canceled_successfully,
    send_bounty_fully_paid_engagement_email,
    send_bounty_fully_paid_no_engagement_email,
    send_sub_paused_by_admin_email,
    send_donation_successfully_created_email,
    send_failed_payment_email,
    send_donation_subscription_cancelled_email,
)
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger("project")


@transaction.atomic
def process_bounty_payment(bounty_order_obj, session, event_id):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    # bounty_order_obj = BountyOrder.objects.select_for_update().get(id=bounty_order_id)

    # Define variables
    amount_paid = session.get("amount_total", None)
    if amount_paid is None:
        amount_paid = session.get("amount_paid", None)
    if amount_paid is not None:
        amount_paid = float(amount_paid) / 100
    else:
        # exit the function
        return None

    invoice_id = session.get("invoice") if session.get("invoice") else session.get("id")
    payment_method = session.get("payment_settings", {}).get("payment_method_types")
    price_object_id = session.get("lines", {}).get("data", [{}])[0].get("price", {}).get("id")
    billing_reason = session.get("billing_reason")
    collection_method = session.get("collection_method")

    # Create BountySubscriptionTransaction
    BountySubscriptionTransaction.objects.create(
        bounty_order=bounty_order_obj,
        invoice_id=invoice_id,
        amount=amount_paid,
        payment_method=payment_method,
        price_object_id=price_object_id,
        billing_reason=billing_reason,
        collection_method=collection_method,
        event_id=event_id,
    )

    # Add bounty to user account if not already added
    if not bounty_order_obj.was_pledge_added and bounty_order_obj.bounty_status is BountyOrder.ACTIVE:
        bounty, created = Bounty.objects.select_for_update().get_or_create(user=bounty_order_obj.to_user)
        if created:
            bounty.balance = int(bounty_order_obj.amount)
        else:
            print("adding sub balance for the first time")
            bounty.increase_balance(bounty_order_obj)
            bounty.refresh_from_db()
            bounty_order_obj.refresh_from_db()

        bounty.save()
        # bounty_order_obj.was_pledge_added = True

    # NOW CHECK TO SEE IF THIS INVOICE BELONGS TO A SUBSCRIPTION THAT WAS CANCELED DU TO A FAILED PAYMENT
    # NOTE: THIS IF STATEMENT WORKS I'M NOT SURE IF ITS NEEDED SINCE WE ALREADY HAVE THE PAYMENT UPDATE ENDPOINT
    if (
        bounty_order_obj.bounty_status == BountyOrder.ON_HOLD_PAYMENT_FAILED
        and not bounty_order_obj.is_subscription_active
        and not bounty_order_obj.was_pledge_added
    ):
        # INFO: THE REACTIVATE SUBSCRIPTION METHOD SHOULD BE UPDATING THE STATUSES OF THE BOUNTY ORDER AS WELL AS CREATING A NEW SUBSCRIPTION AND SAVING THAT NEW SUBSCRIPTION ID TO THE BOUNTY ORDER
        bounty_order_obj.reactivate_subscription()
        send_payment_update_successfully.delay(bounty_order_obj.id)
        bounty = Bounty.objects.get(user=bounty_order_obj.to_user)
        print("before adding balance after the being deactivated")
        bounty.increase_balance(bounty_order_obj)

    # Update bounty order
    print("before updating bounty order", bounty_order_obj.amount_paid_so_far, amount_paid)

    bounty_order_obj.amount_paid_so_far += Decimal(amount_paid)
    bounty_order_obj.stripe_invoice_id = invoice_id
    # Check if paid in full
    if bounty_order_obj.amount_paid_so_far >= bounty_order_obj.amount:
        bounty_order_obj.paid_in_full = True
        bounty_order_obj.is_subscription_active = False
        if bounty_order_obj.for_user.profile.status == Profile.STATUS_ENGAGED_TO_BE_MARRIED:
            bounty_order_obj.bounty_status = BountyOrder.PAID_IN_FULL
        else:
            bounty_order_obj.bounty_status = BountyOrder.PAID_IN_FULL_OVER_TIME_NO_ENGAGEMENT

        try:
            stripe.Subscription.delete(
                bounty_order_obj.stripe_subscription_id,
                cancellation_details={"comment": "Canceled after fully paid or after engagement"},
            )

        except stripe.error.StripeError as e:
            # Handle Stripe API error
            print(f"Stripe error: {str(e)}")
            logger.error(
                f"Stripe error While attempting to cancel subscription: {str(e)}",
                exc_info=True,
                extra={"event_id": event_id, "bounty_order_id": bounty_order_obj.id},
            )
    bounty_order_obj.save()
    print("---------------------------------")
    print("GOT TO END OF PROCESS BOUNTY PAYMENT")
    return bounty_order_obj


def handle_failed_payment(bounty_order):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    print("---------------------------------")
    print("in handle_failed_payment function")

    if not bounty_order:
        return "Invalid bounty order"

    try:
        updated_subscription = stripe.Subscription.modify(
            bounty_order.stripe_subscription_id,
            pause_collection={
                "behavior": "mark_uncollectible",
            },
        )
        print(f"Subscription {bounty_order.stripe_subscription_id} paused due to payment failure")
    except stripe.error.StripeError as e:
        return f"Failed to pause Stripe subscription: {str(e)}"

    try:
        bounty_order.update_failed_payment_status()
    except ObjectDoesNotExist:
        return "Bounty does not exist for the given user"
    except Exception as e:
        return f"Failed to update bounty order and bounty: {str(e)}"

    send_sub_payment_failed_email.delay(bounty_order.id)
    return "Subscription paused and bounty updated successfully"


def handle_deleted_subscription(subscription_id):
    # see first if its a donation object
    donation = Donation.objects.filter(stripe_subscription_id=subscription_id).first()
    if donation:
        if donation.status != Donation.CANCELLED_BY_USER:
            donation.status = Donation.CANCELLED_BY_ADMIN
            donation.save()

        send_donation_subscription_cancelled_email.delay(donation.id)
        return True
    try:
        bounty_order = BountyOrder.objects.get(stripe_subscription_id=subscription_id)
        # if the bounty is already canceled by customer return and exit the function
        if bounty_order.bounty_status == BountyOrder.CANCELLED_BY_USER:
            return True

        if bounty_order.bounty_status == BountyOrder.PAID_IN_FULL:
            # mark as not active
            send_bounty_fully_paid_engagement_email.delay(bounty_order.id)
            return True

        if bounty_order.bounty_status == BountyOrder.PAID_IN_FULL_OVER_TIME_NO_ENGAGEMENT:
            send_bounty_fully_paid_no_engagement_email.delay(bounty_order.id)
            # IF IT SIMPLY THE FINAL COLLECTION (SAY ITS A 50 BOUNTY AND 5 YEARS PASS IT SHOULD SIMPLY SAY THAT THERE BOUNTY HAS BEEN FULLY PAID AND NO FURTHER CHARGES WILL BE MADE)
            return True
        with transaction.atomic():
            # was the money added to the account
            if bounty_order.was_pledge_added:
                bounty = Bounty.objects.get(user=bounty_order.to_user)
                # now get the total amount of bounty_order_transactions associated with the bounty_order

                if bounty_order.recurring_payment:
                    bounty_order_transactions_count = bounty_order.bounty_order_transactions.all().count()
                    if bounty_order_transactions_count > bounty_order.number_of_months:
                        bounty_order_transactions_count = bounty_order.number_of_months
                    amount = bounty_order_transactions_count * bounty_order.amount
                else:
                    amount = bounty_order.amount

                bounty.decrease_balance(amount, bounty_order)
            # just make sure the status is active before we flip the status to canceled_by_admin
            if bounty_order.bounty_status == BountyOrder.ACTIVE:
                bounty_order.bounty_status = BountyOrder.CANCELLED_BY_ADMIN
                bounty_order.save()

        # Send a notification email to the user
        send_bounty_canceled_successfully.delay(bounty_order.id)

        # return HttpResponse(status=200)
        return True

    except BountyOrder.DoesNotExist:
        logger.error(f"Failed to find bounty order for subscription {subscription_id}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Failed to cancel subscription {subscription_id}: {str(e)}", exc_info=True)
        return False


@transaction.atomic
def handle_updated_payment_method(customer_id, default_payment_method_id):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if not customer_id or not default_payment_method_id:
        return "Must provide customer ID and default payment method ID"
    # confirm the payment method is valid
    try:
        payment_method = stripe.PaymentMethod.retrieve(default_payment_method_id)
        if payment_method["type"] != "card" and payment_method["card"]["checks"]["cvc_check"] != "pass":
            # exit function and do nothing
            print("Payment method is not a valid card")
            return "Payment method is not a valid card"

    except stripe.error.StripeError as e:
        print(f"Error retrieving payment method: {str(e)}")
        logger.error(f"Error retrieving payment method from customer {customer_id}: {str(e)}", exc_info=True)
        return f"Error retrieving payment method: {str(e)}"

    bounty_orders = BountyOrder.objects.filter(
        stripe_customer_id=customer_id,
        bounty_status=BountyOrder.ON_HOLD_PAYMENT_FAILED,
        is_subscription_active=False,
        was_pledge_added=False,
    )

    for bounty_order in bounty_orders:
        try:
            with transaction.atomic():
                bounty_order.reactivate_subscription()
                bounty = Bounty.objects.get(user=bounty_order.to_user)
                bounty.increase_balance(bounty_order)
            send_payment_update_successfully.delay(bounty_order.id)
        except ObjectDoesNotExist:
            return f"Bounty not found for order {bounty_order.id}"
        except Exception as e:
            return f"Failed to update bounty order {bounty_order.id}: {str(e)}"

    return f"Successfully updated {len(bounty_orders)} bounty orders"


"""
IMPORTANT:
THE CURRENT SET UP THERE ARE THREE TYPES OF WEBHOOKS WE ARE HANDLING,
    - checkout.session.completed
        - WE WILL PROCESS THE INITIAL PAYMENT FOR THE SUBSCRIPTION AND ADD THE AMOUNT TO THE USERS ACCOUNT

    - invoice.paid
        - WE WILL PROCESS ALL SUBSEQUENT PAYMENTS FOR THE SUBSCRIPTION AND ADD THE AMOUNT TO THE USERS ACCOUNT

    - invoice.payment_failed
        - WE WILL CANCEL THE SUBSCRIPTION, NOTIFY THE USER AND REMOVE THE AMOUNT FROM THE USERS ACCOUNT
"""


# make a stripe webhook to verify the payment
@csrf_exempt
def stripe_webhook(request):
    """BOILERPLATE CODE TO RECEIVE AND VERIFY A STRIPE WEBHOOK"""
    # payload = request.body
    # sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    # if not sig_header:
    #     logger.error("No stripe signature header found", extra={"event_id": None})
    #     return HttpResponse(status=400)
    # event = None
    # # verify the event by using the stripe.Webhook.construct_event method
    # try:
    #     event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    # except ValueError:
    #     # invalid payload
    #     logger.error("Invalid payload received", extra={"event_id": None})
    #     return HttpResponse(status=400)
    # except stripe.error.SignatureVerificationError:
    #     # invalid signature
    #     logger.error(f"Invalid signature received: {sig_header} and webhook secret: {settings.STRIPE_WEBHOOK_SECRET}")
    #     return HttpResponse(status=400)
    # Get raw body directly from wsgi.input to avoid middleware interference
    try:
        # Get raw request data
        if hasattr(request, "_body"):
            payload = request._body
        else:
            payload = request.body

        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        # Add extensive debugging
        logger.info(f"Webhook received with sig: {sig_header[:30]}...")
        logger.info(f"Payload size: {len(payload)} bytes")

        # Try the verification
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)

    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Signature verification failed: {str(e)}")
        # Just for debugging - log the first 100 bytes of payload
        logger.error(f"First 100 bytes of payload: {payload[:100]}")
        return HttpResponse(status=400)

    """HANDLE THE CREATION OF A CHECKOUT SESSION FOR A SUBSCRIPTION AS WELL AS ONE TIME PAYMENTS"""
    if event.type == "checkout.session.completed":
        session = event.data.object
        # try to match the client_reference_id to a Donation Object
        client_reference_id = session.get("client_reference_id")  # get the client reference id
        try:
            donation = Donation.objects.get(id=client_reference_id)
            # update the donation to paid
            donation.paid = True
            # if its a subscription add the subscription id to the donation object
            if session.get("mode") == "subscription":
                donation.stripe_subscription_id = session.get("subscription")

            donation.save()
            # send the email that the donation was successful and thanking the user
            send_donation_successfully_created_email.delay(donation.id)
            return HttpResponse(status=200)
        except Donation.DoesNotExist:
            # simply to nothing and allow the webhook to process the next event
            pass
        # IF NOT A SUBSCRIPTION IGNORE THE EVENT
        if session.get("mode") == "subscription":
            """UPDATE THE DATABASE WITH THE SUBSCRIPTION INFO AND THE CANCEL AT DATE"""
            subscription_id = session.get("subscription")  # get subscription id

            invoice_id = session.get("invoice")  # get the invoice id

            bounty_order = BountyOrder.objects.get(id=client_reference_id)  # get the bounty order object
            """ADD THE AMOUNT TO THE USER'S BALANCE"""
            # If a BountySubscriptionTransaction with the given invoice ID already exists, skip the rest of the code
            try:
                BountySubscriptionTransaction.objects.get(invoice_id=invoice_id)
                return HttpResponse(status=200)
            except BountySubscriptionTransaction.DoesNotExist:
                # add the payment intent to the bounty order
                bounty_order.stripe_payment_intent = session.get("payment_intent")
                # update the bounty order object with the subscription id
                bounty_order.stripe_subscription_id = subscription_id
                # update the bounty order object with the customer id
                bounty_order.stripe_customer_id = session.get("customer")
                bounty_order.save()
                process_bounty_payment(bounty_order, session, event.id)
                bounty_order.paid = True
                bounty_order.is_subscription_active = True
                # expiration_datetime = bounty_order.recurring_payment_expiration_date
                # convert the expiration date to a timestamp

                bounty_order.save()
                # send email that the payment was successful
                send_bounty_successfully_created_email.delay(bounty_order.id)
                return HttpResponse(status=200)
        else:
            # assuming its just a one time payment and not a subscription simply return 200
            return HttpResponse(status=200)

    """
    HANDLE RECURRING SUBSCRIPTION PAYMENTS

    This section processes 'invoice.paid' events for subscription renewals.
    It adds the payment amount to the user's account balance for each successful
    recurring billing cycle after the initial subscription setup.
    """
    if event.type == "invoice.paid":
        print("---------------------------------")
        print("before process_bounty_payment in the invoice.paid event")
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = event.data.object
        # get the subscription id
        subscription_id = session.get("subscription", None)

        # if there is no subscription id exit the function since it is a one time payment
        if not subscription_id:
            return HttpResponse(status=200)

        try:
            bounty_order = BountyOrder.objects.get(stripe_subscription_id=subscription_id)
        except BountyOrder.DoesNotExist:
            # try to get a object from the Donation object if we can get it we should not log any error
            try:
                # Get the product ID from the invoice data
                try:
                    product_id = session["lines"]["data"][0]["plan"]["product"]
                    if product_id == settings.DONATION_SUBSCRIPTION_PRODUCT_ID:
                        return HttpResponse(status=200)
                except Exception as e:
                    pass
                print(
                    "in the paid webhook and we need to get the Donation object by the subscription id", subscription_id
                )
                donation = Donation.objects.get(stripe_subscription_id=subscription_id)
                return HttpResponse(status=200)
            except Donation.DoesNotExist:
                pass
            # as of jun 2, 2024 the subscription was not added to the bounty order right it was only being added in the checkout.session.completed event so we need to add the subscription_id to the order when it is created
            print("bounty order does not exist")
            logging.error(
                "bounty order does not exist, but a payment was received, big problem someone paid and we dont know where to put the money",
                exc_info=True,
                extra={"event_id": event.id},
            )
            return HttpResponse(status=404)
        # IMPOTENT IF STATEMENT, IF REMOVED IT WILL END UP ADDING DOUBLE BOUNTY TO A PERSONS ACCOUNT IN THE FIRST TRANSACTION
        if bounty_order.created and bounty_order.created.date() == timezone.now().date():
            return HttpResponse(status=200)
        else:
            print("---------------------------------")
            print("before process_bounty_payment in the invoice.paid event")
            was_on_hold = bounty_order.bounty_status == BountyOrder.ON_HOLD_PAYMENT_FAILED
            # now add the amount paid to the BountyOrder and if the amount is paid in full mark it as so and cancel the subscription
            bounty_order_obj = process_bounty_payment(bounty_order, session, event.id)
            if not was_on_hold:
                send_bounty_assurance_charge_email.delay(bounty_order_obj.id)
            # HOLDING HERE WE ARE STEPPING THROUGH THE PAYMENT SUBMISSION PROCESS, NEXT UP THE IF PAID ENDPOINT AFTER THE SUBSCRIPTION IS RETRIGERD, AFTER THAT THE FAILED PYAMENT AND AFTER THAT THE UPDATE PAYMENT METHOD ECT.

            return HttpResponse(status=200)

    """HANDLE EVENTS THAT ARE OF invoice.payment_failed TO CANCEL THE SUBSCRIPTION AND UPDATE THE DATABASE"""
    if event.type == "invoice.payment_failed":
        # print("in invoice.payment_failed if statement")
        # print("---------------------------------")
        # breakpoint()
        session = event.data.object
        # get the subscription id
        print("---------------------------------")
        print("before handle_failed_payment in the invoice.payment_failed event")
        subscription_id = session.get("subscription")
        # get the bountyOrder using the subscription id
        try:
            bounty_order = BountyOrder.objects.filter(stripe_subscription_id=subscription_id).first()
            if bounty_order:
                handle_failed_payment(bounty_order)
                return HttpResponse(status=200)
            else:
                # try and see if its a donation
                donation = Donation.objects.filter(stripe_subscription_id=subscription_id).first()
                if donation:
                    donation.status = Donation.SUB_PAYMENT_FAILED
                    donation.save()
                    send_failed_payment_email.delay(donation.id)
                    return HttpResponse(status=200)
        except BountyOrder.DoesNotExist:
            logger.error(
                f"Bounty order does not exist for subscription {subscription_id}",
                exc_info=True,
                extra={"event_id": event.id},
            )
            return HttpResponse(status=404)

    # HANDLE PAYMENT UPDATED EVENTS
    # TODO: SEE IF THIS IS NEEDED IF WE ALREADY HAVE THE CUSTOMER.UPDATED EVENT (test if when updating the customers payment in the stripe admin if this event will be triggered and not the update)
    # if event.type == "customer.payment_method.updated":
    #     print("in customer.payment_method.updated if statement")
    #     print("---------------------------------")
    #     customer_id = event.data.object.get("customer")
    #     # now send the user a email that there payment method was updated and that there active subscriptions have been reactivated and updated

    #     handle_updated_payment_method(customer_id)

    if event.type == "customer.subscription.deleted":
        session = event.data.object
        subscription_id = session.get("id")
        handle_deleted_subscription(subscription_id)
        return HttpResponse(status=200)

    if event.type == "customer.updated":
        # check if the user has updated there payment method to a valid card
        print("in customer.updated if statement")
        print("---------------------------------")
        customer = event["data"]["object"]
        customer_id = customer["id"]

        # Check if the customer has a default payment method
        default_payment_method_id = customer["invoice_settings"]["default_payment_method"]

        if default_payment_method_id:
            handle_updated_payment_method(customer_id, default_payment_method_id)

        return HttpResponse(status=200)

    if event.type == "customer.subscription.updated":
        # check if the user has updated there payment method to a valid card
        print("in customer.subscription.updated if statement")
        print("---------------------------------")
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]
        subscription_id = subscription["id"]
        status = subscription["status"]

        if status == "active":
            print(f"Subscription {subscription_id} is active for customer {customer_id}")
        elif status == "paused":
            print(f"Subscription {subscription_id} paused for customer {customer_id}")

            # dong send the email if bountyOrder.bounty_status == ON_HOLD_PAYMENT_FAILED
            bounty_order = BountyOrder.objects.get(stripe_subscription_id=subscription_id)
            if bounty_order.bounty_status == BountyOrder.ON_HOLD_PAYMENT_FAILED:
                return HttpResponse(status=200)

            bounty_order.bounty_status = BountyOrder.ON_HOLD_BY_ADMIN
            bounty_order.save()
            send_sub_paused_by_admin_email.delay(bounty_order.id)

        # # Check if the customer has a default payment method
        # default_payment_method_id = subscription["default_payment_method"]

        # if default_payment_method_id:
        #     handle_updated_payment_method(customer_id, default_payment_method_id)

        return HttpResponse(status=200)

    if event.type == "invoice.upcoming":
        # DO NOTHING FOR NOW
        return HttpResponse(status=200)

    # stripe requires a 200 response for all webhooks to confirm that they have been received
    return HttpResponse(status=200)
