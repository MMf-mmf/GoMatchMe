import logging
from django.conf import settings
from django.core.mail import EmailMessage
from django.templatetags.static import static
from django.template.loader import render_to_string


from django.urls import reverse
from urllib.parse import urlencode
from celery import shared_task
from match_app.models import Suggestion
from django.contrib.auth import get_user_model
from payments_app.models import BountyOrder, Donation

User = get_user_model()
logger = logging.getLogger("project")


# util function
def get_full_url(url_name, url_params=None, query_params=None, hash_params=None, static_path=None):
    if settings.DEBUG:
        domain = "localhost:8000"  # or the port your development server is running on
        scheme = "http"
    else:
        # current_site = Site.objects.get_current()
        # domain = current_site.domain
        domain = "ShidduchMe.com"
        scheme = "https"

    if static_path:
        relative_url = static(static_path)
    else:
        relative_url = reverse(url_name, kwargs=url_params)

    if query_params:
        query_string = urlencode(query_params)
        full_url = f"{scheme}://{domain}{relative_url}?{query_string}"
    else:
        full_url = f"{scheme}://{domain}{relative_url}"

    if hash_params:
        full_url = f"{full_url}#{hash_params}"

    return full_url


# def get_full_url(request, url_name, url_params=None, query_params=None):
#     if settings.DEBUG:
#         domain = 'localhost:8000'  # or the port your development server is running on
#     else:
#         current_site = Site.objects.get_current()
#         domain = current_site.domain

#     relative_url = reverse(url_name, kwargs=url_params)

#     if query_params:
#         query_string = urlencode(query_params)
#         full_url = f"{request.scheme}://{domain}{relative_url}?{query_string}"
#     else:
#         full_url = f"{request.scheme}://{domain}{relative_url}"

#     return full_url


"""
the general gist of how emails are sent here is.
1. create a reusable function that actually sends the emails
2. create a function to call the reusable function and manipulate the data/templates in the correct manor as well as to pass in the correct parameters
"""

"""
THESE FUNCTIONS ARE FOR SENDING EMAILS WITH MIXED WAGTAIL AND DJANGO TEMPLATES. THE WAGTAIL BODY IS INSERTED INTO THE DJANGO TEMPLATE
"""
# def send_mixed_wagtail_django_template_email(email_to, subject, email_template_path, context, file_attachment_path=None):
#     html_content = render_to_string(email_template_path, context)
#     email = EmailMessage(subject,
#                         html_content,
#                         settings.DEFAULT_FROM_EMAIL,
#                         [email_to],
#             )
#     if file_attachment_path != None:
#         email.attach_file(file_attachment_path)
#     email.content_subtype = "html"
#     email.send(fail_silently=False)


# def vendor_lead_confirmation_email(contact_name, company_name, contact_email):

#     email_template_path = 'vendor_portal/email/lead_application_confirmation.html'
#     email = EmailTemplate.objects.get(internal_reference_name='vendor_lead_application_email')

#     template = Template(email.body)
#     subject = 'Application Submitted'
#     context = Context({
#         'user_name': contact_name,
#     })
#     html_content = mark_safe(template.render(context))

#     send_mixed_wagtail_django_template_email(contact_email, subject, email_template_path, context={'wagtail_template': html_content})


""" 
THESE FUNCTIONS ARE FOR SENDING EMAILS WITH WAGTAIL TEMPLATES  !ONLY!.
"""
# def send_wagtail_template_email(email_to, subject, html_content, file_attachment_path=None):
#     email = EmailMessage(subject,
#                         html_content,
#                         settings.DEFAULT_FROM_EMAIL,
#                         [email_to],
#             )
#     if file_attachment_path != None:
#         email.attach_file(file_attachment_path)
#     email.content_subtype = "html"
#     email.send(fail_silently=False)

# EXAMPLE USAGE FOR SENDING A WAGTAIL TEMPLATE ONLY EMAIL
# def send_become_a_vendor_email_confirmation(contact_name, company_name, contact_email):
#     email = EmailTemplate.objects.filter(title='Customer Registration email').first()
#     email = EmailTemplate.objects.all().first()
#     template = Template(email.body)
#     subject = 'Application Submitted'
#     context = Context({
#         'user_name': contact_name,
#     })
#     html_content = template.render(context)
#     send_wagtail_template_email(contact_email, subject, html_content)


""" 
THESE FUNCTIONS ARE FOR SENDING EMAILS WITH DJANGO TEMPLATES !ONLY!
"""


# example usage of sending_django_template_email
def send_django_template_email(email_to, subject, email_template_path, context=None, file_attachment_path=None):
    html_content = render_to_string(email_template_path, context)
    email = EmailMessage(
        subject,
        html_content,
        settings.DEFAULT_FROM_EMAIL,
        [email_to],
    )
    if file_attachment_path != None:
        email.attach_file(file_attachment_path)
    email.content_subtype = "html"
    email.send(fail_silently=False)


@shared_task
def send_sub_payment_failed_email(bounty_order_id):
    bounty_order = BountyOrder.objects.get(id=bounty_order_id)
    email_to = bounty_order.email
    subject = f"Payment Failed"
    email_template_path = "emails/sub_payment_failed.html"
    update_payment_url = get_full_url("customer_billing", query_params={"customer_portal": True})
    logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
    privacy_policy_url = get_full_url("privacy_policy")
    # # Generate absolute URL POTENTIAL TODO
    # relative_url = reverse('create_customer_portal')
    # customer_portal_url = 'http://{}{}'.format(current_site.domain, relative_url)

    send_django_template_email(
        email_to,
        subject,
        email_template_path,
        context={
            "to_user": bounty_order.to_user,
            "from_user": bounty_order.from_user,
            "bounty_order": bounty_order,
            "update_payment_url": update_payment_url,
            "logo_url": logo_url,
            "privacy_policy_url": privacy_policy_url,
        },
    )


@shared_task
def send_bounty_canceled_successfully(bounty_order_id):
    bounty_order = BountyOrder.objects.get(id=bounty_order_id)
    email_to = bounty_order.from_user.email
    subject = f"Bounty Canceled"
    email_template_path = "emails/bounty_canceled_succsullfy.html"
    logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
    privacy_policy_url = get_full_url("privacy_policy")
    send_django_template_email(
        email_to,
        subject,
        email_template_path,
        context={
            "to_user": bounty_order.to_user,
            "bounty_order": bounty_order,
            "logo_url": logo_url,
            "privacy_policy_url": privacy_policy_url,
        },
    )


@shared_task
def send_payment_update_successfully(bounty_order_id):
    bounty_order = BountyOrder.objects.get(id=bounty_order_id)
    email_to = bounty_order.from_user.email
    subject = f"Bounty Reactivated"
    email_template_path = "emails/bounty_reactivated_succsullfy.html"
    logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
    privacy_policy_url = get_full_url("privacy_policy")
    send_django_template_email(
        email_to,
        subject,
        email_template_path,
        context={
            "to_user": bounty_order.to_user,
            "bounty_order": bounty_order,
            "logo_url": logo_url,
            "privacy_policy_url": privacy_policy_url,
        },
    )


def send_contact_shadchan_approval_email(user, shadchan_user):
    email_to = user.email
    subject = f"Contact Shadchan Approval"
    email_template_path = "emails/contact_shadchan_approval.html"
    logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
    privacy_policy_url = get_full_url("privacy_policy")
    send_django_template_email(
        email_to,
        subject,
        email_template_path,
        context={
            "to_user": user,
            "shadchan_user": shadchan_user,
            "logo_url": logo_url,
            "privacy_policy_url": privacy_policy_url,
        },
    )


def send_contact_shadchan_rejection_email(user, shadchan_user):
    email_to = user.email
    subject = f"Contact Request Update"
    email_template_path = "emails/contact_shadchan_rejection.html"
    logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
    privacy_policy_url = get_full_url("privacy_policy")
    send_django_template_email(
        email_to,
        subject,
        email_template_path,
        context={
            "to_user": user,
            "shadchan_user": shadchan_user,
            "logo_url": logo_url,
            "privacy_policy_url": privacy_policy_url,
        },
    )


@shared_task
def email_tagged_shadchan(shadchan_user_id, suggestion_id):
    try:
        suggestion = Suggestion.objects.get(id=suggestion_id)
        shadchan_user = User.objects.get(id=shadchan_user_id)
        email_to = shadchan_user.email
        subject = "You have been tagged in a suggestion"
        email_template_path = "emails/tagged_shadchan.html"
        suggestion_list_url = get_full_url("suggestions", query_params={"suggestion": suggestion_id})
        logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
        privacy_policy_url = get_full_url("privacy_policy")
        send_django_template_email(
            email_to,
            subject,
            email_template_path,
            context={
                "to_user": shadchan_user,
                "suggestion": suggestion,
                "suggestion_list_url": suggestion_list_url,
                "logo_url": logo_url,
                "privacy_policy_url": privacy_policy_url,
            },
        )
    except Exception as e:
        logger.error(f"Failed to send email to tagged shadchan: {e}")


@shared_task
def send_confirmation_to_suggester(suggestion_id):
    try:
        suggestion = Suggestion.objects.get(id=suggestion_id)
        tagged_shadchonim = suggestion.tagged_users.all()
        email_to = suggestion.email if suggestion.email else suggestion.made_by.email
        subject = "Your suggestion has been sent"
        email_template_path = "emails/suggestion_confirmation.html"

        your_suggestions_url = get_full_url("users_suggestions")
        logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
        privacy_policy_url = get_full_url("privacy_policy")
        send_django_template_email(
            email_to,
            subject,
            email_template_path,
            context={
                "tagged_shadchonim": tagged_shadchonim,
                "suggestion": suggestion,
                "your_suggestions_url": your_suggestions_url,
                "logo_url": logo_url,
                "privacy_policy_url": privacy_policy_url,
            },
        )
    except Exception as e:
        logger.error(f"Failed to send confirmation email to suggester: {e}")


@shared_task
def send_bounty_successfully_created_email(bounty_order_id):
    try:
        bounty_order = BountyOrder.objects.get(id=bounty_order_id)
        email_to = bounty_order.from_user.email
        subject = "Bounty Created"
        email_template_path = "emails/bounty_successfully_created_email.html"
        logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
        privacy_policy_url = get_full_url("privacy_policy")
        send_django_template_email(
            email_to,
            subject,
            email_template_path,
            context={
                "to_user": bounty_order.to_user,
                "bounty_order": bounty_order,
                "logo_url": logo_url,
                "privacy_policy_url": privacy_policy_url,
            },
        )
    except Exception as e:
        logger.error(f"Failed to send email to bounty creator: {e}")


@shared_task
def send_bounty_assurance_charge_email(bounty_order_id):
    try:
        bounty_order = BountyOrder.objects.get(id=bounty_order_id)
        email_to = bounty_order.from_user.email
        subject = "Bounty Assurance Charge"
        email_template_path = "emails/bounty_assurance_charge_email.html"
        logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
        privacy_policy_url = get_full_url("privacy_policy")
        send_django_template_email(
            email_to,
            subject,
            email_template_path,
            context={
                "to_user": bounty_order.to_user,
                "bounty_order": bounty_order,
                "logo_url": logo_url,
                "privacy_policy_url": privacy_policy_url,
            },
        )
    except Exception as e:
        logger.error(f"Failed to send email to bounty creator: {e}")


@shared_task
def send_bounty_deleted_email(bounty_order_id):
    try:
        bounty_order = BountyOrder.objects.get(id=bounty_order_id)
        email_to = bounty_order.from_user.email
        subject = "Bounty Canceled"
        # TODO: CREATE THE TEMPLATE
        email_template_path = "emails/bounty_delete_email.html"
        faq_url = get_full_url("faq", hash_params="#bounty-cancellation")
        logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
        privacy_policy_url = get_full_url("privacy_policy")
        send_django_template_email(
            email_to,
            subject,
            email_template_path,
            context={
                "to_user": bounty_order.to_user,
                "bounty_order": bounty_order,
                "faq_url": faq_url,
                "logo_url": logo_url,
                "privacy_policy_url": privacy_policy_url,
            },
        )
    except Exception as e:
        logger.error(f"Failed to send email to bounty creator: {e}")


@shared_task
def send_bounty_fully_paid_engagement_email(bounty_order_id):
    try:
        bounty_order = BountyOrder.objects.get(id=bounty_order_id)
        email_to = bounty_order.to_user.email
        subject = "Bounty Fully Paid"
        email_template_path = "emails/bounty_fully_paid_engagement_email.html"
        logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
        privacy_policy_url = get_full_url("privacy_policy")

        send_django_template_email(
            email_to,
            subject,
            email_template_path,
            context={
                "to_user": bounty_order.to_user,
                "bounty_order": bounty_order,
                "logo_url": logo_url,
                "privacy_policy_url": privacy_policy_url,
            },
        )
    except Exception as e:
        logger.error(f"Failed to send email to bounty creator: {e}")


@shared_task
def send_bounty_fully_paid_no_engagement_email(bounty_order_id):
    try:
        bounty_order = BountyOrder.objects.get(id=bounty_order_id)
        email_to = bounty_order.to_user.email
        subject = "Bounty Fully Paid"
        email_template_path = "emails/bounty_fully_paid_no_engagement_email.html"
        logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
        privacy_policy_url = get_full_url("privacy_policy")

        send_django_template_email(
            email_to,
            subject,
            email_template_path,
            context={
                "to_user": bounty_order.to_user,
                "bounty_order": bounty_order,
                "logo_url": logo_url,
                "privacy_policy_url": privacy_policy_url,
            },
        )
    except Exception as e:
        logger.error(f"Failed to send email to bounty creator: {e}")


@shared_task
def send_sub_paused_by_admin_email(bounty_order_id):
    try:
        bounty_order = BountyOrder.objects.get(id=bounty_order_id)
        email_to = bounty_order.from_user.email
        subject = "Subscription Paused"
        email_template_path = "emails/sub_paused_by_admin_email.html"
        logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
        privacy_policy_url = get_full_url("privacy_policy")

        send_django_template_email(
            email_to,
            subject,
            email_template_path,
            context={
                "to_user": bounty_order.to_user,
                "bounty_order": bounty_order,
                "logo_url": logo_url,
                "privacy_policy_url": privacy_policy_url,
            },
        )
    except Exception as e:
        logger.error(f"Failed to send email to bounty creator: {e}")


@shared_task
def send_donation_successfully_created_email(donation_id):
    try:
        donation = Donation.objects.get(id=donation_id)
        email_to = donation.email
        subject = "Donation Created"
        email_template_path = "emails/donation_successfully_created_email.html"
        logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
        privacy_policy_url = get_full_url("privacy_policy")
        send_django_template_email(
            email_to,
            subject,
            email_template_path,
            context={"donation": donation, "logo_url": logo_url, "privacy_policy_url": privacy_policy_url},
        )
    except Exception as e:
        logger.error(f"Failed to send email to donation creator: {e}")


@shared_task
def send_failed_payment_email(donation_id):
    try:
        donation = Donation.objects.get(id=donation_id)
        email_to = donation.email
        subject = "Payment Failed"
        email_template_path = "emails/payment_failed_email.html"
        donation_link = get_full_url("partner_with_us", query_params={"donation_id": donation_id})
        update_payment_url = (
            get_full_url("customer_billing", query_params={"customer_portal": True}) if donation.from_user else None
        )
        logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
        privacy_policy_url = get_full_url("privacy_policy")

        send_django_template_email(
            email_to,
            subject,
            email_template_path,
            context={
                "donation": donation,
                "donation_link": donation_link,
                "update_payment_url": update_payment_url,
                "logo_url": logo_url,
                "privacy_policy_url": privacy_policy_url,
            },
        )
    except Exception as e:
        logger.error(f"Failed to send email to donation creator: {e}")


@shared_task
def send_donation_subscription_cancelled_email(donation_id):
    try:
        donation = Donation.objects.get(id=donation_id)
        email_to = donation.email
        subject = "Donation Subscription Canceled"
        email_template_path = "emails/donation_subscription_cancelled_email.html"
        donation_link = get_full_url("partner_with_us", query_params={"donation_id": donation_id})

        logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
        privacy_policy_url = get_full_url("privacy_policy")

        send_django_template_email(
            email_to,
            subject,
            email_template_path,
            context={
                "donation": donation,
                "donation_link": donation_link,
                "logo_url": logo_url,
                "privacy_policy_url": privacy_policy_url,
            },
        )
    except Exception as e:
        logger.error(f"Failed to send email to donation creator: {e}")


@shared_task
def send_shadchan_application_accepted_email(user_id):
    try:
        user = User.objects.get(id=user_id)
        email_to = user.email
        subject = "Shadchan Application Accepted"
        email_template_path = "emails/shadchan_application_accepted_email.html"
        logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
        privacy_policy_url = get_full_url("privacy_policy")

        send_django_template_email(
            email_to,
            subject,
            email_template_path,
            context={
                "full_name": user.get_full_name(),
                "logo_url": logo_url,
                "privacy_policy_url": privacy_policy_url,
            },
        )
    except Exception as e:
        logger.error(f"Failed to send email notifying shadchan of profile acceptance creator: {e}")


@shared_task
def send_shadchan_application_rejected_email(user_id):
    try:
        user = User.objects.get(id=user_id)
        email_to = user.email
        subject = "Shadchan Application Status Update"
        email_template_path = "emails/shadchan_application_rejected_email.html"
        logo_url = "https://shidduchme.com/static/images/ShidduchMeLogo.png"
        privacy_policy_url = get_full_url("privacy_policy")

        send_django_template_email(
            email_to,
            subject,
            email_template_path,
            context={
                "full_name": user.get_full_name(),
                "logo_url": logo_url,
                "privacy_policy_url": privacy_policy_url,
            },
        )
    except Exception as e:
        logger.error(f"Failed to send email notifying user of shadchan application rejection: {e}")
