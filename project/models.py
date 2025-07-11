from django.db import models
from utils.abstract_models import TimeStampedModel


class Contact(TimeStampedModel):
    SUBJECT_GENERAL = "General"
    SUBJECT_TECHNICAL = "Technical"
    SUBJECT_BILLING = "Billing"
    SUBJECT_OTHER = "Other"

    SUBJECT_CHOICES = [
        (SUBJECT_GENERAL, ("General")),
        (SUBJECT_TECHNICAL, ("Technical")),
        (SUBJECT_BILLING, ("Billing")),
        (SUBJECT_OTHER, ("Other")),
    ]
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()
    message = models.TextField(max_length=1_000)
    user = models.ForeignKey("accounts_app.CustomUser", on_delete=models.SET_NULL, null=True, blank=True)
    screenshot = models.ImageField(upload_to="screenshots/", blank=True, null=True)
    status = models.PositiveIntegerField(default=0, choices=((0, "New"), (1, "In Progress"), (2, "Resolved")))
    subject = models.CharField(max_length=255, choices=SUBJECT_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.message[:20]}"
