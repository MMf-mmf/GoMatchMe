from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from .tasks import send_signup_sms_task, send_contact_form_sms_task
from .models import Contact
import logging

logger = logging.getLogger("project")


@receiver(user_signed_up)
def handle_user_signed_up(request, user, **kwargs):
    try:
        # Call the Celery task asynchronously
        send_signup_sms_task.delay(user.id)
    except Exception as e:
        # log the error if there is an error
        logger.exception(f"Error queuing SMS task when user signed up, User ID:{user.id}, Full exception: {e}")


@receiver(post_save, sender=Contact)
def handle_contact_created(sender, instance, created, **kwargs):
    """
    Signal handler to send an SMS notification when a new Contact is created.
    """
    if created:  # Only send SMS for newly created contacts
        try:
            # Call the Celery task asynchronously
            send_contact_form_sms_task.delay(instance.id)
        except Exception as e:
            logger.exception(f"Error queuing SMS task for contact form, Contact ID:{instance.id}, Full exception: {e}")
