from celery import shared_task
from django.conf import settings
from twilio.rest import Client
from django.contrib.auth import get_user_model
from accounts_app.models import Contact
import logging

logger = logging.getLogger("project")


@shared_task
def send_signup_sms_task(user_id):
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)

        # Twilio credentials
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        twilio_phone_number = settings.TWILIO_PHONE_NUMBER
        your_phone_number = settings.DEV_PHONE_NUMBER

        client = Client(account_sid, auth_token)

        client.messages.create(
            body=f"New user signed up, Email: {user.email}, First Name: {user.first_name}, Last Name: {user.last_name}, Account Type: {user.get_account_type_display()}",
            from_=twilio_phone_number,
            to=your_phone_number,
        )
    except Exception as e:
        # log the error if there is an error
        logger.exception(f"Error sending SMS When user signed up, User ID:{user_id}, Full exception: {e}")


@shared_task
def send_contact_form_sms_task(contact_id):
    try:
        contact = Contact.objects.get(id=contact_id)

        # Twilio credentials
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        twilio_phone_number = settings.TWILIO_PHONE_NUMBER
        your_phone_number = settings.DEV_PHONE_NUMBER

        client = Client(account_sid, auth_token)

        # Prepare message - keep it brief to fit SMS limits
        message = (
            f"New contact form submission:\n"
            f"From: {contact.first_name} {contact.last_name}\n"
            f"Email: {contact.email}\n"
            f"Subject: {contact.subject or 'Not specified'}\n"
            f"Status: {contact.get_status_display()}"
        )

        client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=your_phone_number,
        )
    except Exception as e:
        logger.exception(f"Error sending SMS for contact form, Contact ID:{contact_id}, Full exception: {e}")
