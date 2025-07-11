import datetime, stripe, time, logging
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import BountyOrderForm
from django.contrib.auth.mixins import LoginRequiredMixin
from .helpers.general_helper import create_bounty_order
from .helpers.payments import handel_bounty_payment, handel_donation_payment
from django.contrib import messages as message
from .models import BountyOrder
from django.http import HttpResponse
from dateutil.relativedelta import relativedelta
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib import messages
from payments_app.helpers.payments import get_stripe_session
from utils.view_mixins import IsAdminOrStaff
from payments_app.helpers.payments import return_stripe_customer_id
from payments_app.forms import DonationForm
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from accounts_app.models import Bounty
from payments_app.models import Donation
from utils.email_sender import send_bounty_deleted_email

logger = logging.getLogger("project")
User = get_user_model()


class AddBounty(View):
    def get(self, request, to_user_id=None):
        to_user = None
        initial_data = {}

        if to_user_id is not None:
            post_to_path = reverse("add_bounty_to_user", kwargs={"to_user_id": to_user_id})
            to_user = get_object_or_404(User, id=to_user_id)
            initial_data = {"single_id": to_user.id}
        else:
            post_to_path = reverse("add_bounty")
        if request.user.is_authenticated:
            we_need_givers_name = len(request.user.get_full_name()) < 2
        else:
            we_need_givers_name = False
        add_bounty_form = BountyOrderForm(request=request, initial=initial_data)

        return render(
            request,
            "payments_app/add_bounty.html",
            {
                "to_user": to_user,
                "add_bounty_form": add_bounty_form,
                "post_to_path": post_to_path,
                "we_need_givers_name": we_need_givers_name,
            },
        )

    @method_decorator(login_required)
    def post(self, request, to_user_id=None):
        if to_user_id is not None:
            post_to_path = reverse("add_bounty_to_user", kwargs={"to_user_id": to_user_id})
        else:
            post_to_path = reverse("add_bounty")

        add_bounty_form = BountyOrderForm(request.POST, request=request)

        # if to_user_id is not None:
        #     to_user = get_object_or_404(User, id=to_user_id)
        # since you do not need a account to add a bounty, check if the user is authenticated

        from_user = get_object_or_404(User, id=request.user.id)
        try:
            # if it is a user that has a profile we can use the profile's address and zip
            zip = from_user.profile.zip
            address = from_user.profile.address
            city = from_user.profile.city
        except ObjectDoesNotExist:
            # Handle the case where the user does not have a profile
            zip = None
            address = None
            city = None

        # check if the form is valid
        if add_bounty_form.is_valid():
            amount = add_bounty_form.cleaned_data["amount"]
            recurring_payment = add_bounty_form.cleaned_data["recurring_payment"]
            number_of_months = add_bounty_form.cleaned_data["number_of_months"]
            single_id = add_bounty_form.cleaned_data["single_id"]

            email = from_user.email
            givers_full_name = request.user.get_full_name()

            if len(givers_full_name) < 2:
                first_name = add_bounty_form.cleaned_data["first_name"]
                last_name = add_bounty_form.cleaned_data["last_name"]
                # save the first and last name to the user's model

                from_user.first_name = first_name
                from_user.last_name = last_name
                from_user.save()
                givers_full_name = f"{first_name} {last_name}"

            # calculate the expiration date the user selected if any
            expiration_date = None
            if recurring_payment:
                expiration_date = datetime.date.today() + relativedelta(months=number_of_months)
            # TODO: somtimes the users that is slected might not add and submit with the form
            to_user = get_object_or_404(User, id=single_id)

            bounty_order = create_bounty_order(
                from_user,
                to_user,
                amount,
                email,
                address,
                zip,
                city,
                recurring_payment,
                expiration_date,
                number_of_months,
            )

            if bounty_order:
                return handel_bounty_payment(request, bounty_order, recurring_payment, givers_full_name, to_user)
            else:
                message.error(request, "There was an error initializing your order please contact customer support.")
        return render(
            request,
            "payments_app/add_bounty.html",
            {"to_user": to_user, "add_bounty_form": add_bounty_form, "post_to_path": post_to_path},
        )


# this view is meant to be ran once and that is when the user makes a successful payment and is redirected back the the site
class BountyPaymentComplete(View):
    def get(self, request, order_id):
        order = get_object_or_404(BountyOrder, id=order_id)

        # # if the order was already marked as paid, we do not want to add more money to the users account so we just return the success page
        # if order.paid == False:
        #     session_id = order.stripe_checkout_session_id
        #     retrieved_session = get_stripe_session(session_id)
        #     # get the amount paid on the invoice session
        #     amount_paid = (
        #         retrieved_session.amount_total / 100
        #     )  # stripe returns the amount in cents so we divide by 100 to get the amount in dollars
        #     invoice_id = retrieved_session.get("invoice", None)
        #     subscription_id = retrieved_session.subscription

        #     order.stripe_subscription_id = subscription_id  # update the bounty order object with the subscription id
        #     order.stripe_invoice_id = invoice_id
        #     order.is_subscription_active = True

        #     if retrieved_session.payment_status == "paid":
        #         pass

        #     else:
        #         messages.error(request, "Payment failed")
        #         return redirect("bounty_payment_canceled", order_id=order.id)

        # establish the bounty history and if the user can tag a shadchan for the template
        if order.from_user:
            bounty_history = BountyOrder.objects.filter(from_user=order.from_user, paid=True).exclude(id=order.id)
        else:
            bounty_history = BountyOrder.objects.filter(email=order.email, paid=True).exclude(id=order.id)
        PLEDGE_ASSURANCE_CHARGE = settings.PLEDGE_ASSURANCE_CHARGE
        return render(
            request,
            "payments_app/bounty_payment_complete.html",
            {"order": order, "bounty_history": bounty_history, "PLEDGE_ASSURANCE_CHARGE": PLEDGE_ASSURANCE_CHARGE},
        )


class BountyPaymentCanceled(View):
    def get(self, request, order_id):
        post_to_path = reverse("bounty_payment_canceled", kwargs={"order_id": order_id})
        bounty_order = get_object_or_404(BountyOrder, id=order_id)
        # instantiate the form
        to_user = bounty_order.to_user

        initial_data = {
            "amount": bounty_order.amount,
            "recurring_payment": bounty_order.recurring_payment,
            "number_of_months": bounty_order.number_of_months,
            "single_id": to_user.id,
        }
        add_bounty_form = BountyOrderForm(request=request, initial=initial_data)

        new_suggestion_url = reverse("add_bounty")  # Replace 'profile' with the name of your profile view
        message = 'Payment not processed! Please <a href="#submit_bounty_button" class="text-blue-500">resubmit this suggestion</a> or create a  <a href="{}" class="text-blue-500">new bounty<span aria-hidden="true"> &rarr;</span></a>'.format(
            new_suggestion_url
        )
        messages.info(request, mark_safe(message), extra_tags="banner_message")

        return render(
            request,
            "payments_app/add_bounty.html",
            {"to_user": to_user, "add_bounty_form": add_bounty_form, "post_to_path": post_to_path},
        )
        # return render(request, 'payments_app/bounty_payment_canceled.html')

    def post(self, request, order_id):

        post_to_path = reverse("bounty_payment_canceled", kwargs={"order_id": order_id})
        add_bounty_form = BountyOrderForm(request.POST, request=request)

        # if to_user_id is not None:
        #     to_user = get_object_or_404(User, id=to_user_id)\

        # since you do NOT need a account to add a bounty, check if the user is authenticated
        if request.user.is_authenticated:
            from_user = get_object_or_404(User, id=request.user.id)
            zip = from_user.profile.zip
            address = from_user.profile.address
            city = from_user.profile.city
        else:
            from_user = None
            zip = None
            address = None
            city = None

        # check if the form is valid
        if add_bounty_form.is_valid():
            amount = add_bounty_form.cleaned_data["amount"]
            recurring_payment = add_bounty_form.cleaned_data["recurring_payment"]
            number_of_months = add_bounty_form.cleaned_data["number_of_months"]
            single_id = add_bounty_form.cleaned_data["single_id"]

            if request.user.is_authenticated:
                givers_full_name = request.user.get_full_name()
                email = from_user.email
            else:
                email = add_bounty_form.cleaned_data["email"]
                givers_full_name = add_bounty_form.cleaned_data["full_name"]

            # calculate the expiration date the user selected if any
            expiration_date = None
            if recurring_payment:
                expiration_date = datetime.date.today() + relativedelta(months=number_of_months)

            to_user = get_object_or_404(User, id=single_id)

            bounty_order = create_bounty_order(
                from_user,
                to_user,
                amount,
                email,
                address,
                zip,
                city,
                recurring_payment,
                expiration_date,
                number_of_months,
                order_id,
            )

            if bounty_order:
                return handel_bounty_payment(request, bounty_order, recurring_payment, givers_full_name, to_user)
            else:
                message.error(request, "There was an error initializing your order please contact customer support.")
        return render(
            request,
            "payments_app/add_bounty.html",
            {"to_user": to_user, "add_bounty_form": add_bounty_form, "post_to_path": post_to_path},
        )


class Subscriptions(LoginRequiredMixin, View):
    def get(self, request):
        subscriptions = BountyOrder.objects.filter(from_user=request.user, is_subscription_active=True)
        donation_subscriptions = Donation.objects.filter(from_user=request.user, paid=True, status=Donation.ACTIVE)
        return render(
            request,
            "payments_app/subscriptions.html",
            {"subscriptions": subscriptions, "donation_subscriptions": donation_subscriptions},
        )

    def post(self, request):
        return render(request, "payments_app/subscriptions.html")


class CancelBountySubscription(LoginRequiredMixin, View):
    def post(self, request, bounty_id):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Retrieve the bounty order and ensure it belongs to the logged-in user
        bounty_order = get_object_or_404(BountyOrder, id=bounty_id, from_user=request.user)
        stripe_subscription_id = bounty_order.stripe_subscription_id

        if not stripe_subscription_id:
            return HttpResponse(status=400)

        try:
            with transaction.atomic():
                # Update the bounty order status
                bounty_order.is_subscription_active = False
                bounty_order.bounty_status = BountyOrder.CANCELLED_BY_USER
                bounty_order.save(update_fields=["is_subscription_active", "bounty_status"])

                # Retrieve the bounty and update the balance
                bounty = Bounty.objects.get(user=bounty_order.to_user)
                # if its recurring_payment we want to deduct the amount of the bounty_order * the number of transactions as long as the number
                # of transactions is not greater then the number_of_months (since it will happen that the subsciption will out live the number of months)
                if bounty_order.recurring_payment:
                    bounty_order_transactions_count = bounty_order.bounty_order_transactions.all().count()
                    if bounty_order_transactions_count > bounty_order.number_of_months:
                        bounty_order_transactions_count = bounty_order.number_of_months
                    amount = bounty_order_transactions_count * bounty_order.amount
                else:
                    amount = bounty_order.amount

                bounty.decrease_balance(amount, bounty_order)

                # Send cancellation email
                send_bounty_deleted_email.delay(bounty_order.id)

                # Schedule the Stripe subscription deletion after the transaction commits
                def delete_stripe_subscription():
                    try:
                        stripe.Subscription.delete(
                            stripe_subscription_id,
                            cancellation_details={"comment": "Cancelled by user"},
                        )
                        print("Subscription deleted")
                    except stripe.error.StripeError as e:
                        # Handle Stripe errors
                        error_message = getattr(e, "user_message", str(e))
                        # Log the error or take appropriate action
                        print(f"Stripe error: {error_message}")

                transaction.on_commit(delete_stripe_subscription)

        except ObjectDoesNotExist:
            return HttpResponse(status=400)
        except Exception as e:
            # Handle other exceptions and return a server error
            return HttpResponse(status=500)

        return HttpResponse(status=200)
        # return JsonResponse({"message": "Subscription cancelled successfully"}, status=200)


class CancelDonationSubscription(LoginRequiredMixin, View):
    # this one is simpler then the cancel bounty subscription all we need to to do is call stripe to cancel it and update the donation.status to 1
    def post(self, request, donation_id):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Retrieve the donation and ensure it belongs to the logged-in user
        donation = get_object_or_404(Donation, id=donation_id, from_user=request.user)
        stripe_subscription_id = donation.stripe_subscription_id

        if not stripe_subscription_id:
            return HttpResponse(status=400)

        try:
            with transaction.atomic():
                # Update the donation status
                donation.status = Donation.CANCELLED_BY_USER
                donation.save(update_fields=["status"])

                # Schedule the Stripe subscription deletion after the transaction commits
                def delete_stripe_subscription():
                    try:
                        stripe.Subscription.delete(
                            stripe_subscription_id,
                            cancellation_details={"comment": "Cancelled by user"},
                        )
                        print("Subscription deleted")
                    except stripe.error.StripeError as e:
                        # Handle Stripe errors
                        error_message = getattr(e, "user_message", str(e))
                        # Log the error or take appropriate action
                        print(f"Stripe error: {error_message}")
                        logger.error(f"Stripe error: {error_message}", exc_info=True)

                transaction.on_commit(delete_stripe_subscription)

        except ObjectDoesNotExist:
            return HttpResponse(status=400)
        except Exception as e:
            # Handle other exceptions and return a server error
            return HttpResponse(status=500)

        return HttpResponse(status=200)
        # return JsonResponse({"message": "Subscription cancelled successfully"}, status=200)


class CreateStipeCustomerPortal(LoginRequiredMixin, View):
    def get(self, request):
        # get the stripe customer id from the users object
        stripe_customer_id = request.user.stripe_customer_id
        if not stripe_customer_id:
            stripe_customer_id = return_stripe_customer_id(request.user.email, request.user.get_full_name())
            request.user.stripe_customer_id = stripe_customer_id
            request.user.save()
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            portal_session = stripe.billing_portal.Session.create(
                customer=stripe_customer_id,
                return_url=request.build_absolute_uri(reverse("customer_billing")),
                flow_data={"type": "payment_method_update"},
            )
        except Exception as e:
            messages.warning(request, "There was a error accessing the billing information, Please try again.")
            return redirect("customer_billing")

        return redirect(portal_session.url, code=303)


class BillingView(LoginRequiredMixin, View):
    def get(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe_customer_id = request.user.stripe_customer_id
        all_transactions = []

        if not stripe_customer_id:
            # return
            return render(request, "accounts_app/billing.html", {"all_transactions": all_transactions})

        # get all the invoices from a given customer
        invoices = stripe.Invoice.list(customer=stripe_customer_id)
        # charges = stripe.Charge.list(customer=customers_id)
        #    HOLDING HERE WE CAN GET THE SINGLE SUGGESTION CHARGES WITH THE CHARGE LIST, HOWEVER WE NEED TO SEE IF THE BOUNTY SUBSCRIPTIONS WILL ALSO BE LISTED HERE AND IF YEST WE NEED TO FILTER THE LIST ACCORDINGLY TO SPLIT THEM INTO 2 DIFFERNET LISTS OR AT LEAST LABELS
        # unpack the invoices and group them by subscription id
        for invoice in invoices:
            subscription_id = invoice.subscription
            if subscription_id and invoice.amount_due:
                # Extract the required information
                invoice_info = {
                    "hosted_invoice_url": invoice.hosted_invoice_url,
                    "invoice_pdf": invoice.invoice_pdf,
                    "amount_paid": (invoice.amount_paid / 100),
                    "billing_reason": invoice.billing_reason,
                    "currency": invoice.currency,
                    # 'description': invoice.description,
                    "description": invoice.lines.data[0].description if len(invoice.lines.data) > 0 else None,
                    "active": invoice.lines.data[0].plan.active,
                    "subscription": invoice.subscription,
                    "status": invoice.status,
                    "created": datetime.datetime.fromtimestamp(invoice.created),
                    "paid_at": (
                        datetime.datetime.fromtimestamp(invoice.status_transitions.paid_at)
                        if invoice.status_transitions.paid_at
                        else None
                    ),
                    "price_id": invoice.lines.data[0].price.id if invoice.lines.data[0].price else None,
                    "product_id": invoice.lines.data[0].price.product if invoice.lines.data[0].price else None,
                }

                all_transactions.append(invoice_info)
            # IF THE INVOICE IS NOT A SUBSCRIPTION
            elif invoice.amount_due > 0:
                invoice_info = {
                    "hosted_invoice_url": invoice.hosted_invoice_url,
                    "invoice_pdf": invoice.invoice_pdf,
                    "amount_paid": (invoice.amount_paid / 100),
                    "billing_reason": invoice.billing_reason,
                    "currency": invoice.currency,
                    # 'description': invoice.description,
                    "description": invoice.lines.data[0].description if len(invoice.lines.data) > 0 else None,
                    "status": invoice.status,
                    "created": datetime.datetime.fromtimestamp(invoice.created),
                    "paid_at": (
                        datetime.datetime.fromtimestamp(invoice.status_transitions.paid_at)
                        if invoice.status_transitions.paid_at
                        else None
                    ),
                    "price_id": invoice.lines.data[0].price.id if invoice.lines.data else None,
                    "product_id": invoice.lines.data[0].price.product if invoice.lines.data else None,
                }

                all_transactions.append(invoice_info)
        """
        result of suggestion_invoices array we really just want to have a single list of charges displayed to the user and there will be a badage diffrentiatiog the charge type based ont he product chareged
        [{'hosted_invoice_url': 'https://invoice.stripe.com/i/acct_1MIFDUEgD5UQyk1a/test_YWNjdF8xTUlGRFVFZ0Q1VVF5azFhLF9RbHN0YVJsWUZnV1BVdllsMkZZbHkyYXpXc200RE9sLDExNTc2NzE1NA0200VbyNj9Cr?s=ap', 'invoice_pdf': 'https://pay.stripe.com/invoice/acct_1MIFDUEgD5UQyk1a/test_YWNjdF8xTUlGRFVFZ0Q1VVF5azFhLF9RbHN0YVJsWUZnV1BVdllsMkZZbHkyYXpXc200RE9sLDExNTc2NzE1NA0200VbyNj9Cr/pdf?s=ap', 'amount_paid': 5.0, 'billing_reason': 'manual', 'currency': 'usd', 'description': None, 'status': 'paid', 'created': datetime.datetime(2024, 9, 1, 17, 15, 53), 'paid_at': datetime.datetime(2024, 9, 1, 17, 17, 44)}, {'hosted_invoice_url': None, 'invoice_pdf': None, 'amount_paid': 0.0, 'billing_reason': 'manual', 'currency': 'usd', 'description': None, 'status': 'draft', 'created': datetime.datetime(2024, 8, 29, 22, 30, 20), 'paid_at': None}, {'hosted_invoice_url': None, 'invoice_pdf': None, 'amount_paid': 0.0, 'billing_reason': 'manual', 'currency': 'usd', 'description': None, 'status': 'draft', 'created': datetime.datetime(2024, 8, 29, 21, 59, 57), 'paid_at': None}]
        """
        # HOLDING HERE WE NEED TO MAKE SURE WE ARE GETTING ALL THE USERS SUBSCRIPTIONS AS WELL AS SUGGESTION PAYMENTS
        # now combine the two lists and sort them by the created date

        all_transactions = sorted(all_transactions, key=lambda x: x["created"], reverse=True)

        return render(request, "accounts_app/billing.html", {"all_transactions": all_transactions})


# ADMIN ROUTS
class ADMIN_ViewAllPaidInvoices(IsAdminOrStaff):
    def get(self, request):
        import stripe
        from datetime import datetime

        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Get the current date and time
        now = datetime.now()

        # Get the timestamp for the start of the day
        start_of_day = datetime(now.year, now.month, now.day)

        # Convert the start of the day to a timestamp
        start_of_day_timestamp = int(start_of_day.timestamp())

        # Get the invoices that were created today and are paid
        invoices = stripe.Invoice.list(created={"gte": start_of_day_timestamp}, status="paid")

        # for invoice in invoices:
        #     # Get the subscription id
        #     subscription_id = invoice.subscription
        #     # Get the amount paid
        #     amount_paid = invoice.total / 100
        #     # Get the customer id
        #     customer_id = invoice.customer
        #     # invoice id
        #     invoice_id = invoice.id
        #     print(subscription_id, amount_paid, customer_id, invoice_id)
        return render(request, "payments_app/view_all_paid_invoices.html", {"invoices": invoices})


# we need to a function/script to run and see if there are any subscriptions that are not paid and we are expecting a payment from them so we can mark them as posed with a note that we are awaiting payment and there for the bounty had to be paused


class PartnerWithUsPage(View):
    def get(self, request, donation_id=None):
        if donation_id:
            try:
                donation = Donation.objects.get(id=donation_id)

                donation_form = DonationForm(user=request.user)
                if (
                    donation.paid
                    and donation.status != Donation.CANCELLED_BY_USER
                    and donation.status != Donation.CANCELLED_BY_ADMIN
                ):
                    messages.success(request, "Thank you for your donation!")
                    return render(request, "payments_app/partner_with_us.html", {"donation_form": donation_form})
                else:
                    # paid 0.5 seconds and check again since it can be that the webhook has failed for some reason
                    time.sleep(0.5)
                    donation.refresh_from_db()
                    if (
                        donation.paid
                        and donation.status != Donation.CANCELLED_BY_USER
                        and donation.status != Donation.CANCELLED_BY_ADMIN
                    ):
                        messages.success(request, "Thank you for your donation!")
                        return render(request, "payments_app/partner_with_us.html", {"donation_form": donation_form})
                    if donation.status != Donation.CANCELLED_BY_USER and donation.status != Donation.CANCELLED_BY_ADMIN:
                        messages.warning(request, "Welcome Back, We Where Unable To Confirm A Successful Transaction.")
                    donation_form = DonationForm(
                        initial={
                            "amount": donation.amount,
                            "recurring_payment": donation.recurring_payment,
                            "number_of_months": donation.number_of_months,
                        },
                        user=request.user,
                    )
            except Donation.DoesNotExist:
                messages.error(request, "Donation not found.")
                donation_form = DonationForm(user=request.user)
        else:
            donation_form = DonationForm(user=request.user)
        return render(request, "payments_app/partner_with_us.html", {"donation_form": donation_form})

    def post(self, request):
        donation_form = DonationForm(request.POST, user=request.user)
        if donation_form.is_valid():
            donation_object = donation_form.save()
            return handel_donation_payment(request, donation_object)
        return render(request, "payments_app/partner_with_us.html", {"donation_form": donation_form})
